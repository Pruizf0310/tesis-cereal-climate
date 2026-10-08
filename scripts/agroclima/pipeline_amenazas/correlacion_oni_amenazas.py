"""Local vectorized phase-window ONI vs annual hazard-count correlations."""
import argparse
import csv
import gzip
import hashlib
import html
import json
import re
import shutil
import time
from pathlib import Path

import numpy as np
import pandas as pd

PHASES=['EST','VEG','REP','FLO','FIL','MAT']
SEASONS=['DJF','JFM','FMA','MAM','AMJ','MJJ','JJA','JAS','ASO','SON','OND','NDJ']


def read_oni(path):
    if path.suffix.lower() in {'.html','.htm'}:
        rows=[]
        for tr in re.findall(r'<tr\b[^>]*>(.*?)</tr>',path.read_text(encoding='utf-8',errors='replace'),flags=re.S|re.I):
            cells=[html.unescape(re.sub(r'<[^>]+>','',s)).strip() for s in re.findall(r'<td\b[^>]*>(.*?)</td>',tr,flags=re.S|re.I)]
            if len(cells)>=13 and re.fullmatch(r'\d{4}',cells[0]):rows.append(cells[:13])
        frame=pd.DataFrame(rows,columns=['Year']+SEASONS)
    else:
        with path.open(encoding='utf-8-sig') as source:header=source.readline()
        frame=pd.read_csv(path,sep='\t' if '\t' in header else r'\s+')
    if not set(['Year']+SEASONS)<=set(frame):raise ValueError('Formato ONI: se requieren Year, DJF...NDJ')
    frame['Year']=pd.to_numeric(frame['Year'],errors='coerce');frame=frame.dropna(subset=['Year'])
    monthly=[]
    for row in frame.to_dict('records'):
        for month,season in enumerate(SEASONS,1):
            value=pd.to_numeric(row[season],errors='coerce')
            if pd.notna(value) and abs(value)>10:value=np.nan
            monthly.append((pd.Timestamp(int(row['Year']),month,1),float(value)))
    series=pd.Series(dict(monthly)).sort_index()
    if len(series)!=len(monthly):raise ValueError('Años ONI duplicados')
    if series.empty:raise ValueError('ONI vacío')
    daily_dates=pd.date_range(series.index.min(),series.index.max()+pd.offsets.MonthEnd(0),freq='D')
    daily=series.reindex(daily_dates.to_period('M').to_timestamp()).to_numpy()
    return series,daily_dates[0].to_datetime64().astype('datetime64[D]'),np.r_[0,np.nancumsum(daily)],np.r_[0,np.cumsum(np.isnan(daily))]


def window_oni(start,end,origin,sums,missing):
    a=(pd.to_datetime(start).to_numpy(dtype='datetime64[D]')-origin).astype(int)
    b=(pd.to_datetime(end).to_numpy(dtype='datetime64[D]')-origin).astype(int)+1
    result=np.full(len(a),np.nan)
    valid=(a>=0)&(b<len(sums))&(b>a)
    indices=np.flatnonzero(valid)
    indices=indices[(missing[b[indices]]-missing[a[indices]])==0]
    result[indices]=(sums[b[indices]]-sums[a[indices]])/(b[indices]-a[indices])
    return result


def standardized(a):
    valid=np.isfinite(a)
    n=valid.sum(axis=1)
    mean=np.divide(np.nansum(a,axis=1),n,out=np.zeros(len(a)),where=n>0)
    centered=np.where(valid,a-mean[:,None],0)
    norm=np.sqrt((centered*centered).sum(axis=1))
    return np.divide(centered,norm[:,None],out=np.zeros_like(centered),where=norm[:,None]>0),norm


def correlations(x,y,min_years):
    mask=np.isfinite(x)&np.isfinite(y)
    x=np.where(mask,x,np.nan);y=np.where(mask,y,np.nan)
    n=mask.sum(axis=1)
    zx,sx=standardized(x);zy,sy=standardized(y)
    rx=pd.DataFrame(x).rank(axis=1,method='average',na_option='keep').to_numpy()
    ry=pd.DataFrame(y).rank(axis=1,method='average',na_option='keep').to_numpy()
    zrx,_=standardized(rx);zry,_=standardized(ry)
    good=(n>=min_years)&(sx>1e-12)&(sy>1e-12)
    pearson=np.where(good,np.clip(np.einsum('ij,ij->i',zx,zy),-1,1),np.nan)
    spearman=np.where(good,np.clip(np.einsum('ij,ij->i',zrx,zry),-1,1),np.nan)
    status=np.where(n<min_years,'INSUFFICIENT_YEARS',np.where(sy<=1e-12,'CONSTANT_HAZARD',np.where(sx<=1e-12,'CONSTANT_ONI','OK')))
    return dict(n=n,status=status,pearson=pearson,spearman=spearman,
                zx=zx,zy=zy,zrx=zrx,zry=zry,full=good&(n==x.shape[1]))


