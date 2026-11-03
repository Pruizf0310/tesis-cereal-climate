"""Pearson ONI v6–ocurrencias: todos los píxeles de maíz y seis fases. Sin gráficos."""
import argparse
import gzip
import hashlib
import json
import shutil
import time
import uuid
from pathlib import Path
import numpy as np
import pandas as pd
from correlacion_oni_amenazas import read_oni, window_oni, standardized

PHASES=['EST','VEG','REP','FLO','FIL','MAT']

def pearson_rows(x,y,min_years=20):
    valid=np.isfinite(x)&np.isfinite(y)
    x=np.where(valid,x,np.nan);y=np.where(valid,y,np.nan)
    n=valid.sum(axis=1);zx,sx=standardized(x);zy,sy=standardized(y)
    good=(n>=min_years)&(sx>1e-12)&(sy>1e-12)
    r=np.where(good,np.clip(np.einsum('ij,ij->i',zx,zy),-1,1),np.nan)
    status=np.where(n<min_years,'INSUFFICIENT_YEARS',np.where(sy<=1e-12,'CONSTANT_OCCURRENCES',np.where(sx<=1e-12,'CONSTANT_ONI','OK')))
    return x,y,n,r,status

def condition_summary(x,y):
    result={}
    for name,mask in [('positive',x>0),('negative',x<0),('zero',x==0)]:
        mask=mask&np.isfinite(x)&np.isfinite(y);n=mask.sum(axis=1)
        events=(mask&(y>0)).sum(axis=1)
        result[f'years_ONI_{name}']=n
        result[f'years_with_occurrences_ONI_{name}']=events
        result[f'percent_years_with_occurrences_ONI_{name}']=np.divide(100*events,n,out=np.full(len(n),np.nan),where=n>0)
        result[f'mean_count_ONI_{name}']=np.divide(np.where(mask,y,0).sum(axis=1),n,out=np.full(len(n),np.nan),where=n>0)
    return result

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=Path('C:/Users/paola/Tesis'))
    ap.add_argument('--min-years',type=int,default=20)
    args=ap.parse_args()
    if not 3<=args.min_years<=36:ap.error('--min-years debe estar entre 3 y 36')
    root=args.root;started=time.perf_counter()
    source=root/'03_Resultados/Agroclima/vigente/ejecuciones/maize_seis_fases_GEE_1981_2016/resumen_GDHY_anual.csv'
    pixels=root/'02_Procesados/Pixeles_correlacion_vigentes/pixeles_maize.csv'
    oni_path=root/'01_Data/ONI/ONI_v6_2026-10-08.html'
    for path in [source,pixels,oni_path]:
        if not path.is_file():raise FileNotFoundError(path)
    coords=pd.read_csv(pixels).sort_values('h5_index').reset_index(drop=True)
    if coords.pixel_id.duplicated().any():raise ValueError('Píxeles duplicados')
    mapping=dict(zip(coords.pixel_id,range(len(coords))))
    run=time.strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:6]
    parent=root/'03_Resultados/Agroclima/vigente/correlaciones/maize_ONI_Pearson'
    out=parent/run;out.mkdir(parents=True,exist_ok=False)
    oni,origin,sums,missing=read_oni(oni_path)
    oni.rename('oni').to_csv(out/'oni_v6_monthly_centers.csv',index_label='month_center')
    shape=(6,len(coords),36);x=np.full(shape,np.nan);y=x.copy();seen=np.zeros(shape,bool)
    rules={p:set() for p in PHASES};read=0;incomplete=0;missing_oni=0
    columns=['pixel_id','season_year','phase','start','end','quality','mean_count_per_native_cell',
             'variable','threshold','operator','min_days','count_unit']
    expected=int(np.prod(shape))
    print(f'Pearson únicamente: {len(coords):,} píxeles × 6 fases × 36 temporadas.',flush=True)
    print('CPU local. Sin GEE, gráficos, Spearman ni nuevas descargas. Preparación estimada: pocos minutos.',flush=True)
    with gzip.open(out/'annual_ONI_occurrence_pairs.csv.gz','wt',encoding='utf-8',newline='') as paired:
        first=True
        for df in pd.read_csv(source,usecols=columns,chunksize=100000):
            df=df[df.pixel_id.isin(mapping)&df.season_year.between(1981,2016)].copy()
            if df.empty:continue
            phase=df.phase.map(dict(zip(PHASES,range(6))))
            if phase.isna().any():raise ValueError('Fase desconocida')
            p=phase.to_numpy(dtype=int);i=df.pixel_id.map(mapping).to_numpy(dtype=int);j=df.season_year.to_numpy(dtype=int)-1981
            slots=np.ravel_multi_index((p,i,j),shape)
            if len(np.unique(slots))!=len(slots) or seen[p,i,j].any():raise ValueError('Filas duplicadas')
            seen[p,i,j]=True
            df['oni_phase']=window_oni(df.start,df.end,origin,sums,missing)
            good=(df.quality=='OK')&np.isfinite(df.oni_phase)&np.isfinite(df.mean_count_per_native_cell)
            if (df.loc[good,'mean_count_per_native_cell']<0).any():raise ValueError('Conteo negativo')
            df['included_pair']=good
            x[p,i,j]=np.where(good,df.oni_phase,np.nan)
            y[p,i,j]=np.where(good,df.mean_count_per_native_cell,np.nan)
            for rule in df[['phase','variable','operator','threshold','min_days','count_unit']].drop_duplicates().itertuples(index=False,name=None):rules[rule[0]].add(tuple(rule[1:]))
            incomplete+=int((df.quality!='OK').sum());missing_oni+=int(df.oni_phase.isna().sum())
            df.to_csv(paired,index=False,header=first);first=False
            read+=len(df);elapsed=time.perf_counter()-started
            eta=elapsed*(expected-read)/read
            print(f'Pares {read:,}/{expected:,} | {elapsed:.0f} s | restante de preparación ≈{eta:.0f} s',flush=True)
    if not seen.all():raise ValueError('Faltan combinaciones píxel–fase–año; no se publican resultados incompletos')
    preparation=time.perf_counter()-started;tables=[];summary=[]
    for p,phase in enumerate(PHASES):
        if len(rules[phase])!=1:raise ValueError(f'Reglas mezcladas en {phase}: {rules[phase]}')
        variable,operator,threshold,min_days,unit=next(iter(rules[phase]))
        a,b,n,r,status=pearson_rows(x[p],y[p],args.min_years)
        table=coords[['pixel_id','h5_index','latitude','longitude']].copy()
        table['phase']=phase;table['n_valid_years']=n;table['pearson_r']=r;table['status']=status
        table['variable']=variable;table['operator']=operator;table['threshold']=threshold
        table['min_days']=min_days;table['count_unit']=unit
        for key,value in condition_summary(a,b).items():table[key]=value
        tables.append(table)
        summary.append(dict(phase=phase,pixels=len(coords),valid_pearson=int((status=='OK').sum()),
            constant_occurrences=int((status=='CONSTANT_OCCURRENCES').sum()),insufficient_years=int((status=='INSUFFICIENT_YEARS').sum()),
            complete_36_year_pairs=int((n==36).sum())))
        print(f'{phase}: {sum(status=="OK"):,} coeficientes calculables.',flush=True)
    result=pd.concat(tables,ignore_index=True)
    result.to_csv(out/'pearson_by_pixel_phase.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(summary).to_csv(out/'coverage_summary.csv',index=False,encoding='utf-8-sig')
    report=dict(run=run,source=str(source),pixels=str(pixels),oni=str(oni_path),oni_version='ERSSTv6',
        rows_read=read,expected_pixel_phase_rows=len(result),incomplete_climate_rows=incomplete,missing_ONI_rows=missing_oni,
        min_years=args.min_years,preparation_seconds=preparation,
        hashes={str(path):digest(path) for path in [source,pixels,oni_path,Path(__file__)]},
        method='Pearson across annual pairs, separately per pixel and phase; raw counts and ONI; no detrending, significance tests or lag search.',
        temporal_matching='Daily-weighted mean of centered monthly ONI indices within inclusive actual hazard-window start/end dates; cross-year windows use the following year as needed.',
        definitions='Response: area-weighted mean native-cell count within GDHY pixel. ONI positive >0, negative <0, zero ==0; these groups are not official ENSO episode classifications.',
        limitations=['Contemporaneous association, not causation or forecast. Centered ONI can include information after the phase.',
        'Constant series undefined; genuine zeros retained, incomplete or absent values excluded.',
        'Simple Pearson coefficients only: temporal dependence, trends and multiple comparisons still require uncertainty assessment.',
        'Current calendar approximations, source thresholds and phase-window clipping retained; no rule correction.',
        'Any positive mean indicates occurrence in some native cells, not exposure of the whole GDHY pixel.',
        'Years label planting season, not necessarily harvest; yield and MJO not analyzed.'])
    report['elapsed_seconds']=time.perf_counter()-started
    (out/'provenance.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    guide=Path(__file__).with_name('LEEME_MAIZE_ONI_PEARSON.md')
    if guide.exists():shutil.copy2(guide,out/guide.name)
    mirror=root/'Repositorio/tesis-cereal-climate/outputs/agroclima_vigente/correlaciones/maize_ONI_Pearson'/run
    if (root/'Repositorio/tesis-cereal-climate').is_dir():
        shutil.copytree(out,mirror);print(f'Copia en repositorio local: {mirror}',flush=True)
    (parent/'ultima_ejecucion.json').write_text(json.dumps({'run':run,'output':str(out)},indent=2),encoding='utf-8')
    print(f'Terminado en {time.perf_counter()-started:.1f} s. Tablas: {out}',flush=True)

if __name__=='__main__':main()
