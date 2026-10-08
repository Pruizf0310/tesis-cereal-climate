"""Server-side native-cell run counting, resumable small batches, no daily downloads."""
import argparse
import concurrent.futures as futures
import csv
import hashlib
import json
import math
import shutil
import time
from datetime import date, timedelta
from pathlib import Path

import pipeline as core
from maize_seis_fases import load_rules, windows, STAGES


def count_arrays(ee, hits, valid, min_days, count_unit):
    """Count each qualifying run at its Nth day; missing days are false hits."""
    n=hits.arrayLength(0)
    zero=ee.Image.constant(ee.Array([0]))
    if count_unit=='days':
        flags=hits
    else:
        flags=hits
        for lag in range(1,min_days):
            prev=ee.Image.constant(ee.Array([0]*lag)).arrayCat(hits,0).arraySlice(0,0,n)
            flags=flags.And(prev)
        before=ee.Image.constant(ee.Array([0]*min_days)).arrayCat(hits,0).arraySlice(0,0,n)
        flags=flags.And(before.Not())
    scalar=lambda a:a.arrayReduce(ee.Reducer.sum(),[0]).arrayGet([0])
    return scalar(flags).rename('count'),scalar(valid).rename('valid_days')


def phase_feature(ee,pixel,rule,window):
    start=window['start']; end=(date.fromisoformat(window['end'])+timedelta(days=1)).isoformat()
    total=(date.fromisoformat(end)-date.fromisoformat(start)).days
    rain=rule['variable']=='precip_mm'
    band='total_precipitation_sum' if rain else 'temperature_2m_max'
    source=ee.ImageCollection(core.DATASET).filterDate(start,end).select(band).sort('system:time_start')
    projection=ee.ImageCollection(core.DATASET).first().select('temperature_2m_max').projection()
    # Build every expected date, including entirely absent images, to preserve gaps.
    def day_image(offset):
        day=ee.Date(start).advance(offset,'day')
        daily=source.filterDate(day,day.advance(1,'day'))
        empty=ee.Image.constant(0).rename(band).updateMask(ee.Image.constant(0)).setDefaultProjection(projection)
        image=ee.Image(ee.Algorithms.If(daily.size(),daily.first(),empty))
        valid=image.mask().unmask(0).gt(0).rename('valid')
        value=image.multiply(1000) if rain else image.subtract(273.15)
        hit=value.gt(rule['threshold']) if rule['operator']=='>' else value.gte(rule['threshold'])
        return hit.unmask(0).And(valid).rename('hit').addBands(valid).toByte().set('system:time_start',day.millis())
    array=ee.ImageCollection.fromImages(ee.List.sequence(0,total-1).map(day_image)).toArray()
    hits=array.arraySlice(1,0,1).arrayProject([0])
    valid=array.arraySlice(1,1,2).arrayProject([0])
    count,days=count_arrays(ee,hits,valid,rule['min_days'],rule['count_unit'])
    complete=days.eq(total)
    # Threshold and runs are evaluated on each native ERA cell BEFORE reduction.
    weight=ee.Image.pixelLonLat().select('latitude').multiply(math.pi/180).cos()
    measures=count.multiply(weight).multiply(complete).rename('weighted_count')
    measures=measures.addBands(count.gt(0).multiply(weight).multiply(complete).rename('weighted_exposed'))
    measures=measures.addBands(weight.multiply(complete).rename('weight'))
    measures=measures.addBands(complete.rename('complete_cells'))
    measures=measures.addBands(ee.Image.constant(1).rename('native_cells'))
    measures=measures.addBands(days.rename('valid_cell_days'))
    measures=measures.addBands(ee.Image.constant(total).rename('expected_cell_days'))
    lon,lat=pixel['lon'],pixel['lat']
    region=ee.Geometry.Rectangle([lon-.25,lat-.25,lon+.25,lat+.25],geodesic=False)
    stats=measures.reduceRegion(reducer=ee.Reducer.sum().unweighted(),geometry=region,
                               crs=projection,maxPixels=1000,tileScale=2)
    return ee.Feature(None,stats).set(dict(pixel_id=pixel['pixel_id'],season_year=window['season_year'],
        phase=rule['phase'],start=start,end=window['end'],threshold=rule['threshold'],
        variable=rule['variable'],operator=rule['operator'],min_days=rule['min_days'],
        count_unit=rule['count_unit'],source=rule['source']))


