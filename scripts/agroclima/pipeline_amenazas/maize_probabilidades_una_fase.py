"""All maize pixels, 1981–2016: one phase, daily ONI/MJO conditional probabilities."""
import argparse
import concurrent.futures as futures
import gzip
import hashlib
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
from fechas_ocurrencias_core import native_features,qualifying_runs
from maize_seis_fases import windows
from maize_mjo_diario import initialize_gee
from probabilidades_oni_mjo import affected_fraction,summarize,STATES
from correlacion_oni_amenazas import read_oni
import pipeline as core

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def atomic_json(path,value):
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8');temp.replace(path)

def save_native(path,rows):
    temp=path.with_suffix('.tmp')
    with gzip.open(temp,'wt',encoding='utf-8') as f:json.dump(rows,f)
    temp.replace(path)
    atomic_json(path.with_suffix('.sha.json'),{'sha256':sha(path)})

def load_native(path):
    if sha(path)!=json.loads(path.with_suffix('.sha.json').read_text())['sha256']:
        raise ValueError(f'Caché alterada: {path}')
    with gzip.open(path,'rt',encoding='utf-8') as f:return json.load(f)

def daily_frame(rows,rule,pixel,year,calendar):
    w=windows(calendar,pixel,rule['phase'],year,year)[0]
    dates=pd.date_range(w['start'],w['end']);required=1 if rule['count_unit']=='days' else int(rule['min_days'])
    if not rows:raise ValueError('GEE no devolvió celdas')
    if len({(c['x'],c['y']) for c in rows})!=len(rows):raise ValueError('Celdas duplicadas')
    if any(len(np.asarray(c['hits']).ravel())!=len(dates) or len(np.asarray(c['valid']).ravel())!=len(dates) for c in rows):raise ValueError('Serie truncada')
    affected=affected_fraction(rows,required)
    weights=np.cos(np.deg2rad([float(c['latitude']) for c in rows]));flags=[]
    for c in rows:
        flag=np.zeros(len(dates))
        for a,q,b in qualifying_runs(np.asarray(c['hits']).ravel(),np.asarray(c['valid']).ravel(),required):
            if rule['count_unit']=='days':flag[a:b+1]=1
            else:flag[q]=1
        flags.append(flag)
    count=weights@np.asarray(flags)/weights.sum();count[~np.isfinite(affected)]=np.nan
    return pd.DataFrame(dict(pixel_id=pixel['pixel_id'],season_year=year,phase=rule['phase'],date=dates,
        affected=affected,mean_occurrences_qualified=count))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=Path('C:/Users/paola/Tesis'))
    ap.add_argument('--phase',choices=['EST','VEG','REP','FLO','FIL','MAT'],default='EST')
    ap.add_argument('--workers',type=int,default=4)
    ap.add_argument('--years-per-request',type=int,default=36)
    ap.add_argument('--min-days',type=int,default=30)
    ap.add_argument('--min-years',type=int,default=3)
    ap.add_argument('--cache-only',action='store_true')
    args=ap.parse_args()
    if not 1<=args.workers<=8 or not 1<=args.years_per_request<=36 or args.min_days<1 or args.min_years<1:ap.error('Revisar workers (1–8), años por solicitud (1–36) y mínimos positivos')
    root=args.root;base=root/'03_Resultados/Agroclima/vigente'
    plan_path=base/'ejecuciones/maize_seis_fases_GEE_1981_2016/plan_ejecucion.json'
    plan=json.loads(plan_path.read_text(encoding='utf-8'));rule=next(r for r in plan['rules'] if r['phase']==args.phase)
    calendar_path=Path(plan['config']['calendar_dir'])/'maize-maize__rf.json'
    if sha(calendar_path)!=plan['calendar_sha256']:raise ValueError('Calendario distinto al original')
    calendar=json.loads(calendar_path.read_text(encoding='utf-8'))
    coords_path=root/'02_Procesados/Pixeles_correlacion_vigentes/pixeles_maize.csv'
    coords=pd.read_csv(coords_path).sort_values('h5_index')
    if coords.pixel_id.duplicated().any():raise ValueError('Píxeles duplicados')
    rmm_path=root/'01_Data/RMM/rmm_official.txt';oni_path=root/'01_Data/ONI/ONI_v6_2026-10-08.html'
    rmm=pd.read_csv(rmm_path,sep=r'\s+',skiprows=2,header=None,usecols=range(7),names=['year','month','day','rmm1','rmm2','mjo_phase','amplitude'])
    rmm['date']=pd.to_datetime(rmm[['year','month','day']])
    if rmm.date.duplicated().any():raise ValueError('RMM duplicado')
    bad=(rmm[['rmm1','rmm2']].abs()>=100).any(axis=1)|(~rmm.mjo_phase.between(1,8))|(~rmm.amplitude.between(0,100))
    rmm.loc[bad,['mjo_phase','amplitude']]=np.nan
    rmm=rmm.set_index('date')[['mjo_phase','amplitude']]
    oni,*_=read_oni(oni_path);oni=pd.Series(oni.to_numpy(),index=pd.to_datetime(oni.index).to_period('M'))
    identity=dict(version='one_phase_v1',rule=rule,calendar=sha(calendar_path),pixels=sha(coords_path),rmm=sha(rmm_path),oni=sha(oni_path),
        code=sha(Path(__file__)),helper=sha(Path(__file__).with_name('probabilidades_oni_mjo.py')),min_days=args.min_days,min_years=args.min_years)
    fp=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()[:16]
    out=base/'probabilidades'/f'maize_{args.phase}_global_1981_2016'/fp
    checkpoints=out/'por_pixel';checkpoints.mkdir(parents=True,exist_ok=True)
    # Native climate cache independent of statistical settings and index versions.
    cfp=hashlib.sha256((sha(calendar_path)+json.dumps(rule,sort_keys=True)+'native_one_phase_v1').encode()).hexdigest()[:16]
    cache=root/'02_Procesados/Clima_ERA5_Land_cache/ONI_MJO_una_fase'/cfp;cache.mkdir(parents=True,exist_ok=True)
    atomic_json(out/'plan.json',dict(identity=identity,phase=args.phase,years=[1981,2016],pixels=len(coords),cache=str(cache),project=plan['config']['project']))
    # Discover verified previous daily runs and reuse their native arrays, including the 10-pixel pilot.
    previous=[]
    for p in (base/'correlaciones/maize_MJO_diario').glob('*/provenance.json'):
        m=json.loads(p.read_text(encoding='utf-8'))
        if m.get('plan_sha256')==sha(plan_path) and m.get('annual_count_verification',{}).get('mismatches')==0:previous.append(Path(m['climate_cache']))
    ee=None if args.cache_only else initialize_gee(plan['config'])
    def get_rows(pixel,years):
        result={};missing=[]
        path=cache/f'{pixel["pixel_id"]}.json.gz'
        saved=load_native(path) if path.exists() else {}
        for year in years:
            if str(year) in saved:result[year]=saved[str(year)];continue
            for old in previous:
                source=old/f'{pixel["pixel_id"]}_{year}.native.json.gz';marker=old/f'{pixel["pixel_id"]}_{year}.json'
                if not source.exists() or not marker.exists():continue
                if sha(source)!=json.loads(marker.read_text())['hashes']['native']:raise ValueError('Caché previa alterada')
                with gzip.open(source,'rt',encoding='utf-8') as f:rows=[c for c in json.load(f) if c['phase']==args.phase]
                if rows:saved[str(year)]=rows;result[year]=rows;break
            if year not in result:missing.append(year)
        if result:save_native(path,saved)
        if missing:
            if args.cache_only:raise RuntimeError(f'Faltan fechas: píxel {pixel["pixel_id"]}, años {missing}. Repite sin --cache-only.')
            expression=ee.FeatureCollection([])
            for year in missing:expression=expression.merge(native_features(ee,pixel,rule,windows(calendar,pixel,args.phase,year,year)[0]))
            try:rows=core.fetch_pages(ee,expression)
            except Exception as error:
                # Split only resource/size failures, never auth or exhausted-quota failures.
                resource_failure=any(s in str(error).lower() for s in ['memory limit','computed value is too large','request payload size','computation timed out','response too large'])
                if len(missing)==1 or not resource_failure:raise
                mid=len(missing)//2
                result.update(get_rows(pixel,missing[:mid]));result.update(get_rows(pixel,missing[mid:]));return result
            for year in missing:
                selected=[c for c in rows if int(c['season_year'])==year and c['phase']==args.phase]
                daily_frame(selected,rule,pixel,year,calendar) # validate before checkpoint
                saved[str(year)]=selected;result[year]=selected
            save_native(path,saved)
        return result
    def process(pixel):
        pid=pixel['pixel_id'];path=checkpoints/f'{pid}.json'
        if path.exists():return json.loads(path.read_text()),True
        frames=[]
        for start in range(1981,2017,args.years_per_request):
            years=list(range(start,min(2017,start+args.years_per_request)))
            rows=get_rows(pixel,years)
            frames.extend(daily_frame(rows[y],rule,pixel,y,calendar) for y in years)
        d=pd.concat(frames,ignore_index=True)
        d=d.join(rmm,on='date',validate='many_to_one');d['oni']=d.date.dt.to_period('M').map(oni)
        d['month']=d.date.dt.month
        d['oni_state']=np.select([d.oni<=-.5,d.oni>=.5],['Cool','Warm'],default='Neutral')
        d['mjo_state']=d.mjo_phase.astype('Int64').astype(str);d.loc[d.amplitude<=1,'mjo_state']='Weak'
        climate=d[d.affected.notna()].copy()
        annual=climate.groupby(['pixel_id','season_year','phase']).agg(valid_days=('affected','size'),affected_days_equivalent=('affected','sum'),episodes_mean_native_cell=('mean_occurrences_qualified','sum')).reset_index()
        # ONI-only uses all available climate/ONI dates; joint uses overlap with valid RMM.
        oni_days=climate[climate.oni.notna()];joint_days=oni_days[oni_days.amplitude.notna()]
        a=summarize(oni_days,['oni_state'],args.min_days,args.min_years)
        b=summarize(joint_days,['oni_state','mjo_state'],args.min_days,args.min_years)
        # Month AND ONI matched reference for MJO's descriptive incremental association.
        if len(b):
            ref=joint_days.groupby(['month','oni_state']).affected.mean()
            for i,row in b.iterrows():
                s=joint_days[(joint_days.oni_state==row.oni_state)&(joint_days.mjo_state==row.mjo_state)]
                baseline=float(np.mean([ref.loc[(m,row.oni_state)] for m in s.month]))
                b.loc[i,'month_ONI_matched_reference']=baseline
                b.loc[i,'MJO_difference_pp']=100*(row.probability-baseline)
        for frame in [a,b,annual]:
            frame['latitude']=pixel['lat'];frame['longitude']=pixel['lon']
        record=dict(pixel_id=pid,oni=a.to_dict('records'),joint=b.to_dict('records'),annual=annual.to_dict('records'),
            valid_climate_days=len(climate),valid_joint_days=len(joint_days),complete_seasons=int(annual.season_year.nunique()) if len(annual) else 0)
        atomic_json(path,record);return record,False
    pixels=[dict(pixel_id=int(r.pixel_id),lat=float(r.latitude),lon=float(r.longitude)) for r in coords.itertuples()]
    print(f'{args.phase}: TODOS los {len(pixels):,} píxeles × 36 temporadas; años 1981–2016.',flush=True)
    print(f'Regla: {rule["variable"]} {rule["operator"]} {rule["threshold"]}; duración mínima {rule["min_days"]} días.',flush=True)
    print(f'Lotes iniciales: hasta {args.years_per_request} años por píxel; se dividen si GEE rechaza su tamaño. Workers={args.workers}.',flush=True)
    print('SÍ consume cómputo GEE donde faltan fechas. Cuota restringida puede ralentizarlo. Aún no hay una duración fiable.',flush=True)
    print(f'Reanudable con el mismo comando. Resultados: {out}',flush=True)
    started=time.perf_counter();done=0;new=0;records=[];jobs=iter(pixels)
    with futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        pending={}
        def fill():
            while len(pending)<args.workers:
                p=next(jobs,None)
                if p is None:break
                pending[pool.submit(process,p)]=p['pixel_id']
        fill()
        while pending:
            ready,_=futures.wait(pending,return_when=futures.FIRST_COMPLETED)
            for future in ready:
                pid=pending.pop(future)
                try:record,cached=future.result()
                except Exception as e:
                    atomic_json(out/'error.json',dict(pixel_id=pid,error=str(e)))
                    raise RuntimeError(f'Error en píxel {pid}. Checkpoints preservados; repite el mismo comando. {e}') from e
                records.append(record);done+=1;new+=not cached;elapsed=time.perf_counter()-started
                eta=f'{elapsed/max(new,1)*(len(pixels)-done)/3600:.2f} h (preliminar)' if new>=4 else 'estimando con píxeles nuevos'
                print(f'Píxeles {done:,}/{len(pixels):,} | {"caché" if cached else "procesado"} | {elapsed/60:.1f} min | restante ≈{eta}',flush=True)
            fill()
    for key,name in [('oni','probabilities_ONI.csv'),('joint','probabilities_ONI_MJO.csv'),('annual','annual_exposure_for_yield_alignment.csv')]:
        pd.DataFrame([row for r in records for row in r[key]]).to_csv(out/name,index=False)
    pd.DataFrame([{k:v for k,v in r.items() if k not in ['oni','joint','annual']} for r in records]).to_csv(out/'coverage.csv',index=False)
    make_maps(pd.read_csv(out/'probabilities_ONI.csv'),root,out,args.phase,rule)
    atomic_json(out/'completed.json',dict(pixels=done,elapsed_seconds=time.perf_counter()-started,years=[1981,2016],
        interpretation='Historical descriptive probabilities, not forecast skill, causal effects or yield loss. No uncertainty estimates.',
        probability='Area-weighted fraction of native cells in qualifying episodes, averaged across valid phase days. All run days included.',
        limitations=['ONI bins ≤−0.5, between −0.5 and 0.5, ≥0.5 are centered monthly index bins, not official ENSO episode classifications.',
        'Joint table provides month-and-ONI matched reference; no claim of incremental out-of-sample predictive information.',
        'Daily and spatial dependence; minimum days/years are display safeguards only.',
        'Season labels follow planting calendar; harvest-year alignment required before yield correlation.',
        'Phase-clipped runs, frozen rules and regional calendar approximations retained. FIL threshold 32.7 requires source review.',
        'RMM method changes in 2014 require sensitivity assessment. Detrended yield is not exclusively climate.']))
    repo=root/'Repositorio/tesis-cereal-climate/outputs/agroclima_vigente/probabilidades'/out.parent.name/out.name
    repo.mkdir(parents=True,exist_ok=True)
    import shutil
    for file in out.iterdir():
        if file.is_file() and file.name!='error.json':shutil.copy2(file,repo/file.name)
    print(f'TERMINADO: {out}',flush=True)