def block_permutations(n,number,block_years,seed):
    if not 1<=block_years<n:raise ValueError('Longitud de bloque debe ser >=1 y menor que el número de años')
    blocks=[np.arange(i,min(i+block_years,n)) for i in range(0,n,block_years)]
    rng=np.random.default_rng(seed)
    return np.array([np.concatenate([blocks[i] for i in rng.permutation(len(blocks))]) for _ in range(number)])


def permutation_p(stats,indices,pixel_batch=128,permutation_batch=64):
    ids=np.flatnonzero(stats['full'])
    results={method:np.full(len(stats['n']),np.nan) for method in ['pearson','spearman']}
    for start in range(0,len(ids),pixel_batch):
        subset=ids[start:start+pixel_batch]
        for method,xname,yname in [('pearson','zx','zy'),('spearman','zrx','zry')]:
            x=stats[xname][subset];y=stats[yname][subset];observed=abs(stats[method][subset])
            count=np.zeros(len(subset),dtype=int)
            for offset in range(0,len(indices),permutation_batch):
                perm=indices[offset:offset+permutation_batch]
                null=np.einsum('ij,ikj->ik',y,x[:,perm],optimize=True)
                count+=(np.abs(null)>=observed[:,None]-1e-12).sum(axis=1)
            results[method][subset]=(count+1)/(len(indices)+1)
    return results


def fdr_bh(values):
    q=np.full_like(values,np.nan,dtype=float);ids=np.flatnonzero(np.isfinite(values))
    if not len(ids):return q
    order=ids[np.argsort(values[ids])];raw=values[order]*len(order)/np.arange(1,len(order)+1)
    q[order]=np.minimum(1,np.minimum.accumulate(raw[::-1])[::-1])
    return q


