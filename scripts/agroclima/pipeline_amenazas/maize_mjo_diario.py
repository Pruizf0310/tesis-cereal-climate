"""Pearson diario MJO–ocurrencias por fase; fechas persistentes y gráficos automáticos."""
import argparse
import concurrent.futures as futures
import gzip
import hashlib
import json
import math
import time
import urllib.request
from datetime import date,timedelta
from pathlib import Path
import numpy as np
import pandas as pd
import pipeline as core
from maize_seis_fases import windows
from fechas_ocurrencias_core import compute_dates_job

PHASES=['EST','VEG','REP','FLO','FIL','MAT']
RMM_URL='https://www.bom.gov.au/climate/mjo/graphics/rmm.74toRealtime.txt'
RMM_URLS=[RMM_URL,'https://reg.bom.gov.au/climate/mjo/graphics/rmm.74toRealtime.txt']

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def initialize_gee(config):
    """Use the user's existing gcloud ADC explicitly and refresh expired tokens."""
    import ee
    import google.auth
    from google.auth.transport.requests import Request
    from google.auth.exceptions import DefaultCredentialsError,RefreshError
    try:
        credentials,_=google.auth.default(scopes=core.AUTH_SCOPES)
        if not credentials.valid:credentials.refresh(Request())
    except (DefaultCredentialsError,RefreshError) as error:
        raise RuntimeError(
            'No se pudo utilizar la autorización guardada de Google Cloud. '
            'Ejecuta: gcloud auth application-default login '
            '--scopes=https://www.googleapis.com/auth/cloud-platform '
            'y después repite el comando del piloto.') from error
    ee.Initialize(credentials=credentials,project=config['project'])
    print(f'GEE inicializado con credenciales Google Cloud existentes: {config["project"]}.',flush=True)
    return ee

def read_index(path,kind):
    if kind=='RMM' and 'romi' in path.name.lower():raise ValueError('El archivo es ROMI, no RMM. Usa --index-kind ROMI o indica el archivo RMM real.')
    if path.suffix.lower()=='.csv':
        d=pd.read_csv(path);d.columns=[str(c).strip().lower() for c in d.columns]
        if not {'date','rmm1','rmm2'}<=set(d):raise ValueError('CSV: columnas date,rmm1,rmm2')
        d=d.set_index(pd.to_datetime(d.date))[['rmm1','rmm2']];d.columns=['component1','component2']
    else:
        records=[]
        for line in path.read_text(encoding='utf-8-sig',errors='replace').splitlines():
            v=line.split()
            if len(v)<7:continue
            try:
                day=date(int(v[0]),int(v[1]),int(v[2]))
                a,b=(float(v[3]),float(v[4])) if kind=='RMM' else (float(v[4]),float(v[5]))
            except ValueError:continue
            records.append((day,a,b))
        d=pd.DataFrame(records,columns=['date','component1','component2']).set_index('date')
        d.index=pd.to_datetime(d.index)
    if d.empty or d.index.duplicated().any():raise ValueError('Índice vacío o con fechas duplicadas')
    d=d.apply(pd.to_numeric,errors='coerce').where(lambda x:x.abs()<100)
    return d.sort_index()

def download_rmm(path):
    """Public BoM endpoint requires a browser-compatible request header."""
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.stem+'.pending.txt')
    errors=[]
    for url in RMM_URLS:
        try:
            request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'text/plain,*/*;q=0.8'})
            with urllib.request.urlopen(request,timeout=60) as response:payload=response.read()
            temporary.write_bytes(payload)
            index=read_index(temporary,'RMM')
            if index.index.min()>pd.Timestamp('1981-01-01') or index.index.max()<pd.Timestamp('2016-12-31'):
                raise ValueError('RMM no cubre 1981–2016')
            temporary.replace(path)
            path.with_suffix('.source.json').write_text(json.dumps(dict(url=url,sha256=sha(path),
                first_date=str(index.index.min().date()),last_date=str(index.index.max().date()),rows=len(index),
                retrieved_utc=pd.Timestamp.now(tz='UTC').isoformat()),indent=2),encoding='utf-8')
            return index
        except Exception as e:errors.append(f'{url}: {e}')
    raise RuntimeError('No se pudo descargar RMM oficial. '+ ' | '.join(errors))