def make_maps(table,root,out,phase,rule):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    from resumen_amenazas_maize import boundaries
    lines=boundaries(root/'Repositorio/tesis-cereal-climate/web-v2/public/data/world_outline.geojson')
    fig,axes=plt.subplots(3,1,figsize=(14,15),layout='constrained')
    cmap=plt.get_cmap('YlOrRd').copy();cmap.set_bad((1,1,1,0))
    coords=pd.read_csv(root/'02_Procesados/Pixeles_correlacion_vigentes/pixeles_maize.csv')[['pixel_id','latitude','longitude']]
    for ax,state in zip(axes,STATES):
        s=coords.merge(table.loc[table.oni_state==state,['pixel_id','eligible','probability']],on='pixel_id',how='left',validate='one_to_one');grid=np.full((360,720),np.nan)
        r=np.rint((s.latitude.to_numpy()+89.75)/.5).astype(int);c=np.rint((s.longitude.to_numpy()+179.75)/.5).astype(int)
        grid[r,c]=np.where(s.eligible.eq(True),100*s.probability,np.nan)
        # Mask non-cultivated cells separately from insufficient estimates.
        crop=np.zeros((360,720),bool);crop[r,c]=True
        image=np.ma.array(grid,mask=~crop)
        ax.set_facecolor('white')
        mesh=ax.pcolormesh(np.arange(-180,180.5,.5),np.arange(-90,90.5,.5),image,cmap=cmap,vmin=0,vmax=100,rasterized=True)
        # Gray cultivated pixels with insufficient data.
        insufficient=crop&~np.isfinite(grid)
        rr,cc=np.where(insufficient)
        ax.scatter(-179.75+.5*cc,-89.75+.5*rr,s=1,color='#bdbdbd',marker='s')
        if lines:ax.add_collection(LineCollection(lines,colors='#777777',linewidths=.35))
        ax.set(xlim=(-180,180),ylim=(-58,82),title=f'ONI {state.lower()}');ax.set_aspect('equal');ax.set_xticks([]);ax.set_yticks([])
    fig.suptitle(f'MAIZE | {phase} | Probability of climate-threshold exposure, 1981–2016\n{rule["variable"]} {rule["operator"]} {rule["threshold"]}; minimum duration {rule["min_days"]} days',fontsize=14)
    fig.colorbar(mesh,ax=axes,shrink=.6,label='Historical daily exposure probability (%)')
    fig.supxlabel('Monthly centered ONI bins: cool ≤−0.5°C; warm ≥0.5°C; neutral in between.\nGray: insufficient exposure. Descriptive estimates; no forecast or significance claim.',fontsize=10)
    for ext in ['png','pdf']:fig.savefig(out/f'global_ONI_probabilities.{ext}',dpi=200,facecolor='white')
    plt.close(fig)

if __name__=='__main__':main()