def compute_batch(ee,items,rules,data,folder,fingerprint):
    key=hashlib.sha256(json.dumps(items,sort_keys=True).encode()).hexdigest()[:20]
    path=folder/f'batch_{key}.csv'; marker=path.with_suffix('.json')
    if path.exists() and marker.exists():
        meta=json.loads(marker.read_text())
        if meta['fingerprint']!=fingerprint or meta['sha256']!=hashlib.sha256(path.read_bytes()).hexdigest():
            raise ValueError(f'Lote incompatible o alterado: {path}')
        return path,True
    features=[]
    for pixel,year in items:
        for rule in rules:
            w=windows(data,pixel,rule['phase'],year,year)[0]
            features.append(phase_feature(ee,pixel,rule,w))
    rows=core.fetch_pages(ee,ee.FeatureCollection(features))
    expected={(p['pixel_id'],y,r['phase']) for p,y in items for r in rules}
    keys={(int(r['pixel_id']),int(r['season_year']),r['phase']) for r in rows}
    if len(rows)!=len(expected) or keys!=expected:
        raise ValueError('GEE devolvió filas incompletas o duplicadas; no se guarda el lote')
    for row in rows:
        w=float(row.get('weight') or 0)
        cells=int(row.get('native_cells') or 0)
        complete=int(row.get('complete_cells') or 0)
        row['quality']='OK' if cells>0 and complete==cells else 'INCOMPLETE'
        row['mean_count_per_native_cell']=float(row['weighted_count'])/w if w else None
        row['evaluated_area_fraction_with_event']=float(row['weighted_exposed'])/w if w else None
        row['coverage_fraction']=complete/cells if cells else 0
    temporary=path.with_suffix('.tmp')
    core.save_csv(temporary,rows,fields=sorted(rows[0]))
    temporary.replace(path)
    marker.write_text(json.dumps(dict(fingerprint=fingerprint,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                                     rows=len(rows))),encoding='utf-8')
    return path,False


