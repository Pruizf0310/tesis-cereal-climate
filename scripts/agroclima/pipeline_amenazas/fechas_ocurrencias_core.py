"""Export daily occurrence dates and native-cell episodes with original phase rules."""
import gzip
import hashlib
import json
import math
import time
from datetime import date,timedelta
import numpy as np
import pandas as pd
import pipeline as core
from maize_seis_fases import windows

EVENT_COLUMNS=['event_id','pixel_id','season_year','phase','native_x','native_y','longitude','latitude',
    'phase_start','phase_end','event_start_within_phase','qualification_date','event_end_within_phase',
    'observed_duration_days','touches_phase_start','touches_phase_end','variable','operator','threshold','min_days','count_unit','quality']

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def qualifying_runs(hits,valid,min_days):
    """Observed runs clipped to phase; return start, qualification, end indices."""
    hot=np.asarray(hits,dtype=bool)&np.asarray(valid,dtype=bool)
    edges=np.diff(np.r_[False,hot,False].astype(int))
    starts=np.flatnonzero(edges==1);ends=np.flatnonzero(edges==-1)-1
    return [(int(a),int(a+min_days-1),int(b)) for a,b in zip(starts,ends) if b-a+1>=min_days]

def native_features(ee,pixel,rule,window):
    start=window['start'];end=window['end'];total=(date.fromisoformat(end)-date.fromisoformat(start)).days+1
    rain=rule['variable']=='precip_mm';band='total_precipitation_sum' if rain else 'temperature_2m_max'
    projection=ee.ImageCollection(core.DATASET).first().select('temperature_2m_max').projection()
    source=ee.ImageCollection(core.DATASET).filterDate(start,(date.fromisoformat(end)+timedelta(days=1)).isoformat()).select(band)
    def daily(offset):
        day=ee.Date(start).advance(offset,'day');images=source.filterDate(day,day.advance(1,'day'))
        empty=ee.Image.constant(0).rename(band).updateMask(ee.Image.constant(0)).setDefaultProjection(projection)
        image=ee.Image(ee.Algorithms.If(images.size(),images.first(),empty))
        valid=image.mask().unmask(0).gt(0).rename('valid')
        value=image.multiply(1000) if rain else image.subtract(273.15)
        hit=value.gt(rule['threshold']) if rule['operator']=='>' else value.gte(rule['threshold'])
        return hit.unmask(0).And(valid).rename('hit').addBands(valid).toByte().set('system:time_start',day.millis())
    array=ee.ImageCollection.fromImages(ee.List.sequence(0,total-1).map(daily)).toArray()
    image=array.arraySlice(1,0,1).arrayProject([0]).rename('hits')
    image=image.addBands(array.arraySlice(1,1,2).arrayProject([0]).rename('valid'))
    image=image.addBands(ee.Image.pixelLonLat()).addBands(ee.Image.pixelCoordinates(projection))
    region=ee.Geometry.Rectangle([pixel['lon']-.25,pixel['lat']-.25,pixel['lon']+.25,pixel['lat']+.25],geodesic=False)
    sampled=image.sample(region=region,projection=projection,dropNulls=False,geometries=False)
    props=dict(pixel_id=pixel['pixel_id'],season_year=window['season_year'],phase=rule['phase'],
        phase_start=start,phase_end=end,variable=rule['variable'],operator=rule['operator'],threshold=rule['threshold'],
        min_days=int(rule['min_days']),count_unit=rule['count_unit'])
    return sampled.map(lambda f:ee.Feature(f).set(props))