def figures(result,coords,root,out,kind):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap,BoundaryNorm
    from matplotlib.collections import LineCollection
    from resumen_amenazas_maize import boundaries
    lines=boundaries(root/'Repositorio/tesis-cereal-climate/web-v2/public/data/world_outline.geojson')
    bounds=[-1,-.6,-.4,-.2,-.1,.1,.2,.4,.6,1]
    cmap=ListedColormap(['#08306b','#08519c','#2171b5','#6baed6','#fffdf7','#fdae6b','#f16913','#d7301f','#7f0000'])
    norm=BoundaryNorm(bounds,cmap.N)
    zoom=len(coords)<=100
    xlim=(max(-180,coords.longitude.min()-2),min(180,coords.longitude.max()+2)) if zoom else (-180,180)
    ylim=(max(-60,coords.latitude.min()-2),min(85,coords.latitude.max()+2)) if zoom else (-58,82)
    for component in ['component1','component2']:
        label=f'{kind}{component[-1]}' if kind=='RMM' else f'ROMI PC{component[-1]}'
        fig,axes=plt.subplots(3,2,figsize=(16,12));fig.subplots_adjust(left=.035,right=.98,top=.90,bottom=.13,hspace=.25,wspace=.05)
        for ax,phase in zip(axes.flat,PHASES):
            s=result[(result.phase==phase)&(result.component==component)]
            ax.set_facecolor('#f5f7f8')
            if zoom:
                ax.scatter(s.longitude,s.latitude,c='#b8bec5',s=35)
                mesh=ax.scatter(s.longitude,s.latitude,c=s.pearson_r,cmap=cmap,norm=norm,s=28)
            else:
                r=np.rint((s.latitude.to_numpy()+89.75)/.5).astype(int);c=np.rint((s.longitude.to_numpy()+179.75)/.5).astype(int)
                gray=np.full((360,720),np.nan);gray[r,c]=1
                grid=np.full((360,720),np.nan);grid[r,c]=s.pearson_r.to_numpy()
                ax.pcolormesh(np.arange(-180,180.5,.5),np.arange(-90,90.5,.5),gray,cmap=ListedColormap(['#b8bec5']),rasterized=True)
                mesh=ax.pcolormesh(np.arange(-180,180.5,.5),np.arange(-90,90.5,.5),grid,cmap=cmap,norm=norm,rasterized=True)
            if lines:ax.add_collection(LineCollection(lines,colors='#bdc6cd',linewidths=.4))
            ax.set(xlim=xlim,ylim=ylim,title=phase);ax.set_aspect('equal',adjustable='box');ax.set_xticks([]);ax.set_yticks([])
            for spine in ax.spines.values():spine.set_visible(False)
        fig.suptitle(f'MAIZE · {label} vs daily climate-threshold occurrences\nPearson · same-day UTC pairs · daily RMM · '+('Regional pilot' if zoom else 'Cultivated pixel selection'),fontsize=14)
        cb=fig.colorbar(mesh,cax=fig.add_axes([.06,.075,.88,.016]),orientation='horizontal',ticks=bounds,spacing='uniform')
        cb.set_label('Pearson r · blue: negative | orange/red: positive',fontsize=9)
        fig.text(.035,.015,'Gray: undefined / insufficient data. Colors do not indicate significance. Daily observations are temporally dependent.',fontsize=9)
        for ext in ['png','pdf']:
            with (out/f'{kind}_{component}_six_phases.{ext}').open('wb') as handle:fig.savefig(handle,format=ext,dpi=220,facecolor='white')
        plt.close(fig)