def map_figure(results,coords,method,output,outline,version):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    lines=[]
    def geometry(g):
        if g['type']=='Polygon':lines.extend(g['coordinates'])
        elif g['type']=='MultiPolygon':
            for polygon in g['coordinates']:lines.extend(polygon)
        elif g['type']=='GeometryCollection':
            for child in g['geometries']:geometry(child)
    if outline.exists():
        data=json.loads(outline.read_text(encoding='utf-8'))
        for feature in data.get('features',[]):
            if feature.get('geometry'):geometry(feature['geometry'])
    # Do not draw world-spanning edges across the antimeridian.
    lines=[line for line in lines if len(line)>1 and max(abs(np.diff(np.asarray(line)[:,0])),default=0)<180]
    fig,axes=plt.subplots(3,2,figsize=(14,10))
    row=((coords.latitude+89.75)/.5).round().astype(int).to_numpy()
    col=((coords.longitude+179.75)/.5).round().astype(int).to_numpy()
    for ax,phase in zip(axes.flat,PHASES):
        sub=results[results.phase==phase].set_index('pixel_id').reindex(coords.pixel_id)
        gray=np.full((360,720),np.nan);gray[row,col]=1
        grid=np.full((360,720),np.nan);grid[row,col]=sub[method].to_numpy()
        ax.pcolormesh(np.arange(-180,180.5,.5),np.arange(-90,90.5,.5),gray,cmap='Greys',vmin=0,vmax=4,rasterized=True)
        mesh=ax.pcolormesh(np.arange(-180,180.5,.5),np.arange(-90,90.5,.5),grid,cmap='RdBu_r',vmin=-1,vmax=1,rasterized=True)
        if lines:ax.add_collection(LineCollection(lines,colors='#9ca3af',linewidths=.3))
        ax.set(xlim=(-180,180),ylim=(-60,85),xlabel='Longitud',ylabel='Latitud')
        ax.set_title(f'{phase} · {"días de lluvia >10 mm" if phase=="MAT" else "episodios de calor"}',loc='left',fontsize=11)
        ax.grid(alpha=.1);ax.set_aspect('equal',adjustable='box')
    fig.suptitle(f'Maíz · ONI de la fase frente a frecuencia de amenazas\n{method.capitalize()} · 1981–2016 · {version}',fontsize=15,y=.99)
    fig.subplots_adjust(left=.06,right=.90,top=.89,bottom=.10,hspace=.35,wspace=.18)
    bar=fig.colorbar(mesh,cax=fig.add_axes([.93,.22,.012,.55]));bar.set_label('Coeficiente de correlación')
    fig.text(.06,.025,'Rojo: ONI más alto asociado a más amenazas. Azul: ONI más alto asociado a menos amenazas.\n'
             'Gris: cultivo con correlación no definida / datos insuficientes. Mapas exploratorios; color no implica significancia ni causalidad.',fontsize=9,color='#374151')
    fig.savefig(output,dpi=170);plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default=str(Path(__file__).with_name('config_correlacion_oni_maize.json')))
    parser.add_argument('--benchmark-only',action='store_true')
    args=parser.parse_args()
    c=json.loads(Path(args.config).read_text(encoding='utf-8'))
    out=Path(c['output']);out.mkdir(parents=True,exist_ok=True)
    started=time.perf_counter()
    coords=pd.read_csv(c['pixels_csv']).sort_values('h5_index').reset_index(drop=True)
    if coords.pixel_id.duplicated().any():raise ValueError('Píxeles duplicados')
    years=np.arange(c['start_year'],c['end_year']+1);ny=len(years);npix=len(coords)
    mapping=dict(zip(coords.pixel_id,np.arange(npix)))
    monthly,origin,sums,missing=read_oni(Path(c['oni_path']))
    monthly.rename('oni').to_csv(out/'oni_centros_mensuales.csv',index_label='month_center')
    x=np.full((6,npix,ny),np.nan);y=x.copy();seen=np.zeros_like(x,dtype=bool)
    columns=['pixel_id','season_year','phase','start','end','quality','mean_count_per_native_cell','count_unit']
    expected=npix*ny*6;read=0;oni_missing=0;incomplete=0
    paired=None if args.benchmark_only else gzip.open(out/'pares_oni_amenaza.csv.gz','wt',encoding='utf-8',newline='')
    first_chunk=True
    try:
        for chunk in pd.read_csv(c['hazard_results'],usecols=columns,chunksize=100000):
            valid=chunk.pixel_id.isin(mapping)&chunk.season_year.between(years[0],years[-1])
            chunk=chunk[valid].copy();read+=len(chunk)
            if chunk.empty:continue
            chunk['oni_phase']=window_oni(chunk.start,chunk.end,origin,sums,missing)
            incomplete+=int((chunk.quality!='OK').sum());oni_missing+=int(chunk.oni_phase.isna().sum())
            a=chunk.phase.map(dict(zip(PHASES,range(6))))
            if a.isna().any():raise ValueError('Fase desconocida')
            i=chunk.pixel_id.map(mapping).to_numpy();j=chunk.season_year.to_numpy()-years[0];a=a.to_numpy()
            slots=np.ravel_multi_index((a,i,j),x.shape)
            if len(np.unique(slots))!=len(slots) or seen[a,i,j].any():raise ValueError('Observaciones duplicadas')
            seen[a,i,j]=True
            good=(chunk.quality=='OK')&chunk.oni_phase.notna()&chunk.mean_count_per_native_cell.notna()
            x[a,i,j]=np.where(good,chunk.oni_phase,np.nan)
            y[a,i,j]=np.where(good,chunk.mean_count_per_native_cell,np.nan)
            if paired is not None:
                chunk.to_csv(paired,index=False,header=first_chunk);first_chunk=False
            print(f'Preparación: {read:,}/{expected:,} filas · {(time.perf_counter()-started):.1f} s',flush=True)
    finally:
        if paired is not None:paired.close()
    if read!=expected or not seen.all():raise ValueError('Faltan combinaciones píxel–año–fase en los resultados de entrada')
    prepared=time.perf_counter()-started
    perms=block_permutations(ny,c['permutations'],c['block_years'],c['seed'])
    rng=np.random.default_rng(c['seed']);timings=[];bench=[]
    for p,phase in enumerate(PHASES):
        tick=time.perf_counter();stats=correlations(x[p],y[p],c['min_years'])
        valid=np.flatnonzero(stats['full']);sample=rng.choice(valid,min(128,len(valid)),replace=False) if len(valid) else []
        small={k:v[sample] for k,v in stats.items()};test_perms=perms[:min(99,len(perms))]
        t=time.perf_counter();permutation_p(small,test_perms);seconds=time.perf_counter()-t
        estimate=seconds*len(valid)/max(len(sample),1)*len(perms)/max(len(test_perms),1)
        bench.append(dict(phase=phase,valid_pixels=len(valid),sample_pixels=len(sample),sample_permutations=len(test_perms),
                          benchmark_seconds=seconds,estimated_permutation_seconds=estimate))
        print(f'{phase}: {len(valid)} píxeles evaluables; remuestreo completo estimado {estimate:.1f} s',flush=True)
        if args.benchmark_only:continue
        pvalues=permutation_p(stats,perms)
        table=coords[['pixel_id','latitude','longitude']].copy()
        table['phase']=phase;table['n_years']=stats['n'];table['status']=stats['status']
        for method in ['pearson','spearman']:
            table[method]=stats[method];table[f'p_block_{method}']=pvalues[method]
        timings.append((table,time.perf_counter()-tick))
        print(f'{phase}: correlaciones y permutaciones terminadas en {timings[-1][1]:.1f} s',flush=True)
    estimated=prepared+sum(b['estimated_permutation_seconds'] for b in bench)
    if not args.benchmark_only:
        result=pd.concat([t[0] for t in timings],ignore_index=True)
        for method in ['pearson','spearman']:
            result[f'q_fdr_{method}']=fdr_bh(result[f'p_block_{method}'].to_numpy())
        result.to_csv(out/'correlaciones_por_pixel_fase.csv',index=False,encoding='utf-8-sig')
        for method in ['pearson','spearman']:
            map_figure(result,coords,method,out/f'mapas_{method}_seis_fases.png',Path(c['world_outline']),c['oni_version'])
        summary=[]
        for phase,sub in result.groupby('phase',sort=False):
            summary.append(dict(phase=phase,pixels=len(sub),valid_correlations=int((sub.status=='OK').sum()),
                                constant_hazard=int((sub.status=='CONSTANT_HAZARD').sum()),
                                insufficient_years=int((sub.status=='INSUFFICIENT_YEARS').sum()),
                                significant_spearman_exploratory=int((sub.q_fdr_spearman<=.05).sum())))
        pd.DataFrame(summary).to_csv(out/'resumen_correlaciones.csv',index=False,encoding='utf-8-sig')
    report=dict(config=c,benchmark_only=args.benchmark_only,preparation_seconds=prepared,
                estimated_preparation_plus_permutations_seconds=estimated,benchmarks=bench,
                elapsed_seconds=time.perf_counter()-started,rows_read=read,incomplete_hazard_rows=incomplete,
                missing_ONI_rows=oni_missing,pixel_phase_tests=npix*6,
                hashes={key:hashlib.sha256(Path(c[key]).read_bytes()).hexdigest() for key in ['oni_path','pixels_csv']},
                methods='Pearson and Spearman; ONI phase mean weighted by calendar days, centered monthly 3-month indices; lag 0. Constant series undefined; incomplete hazard windows excluded. P-values: common random permutations of 3-year ONI blocks, full 36-year pairs only; BH FDR across all pixels and six phases separately for each method.',
                limitations='Exploratory association, not causal or predictive validation. Block exchangeability/stationarity and block-length sensitivity require evaluation; no trend adjustment. Finite permutation resolution. Existing hazard-window approximations and FIL threshold discrepancy retained. Dates label planting year, not yield year. No MJO or yield correlation in this run.')
    filename='benchmark_tiempo.json' if args.benchmark_only else 'provenance_correlacion.json'
    (out/filename).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    if c.get('repository_results'):
        dest=Path(c['repository_results']);dest.mkdir(parents=True,exist_ok=True)
        for file in out.iterdir():
            if file.is_file():shutil.copy2(file,dest/file.name)
    print(f'Terminado en {report["elapsed_seconds"]:.1f} segundos. Resultados: {out}',flush=True)


if __name__=='__main__':main()