def consolidate(paths,root):
    import pandas as pd
    temporary=root/'resumen_GDHY_anual.csv.tmp'
    history={}; yearly={}; header=None
    with temporary.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.writer(stream)
        for path in paths:
            with path.open(encoding='utf-8-sig',newline='') as source:
                reader=csv.DictReader(source)
                if header is None:header=reader.fieldnames;writer.writerow(header)
                for row in reader:
                    writer.writerow([row[k] for k in header])
                    if row['quality']!='OK':continue
                    key=(row['pixel_id'],row['phase'],row['count_unit'])
                    h=history.setdefault(key,[0,0.0,0.0])
                    h[0]+=1;h[1]+=float(row['mean_count_per_native_cell']);h[2]+=float(row['evaluated_area_fraction_with_event'])
                    key2=(int(row['season_year']),row['phase'],row['count_unit'])
                    y=yearly.setdefault(key2,[0,0.0]);y[0]+=1;y[1]+=float(row['mean_count_per_native_cell'])
    temporary.replace(root/'resumen_GDHY_anual.csv')
    core.save_csv(root/'frecuencia_historica_GDHY.csv',[
        dict(pixel_id=k[0],phase=k[1],count_unit=k[2],complete_seasons=v[0],
             mean_annual_count_per_native_cell=v[1]/v[0],mean_annual_area_fraction_with_event=v[2]/v[0])
        for k,v in sorted(history.items())])
    annual=[dict(year=k[0],phase=k[1],count_unit=k[2],pixels=v[0],mean_count=v[1]/v[0]) for k,v in sorted(yearly.items())]
    core.save_csv(root/'frecuencia_anual_conjunto.csv',annual)
    if annual:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        frame=pd.DataFrame(annual)
        fig,axes=plt.subplots(3,2,figsize=(12,10))
        for ax,phase in zip(axes.flat,STAGES):
            sub=frame[frame.phase==phase].sort_values('year')
            ax.plot(sub.year,sub.mean_count)
            ax.set(title=phase,xlabel='Año de siembra',ylabel='Días medios/celda' if phase=='MAT' else 'Eventos medios/celda')
        fig.tight_layout();fig.savefig(root/'frecuencia_seis_fases.png',dpi=160);plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default=str(Path(__file__).with_name('config_maize_seis_fases_gee.json')))
    parser.add_argument('--limit',type=int,default=0)
    parser.add_argument('--start-year',type=int)
    parser.add_argument('--end-year',type=int)
    parser.add_argument('--workers',type=int,default=2)
    parser.add_argument('--batch-size',type=int,default=4,help='Píxel-años por solicitud; seis fases por píxel-año')
    args=parser.parse_args()
    if args.limit<0 or not 1<=args.workers<=4 or not 1<=args.batch_size<=16:parser.error('Límites: workers 1–4, batch-size 1–16, limit >=0')
    c=json.loads(Path(args.config).read_text(encoding='utf-8'))
    first=args.start_year or c['start_year'];last=args.end_year or c['end_year']
    if not c['start_year']<=first<=last<=c['end_year']:parser.error('Años fuera del periodo configurado')
    import h5py
    with h5py.File(c['h5']) as f:ii,jj=f['lat_idx'][...],f['lon_idx'][...]
    with h5py.File(c['yield_nc']) as f:lat,lon=f['lat'][...],f['lon'][...]
    pixels=[dict(pixel_id=int(i)*len(lon)+int(j),lat=float(lat[i]),lon=float((lon[j]+180)%360-180)) for i,j in zip(ii,jj)]
    if args.limit:pixels=pixels[:args.limit]
    rules=load_rules(Path(c['rules_csv']))
    calendar=Path(c['calendar_dir'])/'maize-maize__rf.json';data=json.loads(calendar.read_text(encoding='utf-8'))
    scientific=dict(config=c,rules=rules,stages=STAGES,calendar_sha256=hashlib.sha256(calendar.read_bytes()).hexdigest(),
                    algorithm='native_arrays_run_Nth_day_v1',code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    fingerprint=hashlib.sha256(json.dumps(scientific,sort_keys=True).encode()).hexdigest()
    root=Path(c['output']);root.mkdir(parents=True,exist_ok=True)
    folder=root/'lotes';folder.mkdir(exist_ok=True)
    plan=scientific|dict(selected_pixels=len(pixels),first_year=first,last_year=last,workers=args.workers,batch_size=args.batch_size,
        limitations='UTC days; estimated phase dates; same operational source proxies as legacy runner. Count each native cell before spatial mean; incomplete cells excluded. MAT counts individual days. No unique weather-system count or yield association. Daily series and event dates are not exported by this summary engine.')
    (root/'plan_ejecucion.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    import ee
    core.authenticate_gee();core.initialize(c)
    items=[(p,y) for p in pixels for y in range(first,last+1)]
    batches=[items[i:i+args.batch_size] for i in range(0,len(items),args.batch_size)]
    print(f'GEE: {len(pixels)} píxeles × {last-first+1} años × 6 fases; {len(batches)} lotes. No se descargan series diarias.',flush=True)
    started=time.monotonic();done=0;new=0;paths=[]
    iterator=iter(batches); pool=futures.ThreadPoolExecutor(max_workers=args.workers)
    pending={pool.submit(compute_batch,ee,b,rules,data,folder,fingerprint) for b in [next(iterator,None) for _ in range(args.workers)] if b is not None}
    status='RUNNING'
    try:
        while pending:
            ready,pending=futures.wait(pending,timeout=15,return_when=futures.FIRST_COMPLETED)
            if not ready:
                print(f'GEE calculando: {done}/{len(batches)} lotes; transcurridos {(time.monotonic()-started)/60:.1f} min.',flush=True)
                continue
            for job in ready:
                path,cached=job.result();paths.append(path);done+=1;new+=not cached
                elapsed=time.monotonic()-started
                eta=elapsed/new*(len(batches)-done)/args.workers if new else None
                # Throughput already includes parallel execution; do not divide ETA twice.
                eta=elapsed/new*(len(batches)-done) if new else None
                progress=dict(status='RUNNING',completed_batches=done,total_batches=len(batches),new_batches=new,
                              elapsed_seconds=elapsed,estimated_remaining_seconds=eta)
                (root/'progreso_paquete.json').write_text(json.dumps(progress,indent=2),encoding='utf-8')
                print(f'Lotes {done}/{len(batches)} | {"caché" if cached else "calculado"} | '
                      f'transcurrido {elapsed/60:.1f} min | restante aprox. {eta/3600:.2f} h' if eta is not None else
                      f'Lotes {done}/{len(batches)} | caché',flush=True)
                batch=next(iterator,None)
                if batch is not None:pending.add(pool.submit(compute_batch,ee,batch,rules,data,folder,fingerprint))
        status='COMPLETED'
    except KeyboardInterrupt:
        status='INTERRUPTED';print('Interrumpido. Los lotes completos se conservan; solicitudes en curso pueden tardar en cerrar.',flush=True)
    except Exception as exc:
        status='FAILED';print(f'Lote fallido: {exc}. Repite el comando para retomar.',flush=True)
        raise
    finally:
        for job in pending:job.cancel()
        pool.shutdown(wait=True,cancel_futures=True)
        (root/'estado_paquete.json').write_text(json.dumps(dict(status=status,completed_batches=done,total_batches=len(batches))),encoding='utf-8')
    if status=='COMPLETED':
        consolidate(sorted(paths),root)
        if c.get('repository_results'):
            dest=Path(c['repository_results']);dest.mkdir(parents=True,exist_ok=True)
            for file in root.iterdir():
                if file.is_file():shutil.copy2(file,dest/file.name)
        print('Cálculo y gráficos terminados:',root,flush=True)


if __name__=='__main__':main()