def accumulate_daily(stats,daily,index,lookup):
    """Pair exact dates, retain valid zero counts; no phase/month/year averaging."""
    values=index.reindex(pd.to_datetime(daily.date))
    for phase,positions in daily.groupby('phase').indices.items():
        part=daily.iloc[positions]
        y=part.mean_occurrences_qualified.to_numpy(dtype=float)
        climate=(part.quality=='OK').to_numpy() & np.isfinite(y)
        p=PHASES.index(phase);i=lookup[int(part.pixel_id.iloc[0])]
        for component in range(2):
            x=values.iloc[positions,component].to_numpy(dtype=float)
            ok=climate & np.isfinite(x);a=x[ok];b=y[ok]
            stats[component,p,i]+=np.array([len(a),a.sum(),b.sum(),(a*a).sum(),(b*b).sum(),(a*b).sum()])


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=Path('C:/Users/paola/Tesis'))
    ap.add_argument('--index-file',type=Path)
    ap.add_argument('--index-kind',choices=['RMM','ROMI'],default='RMM')
    ap.add_argument('--download-rmm',action='store_true',help='Descargar RMM oficial si falta el archivo')
    ap.add_argument('--limit',type=int,default=10,help='10 para piloto; 0 para todos los píxeles')
    ap.add_argument('--workers',type=int,default=4)
    ap.add_argument('--min-days',type=int,default=20)
    ap.add_argument('--cache-only',action='store_true',help='Usar exclusivamente fechas ya guardadas, sin iniciar GEE')
    args=ap.parse_args();root=args.root
    if args.limit<0 or not 1<=args.workers<=8 or args.min_days<3:ap.error('Revisar limit, workers (1–8) y min-days (≥3)')
    index_path=args.index_file or root/'01_Data/RMM/rmm_official.txt'
    if not index_path.exists():
        if not args.download_rmm or args.index_kind!='RMM':ap.error('Indica --index-file con RMM1/RMM2 o usa --download-rmm. No se sustituye RMM por ROMI.')
        download_rmm(index_path)
    index=read_index(index_path,args.index_kind)
    base=root/'03_Resultados/Agroclima/vigente'
    plan_path=base/'ejecuciones/maize_seis_fases_GEE_1981_2016/plan_ejecucion.json'
    plan=json.loads(plan_path.read_text(encoding='utf-8'));rules=plan['rules']
    calendar_path=Path(plan['config']['calendar_dir'])/'maize-maize__rf.json'
    if sha(calendar_path)!=plan['calendar_sha256']:raise ValueError('El calendario cambió respecto al cálculo original')
    calendar=json.loads(calendar_path.read_text(encoding='utf-8'))
    coords=pd.read_csv(root/'02_Procesados/Pixeles_correlacion_vigentes/pixeles_maize.csv').sort_values('h5_index')
    if args.limit:coords=coords.iloc[:args.limit]
    coords=coords.reset_index(drop=True)
    pixels=[dict(pixel_id=int(r.pixel_id),lat=float(r.latitude),lon=float(r.longitude)) for r in coords.itertuples()]
    base_fp=sha(calendar_path)+json.dumps(rules,sort_keys=True)
    helper_hash=sha(Path(__file__).with_name('fechas_ocurrencias_core.py'))
    fp=hashlib.sha256((base_fp+helper_hash+'native_daily_flags_v1').encode()).hexdigest()[:16]
    legacy=hashlib.sha256((base_fp+sha(Path(__file__).with_name('maize_mjo_semanal.py'))+helper_hash).encode()).hexdigest()[:16]
    cache_root=root/'02_Procesados/Clima_ERA5_Land_cache/MJO_fechas'
    cache=cache_root/(legacy if (cache_root/legacy).is_dir() else fp)
    cache.mkdir(parents=True,exist_ok=True)
    stamp=time.strftime('%Y%m%d_%H%M%S')
    out=base/'correlaciones/maize_MJO_diario'/f'{args.index_kind}_{len(coords)}pix_{stamp}';out.mkdir(parents=True,exist_ok=False)
    print(f'{len(coords):,} píxeles × 36 temporadas: {len(coords)*36:,} solicitudes reanudables a GEE; workers={args.workers}.',flush=True)
    print('Cruce DIARIO: ocurrencias confirmadas y RMM1/RMM2 de la misma fecha. Sin promedios semanales.',flush=True)
    print('Ahora se guardan TODOS los días de cada fase (incluidos ceros), fechas de episodios por celda y estados diarios auditables.',flush=True)
    print(f'{args.index_kind}: {index.index.min().date()} a {index.index.max().date()}.',flush=True)
    ee=None if args.cache_only else initialize_gee(plan['config'])
    lookup=dict(zip(coords.pixel_id,range(len(coords))))
    # Sufficient statistics: n, sum x, sum y, sum x², sum y², sum xy.
    stats=np.zeros((2,6,len(coords),6));completed=0;new=0;new_seconds=0;started=time.perf_counter()
    annual_from_dates=np.full((6,len(coords),36),np.nan)
    jobs=iter((p,y) for p in pixels for y in range(1981,2017))
    total=len(coords)*36;first_daily=True;first_events=True
    with gzip.open(out/'daily_occurrences_with_MJO.csv.gz','wt',encoding='utf-8',newline='') as daily_stream, \
         gzip.open(out/'native_events_with_dates_MJO.csv.gz','wt',encoding='utf-8',newline='') as event_stream, \
         futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        pending={}
        def fill():
            while len(pending)<args.workers:
                job=next(jobs,None)
                if job is None:break
                if args.cache_only and not (cache/f'{job[0]["pixel_id"]}_{job[1]}.json').exists():
                    raise RuntimeError('Faltan fechas en la caché local. Repite sin --cache-only para extraer únicamente los lotes pendientes.')
                pending[pool.submit(compute_dates_job,ee,*job,rules,calendar,cache)]=time.perf_counter()
        fill()
        while pending:
            ready,_=futures.wait(pending,return_when=futures.FIRST_COMPLETED)
            for future in ready:
                tick=pending.pop(future);frame,cached=future.result()
                stem=f'{int(frame.pixel_id.iloc[0])}_{int(frame.season_year.iloc[0])}'
                daily=pd.read_csv(cache/f'{stem}.daily.csv.gz')
                event=pd.read_csv(cache/f'{stem}.events.csv.gz')
                for phase,group in daily.groupby('phase'):
                    if (group.quality=='OK').all():
                        annual_from_dates[PHASES.index(phase),lookup[int(group.pixel_id.iloc[0])],int(group.season_year.iloc[0])-1981]=group.mean_occurrences_qualified.sum()
                for component in ['component1','component2']:
                    daily[f'{args.index_kind}_{component}_on_date']=index[component].reindex(pd.to_datetime(daily.date)).to_numpy()
                    for date_column,prefix in [('qualification_date','qualification'),('event_start_within_phase','start')]:
                        event[f'{args.index_kind}_{component}_on_{prefix}']=index[component].reindex(pd.to_datetime(event[date_column])).to_numpy()
                daily.to_csv(daily_stream,index=False,header=first_daily);first_daily=False
                event.to_csv(event_stream,index=False,header=first_events);first_events=False
                accumulate_daily(stats,daily,index,lookup)
                completed+=1
                if not cached:new+=1;new_seconds+=time.perf_counter()-tick
                eta=(total-completed)*new_seconds/max(new,1)/args.workers
                print(f'{completed}/{total} | {"caché" if cached else "GEE"} | {(time.perf_counter()-started)/60:.1f} min | restante ≈{eta/3600:.2f} h (preliminar)',flush=True)
                if args.limit and new in [4,20,100]:
                    estimate=10923*36*new_seconds/new/args.workers/3600
                    print(f'Proyección orientativa para 10.923 píxeles, sin caché: ≈{estimate:.1f} h; revisar al terminar el piloto.',flush=True)
            fill()
    print('Verificando que las fechas reconstruyen los conteos originales...',flush=True)
    audit_path=out/'verification_against_original_annual_counts.csv'
    mismatch=0;checked=0;header=True
    source=base/'ejecuciones/maize_seis_fases_GEE_1981_2016/resumen_GDHY_anual.csv'
    for chunk in pd.read_csv(source,usecols=['pixel_id','season_year','phase','quality','mean_count_per_native_cell'],chunksize=100000):
        chunk=chunk[chunk.pixel_id.isin(lookup)&chunk.season_year.between(1981,2016)].copy()
        if chunk.empty:continue
        p=chunk.phase.map(dict(zip(PHASES,range(6)))).to_numpy(dtype=int)
        i=chunk.pixel_id.map(lookup).to_numpy(dtype=int);j=chunk.season_year.to_numpy(dtype=int)-1981
        chunk['reconstructed_from_dates']=annual_from_dates[p,i,j]
        a=chunk.mean_count_per_native_cell.to_numpy();b=chunk.reconstructed_from_dates.to_numpy()
        original_valid=(chunk.quality=='OK')&np.isfinite(a)
        chunk['matches']=np.where(original_valid,np.isclose(a,b,rtol=1e-8,atol=1e-8),~np.isfinite(b))
        mismatch+=int((~chunk.matches).sum());checked+=len(chunk)
        chunk.to_csv(audit_path,mode='w' if header else 'a',header=header,index=False);header=False
    if checked!=len(coords)*36*6 or mismatch:
        raise ValueError(f'La reconstrucción no coincide con los conteos originales: {mismatch} discrepancias; revisar {audit_path}. No se generan correlaciones ni mapas finales.')
    tables=[]
    for component in range(2):
        for p,phase in enumerate(PHASES):
            n,sx,sy,sxx,syy,sxy=stats[component,p].T
            vx=np.maximum(0,n*sxx-sx*sx);vy=np.maximum(0,n*syy-sy*sy)
            good=(n>=args.min_days)&(vx>1e-10)&(vy>1e-10)
            r=np.divide(n*sxy-sx*sy,np.sqrt(vx*vy),out=np.full(len(n),np.nan),where=good)
            t=coords[['pixel_id','latitude','longitude']].copy();t['phase']=phase;t['component']=f'component{component+1}'
            t['pearson_r']=np.clip(r,-1,1);t['n_days']=n.astype(int)
            t['status']=np.where(n<args.min_days,'INSUFFICIENT_DAYS',np.where(vy<=1e-10,'CONSTANT_OCCURRENCES',np.where(vx<=1e-10,'CONSTANT_INDEX','OK')))
            tables.append(t)
    result=pd.concat(tables);result.to_csv(out/'pearson_daily_by_pixel_phase.csv',index=False,encoding='utf-8-sig')
    figures(result,coords,root,out,args.index_kind)
    report=dict(index=str(index_path),index_kind=args.index_kind,index_sha256=sha(index_path),plan_sha256=sha(plan_path),
        code_sha256=sha(Path(__file__)),pixels=len(coords),years=[1981,2016],aggregation_days=1,lag_days=0,min_days=args.min_days,
        climate_cache=str(cache),elapsed_seconds=time.perf_counter()-started,
        annual_count_verification={'checked':checked,'mismatches':mismatch,'table':str(audit_path)},
        dated_outputs={'daily':'daily_occurrences_with_MJO.csv.gz','native_events':'native_events_with_dates_MJO.csv.gz',
            'native_states':'Per-job native.json.gz in climate_cache contains daily threshold hits and validity for each native cell.'},
        limitations=['Exploratory simple Pearson; no p-values, detrending or seasonal adjustment. Temporal dependence and shared seasonality require assessment.',
        'All valid phase days included, including zero-event days and final partial weeks. No 7-day grouping.',
        'Native events give observed phase-clipped start/end, qualification date and boundary flags; they are not unique events across phases or adjacent pixels.',
        'Heat episodes counted on qualification day; precipitation occurrences are individual threshold days. Source phase boundary clipping retained.',
        'Only complete native-cell coverage over the whole phase included; missing MJO dates excluded. No missing dates bridged.',
        'Same-day RMM1/RMM2 values, no averaging. Separate coefficients do not establish a joint MJO effect.',
        'No OLR, ONI-conditioned probabilities, loss validation or prediction. No significance claim based on daily sample size.'])
    (out/'provenance.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    import shutil
    repo=root/'Repositorio/tesis-cereal-climate'
    if repo.is_dir():shutil.copytree(out,repo/'outputs/agroclima_vigente/correlaciones/maize_MJO_diario'/out.name)
    print(f'Terminado. Tablas y figuras: {out}',flush=True)

if __name__=='__main__':main()