def assemble(rows,rules,pixel,year,calendar):
    events=[];days=[];weekly=[]
    for rule in rules:
        phase=rule['phase'];w=windows(calendar,pixel,phase,year,year)[0]
        first=date.fromisoformat(w['start']);last=date.fromisoformat(w['end']);length=(last-first).days+1
        cells=[r for r in rows if r['phase']==phase]
        if not cells:raise ValueError(f'No native cells: {phase}')
        if len({(r['x'],r['y']) for r in cells})!=len(cells):raise ValueError('Duplicate native cells')
        all_flags=[];weights=[];complete=[];valid_counts=np.zeros(length,int)
        for cell in cells:
            hits=np.asarray(cell['hits']).ravel();valid=np.asarray(cell['valid']).ravel().astype(bool)
            if len(hits)!=length or len(valid)!=length:raise ValueError('Truncated daily arrays')
            is_complete=bool(valid.all());complete.append(is_complete);valid_counts+=valid.astype(int)
            flags=np.zeros(length);weights.append(math.cos(math.radians(float(cell['latitude']))))
            runs=qualifying_runs(hits,valid,1 if rule['count_unit']=='days' else int(rule['min_days']))
            if rule['count_unit']=='days':runs=[(j,j,j) for a,_,b in runs for j in range(a,b+1)]
            for a,q,b in runs:
                flags[q]=1
                events.append(dict(event_id=f'{pixel["pixel_id"]}_{year}_{phase}_{cell["x"]}_{cell["y"]}_{q}',
                    pixel_id=pixel['pixel_id'],season_year=year,phase=phase,native_x=cell['x'],native_y=cell['y'],
                    longitude=cell['longitude'],latitude=cell['latitude'],phase_start=w['start'],phase_end=w['end'],
                    event_start_within_phase=(first+timedelta(days=a)).isoformat(),qualification_date=(first+timedelta(days=q)).isoformat(),
                    event_end_within_phase=(first+timedelta(days=b)).isoformat(),observed_duration_days=b-a+1,
                    touches_phase_start=a==0,touches_phase_end=b==length-1,variable=rule['variable'],operator=rule['operator'],
                    threshold=rule['threshold'],min_days=rule['min_days'],count_unit=rule['count_unit'],
                    quality='OK' if is_complete else 'INCOMPLETE_NATIVE_PHASE'))
            all_flags.append(flags)
        quality='OK' if all(complete) else 'INCOMPLETE'
        weights=np.asarray(weights);flags=np.asarray(all_flags)
        counts=weights@flags/weights.sum()
        for j in range(length):
            days.append(dict(pixel_id=pixel['pixel_id'],season_year=year,phase=phase,date=(first+timedelta(days=j)).isoformat(),
                phase_start=w['start'],phase_end=w['end'],quality=quality,native_cells=len(cells),
                valid_cells_on_date=int(valid_counts[j]),complete_native_cells=sum(complete),
                mean_occurrences_qualified=counts[j] if quality=='OK' else np.nan,
                variable=rule['variable'],operator=rule['operator'],threshold=rule['threshold'],min_days=rule['min_days'],count_unit=rule['count_unit']))
        for j in range(0,length-6,7):
            weekly.append(dict(pixel_id=pixel['pixel_id'],season_year=year,phase=phase,start=(first+timedelta(days=j)).isoformat(),
                end=(first+timedelta(days=j+6)).isoformat(),quality=quality,count=counts[j:j+7].sum() if quality=='OK' else np.nan,
                native_cells=len(cells),complete_cells=sum(complete),variable=rule['variable'],operator=rule['operator'],
                threshold=rule['threshold'],min_days=rule['min_days'],count_unit=rule['count_unit']))
    return pd.DataFrame(weekly),pd.DataFrame(days),pd.DataFrame(events,columns=EVENT_COLUMNS)

def compute_dates_job(ee,pixel,year,rules,calendar,folder):
    stem=f'{pixel["pixel_id"]}_{year}'
    files={name:folder/f'{stem}.{suffix}' for name,suffix in [('weekly','csv'),('daily','daily.csv.gz'),('events','events.csv.gz'),('native','native.json.gz')]}
    marker=folder/f'{stem}.json'
    if marker.exists():
        info=json.loads(marker.read_text())
        if all(path.exists() and digest(path)==info['hashes'].get(name) for name,path in files.items()):
            return pd.read_csv(files['weekly']),True
        raise ValueError(f'Incomplete or altered dated cache: {stem}')
    features=ee.FeatureCollection([])
    for rule in rules:features=features.merge(native_features(ee,pixel,rule,windows(calendar,pixel,rule['phase'],year,year)[0]))
    for attempt in range(3):
        try:rows=core.fetch_pages(ee,features);break
        except Exception:
            if attempt==2:raise
            time.sleep(2*(attempt+1))
    weekly,daily,events=assemble(rows,rules,pixel,year,calendar)
    for name,frame in [('weekly',weekly),('daily',daily),('events',events)]:
        temp=files[name].with_suffix(files[name].suffix+'.tmp')
        frame.to_csv(temp,index=False,compression='gzip' if name!='weekly' else None);temp.replace(files[name])
    with gzip.open(files['native'],'wt',encoding='utf-8') as stream:json.dump(rows,stream)
    marker.write_text(json.dumps({'hashes':{name:digest(path) for name,path in files.items()},'daily_rows':len(daily),'native_events':len(events)}),encoding='utf-8')
    return weekly,False
