"""Six annual maize hazard counts vs detrended yield, pixel by pixel. Local only."""
import argparse
import gzip
import hashlib
import json
import re
import shutil
import time
from pathlib import Path
import h5py
import numpy as np
import pandas as pd

PHASES=['EST','VEG','REP','FLO','FIL','MAT']

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''):h.update(part)
    return h.hexdigest()

def pearson(x,y):
    if len(x)<3 or np.std(x)<1e-12 or np.std(y)<1e-12:return np.nan
    return float(np.corrcoef(x,y)[0,1])

def ols(x,y):
    """Fit centered/scaled design; never use pseudoinverse to assign aliased phases."""
    mean=x.mean(axis=0);scale=x.std(axis=0)
    active=scale>1e-12
    z=(x[:,active]-mean[active])/scale[active]
    design=np.column_stack([np.ones(len(x)),z])
    if len(x)<=design.shape[1] or np.linalg.matrix_rank(design)<design.shape[1]:return None
    theta=np.linalg.lstsq(design,y,rcond=None)[0]
    beta=np.zeros(6);beta[active]=theta[1:]/scale[active]
    prediction=y.mean()+(x-mean)@beta
    condition=float(np.linalg.cond(design))
    vif=np.full(6,np.nan)
    if active.any():vif[active]=np.diag(np.linalg.inv(z.T@z))*np.sum(z*z,axis=0)
    return dict(beta=beta,active=active,mean=mean,prediction=prediction,condition=condition,vif=vif)

def estimate(x,y,years,min_years=20,block_years=6):
    good=np.isfinite(y)&np.isfinite(x).all(axis=1)
    a=x[good];b=y[good];t=years[good];n=len(b)
    result=dict(n_valid_years=n,n_years_without_events=int((a==0).all(axis=1).sum()),
        n_years_with_events=int((a>0).any(axis=1).sum()),status='INSUFFICIENT_YEARS')
    phases=[dict(phase=p,pearson_r=pearson(a[:,j],b),coefficient=np.nan,partial_r2=np.nan,vif=np.nan,
        status='INSUFFICIENT_YEARS',unit='yield_file_units per mean native-cell episode' if p!='MAT' else 'yield_file_units per mean native-cell precipitation-threshold day') for j,p in enumerate(PHASES)]
    fit_values=np.full(len(y),np.nan);cv_values=fit_values.copy();contributions=np.full((len(y),6),np.nan)
    if n<min_years:return result,phases,fit_values,cv_values,contributions
    if np.std(b)<1e-12:
        result['status']='CONSTANT_YIELD'
        for row in phases:row['status']='CONSTANT_YIELD'
        return result,phases,fit_values,cv_values,contributions
    fit=ols(a,b)
    if fit is None:
        result['status']='PHASES_NOT_SEPARABLE'
        for row in phases:row['status']='PHASES_NOT_SEPARABLE'
        return result,phases,fit_values,cv_values,contributions
    pred=fit['prediction'];sse=float(np.sum((b-pred)**2));sst=float(np.sum((b-b.mean())**2));k=int(fit['active'].sum())
    unstable=fit['condition']>30 or np.nanmax(np.r_[fit['vif'],0])>10
    result.update(status='UNSTABLE_COLLINEARITY' if unstable else 'OK',n_variable_phases=k,
        r2=1-sse/sst,adjusted_r2=1-(sse/(n-k-1))/(sst/(n-1)),rmse=float(np.sqrt(sse/n)),condition_number=fit['condition'])
    fit_values[good]=pred;contributions[good]=(a-fit['mean'])*fit['beta']
    result['fitted_mean_yield']=float(b.mean())
    for j,row in enumerate(phases):
        if not fit['active'][j]:row['status']='CONSTANT_PHASE';continue
        reduced=a.copy();reduced[:,j]=0
        reduced_fit=ols(reduced,b)
        reduced_sse=float(np.sum((b-reduced_fit['prediction'])**2)) if reduced_fit else np.nan
        partial=(reduced_sse-sse)/reduced_sse if reduced_sse>1e-12 else np.nan
        row.update(coefficient=float(fit['beta'][j]),partial_r2=float(np.clip(partial,0,1)) if np.isfinite(partial) else np.nan,
            vif=float(fit['vif'][j]),status='UNSTABLE_COLLINEARITY' if unstable else 'OK')
    # Contiguous held-out year blocks; training transformations recomputed for each block.
    cv=np.full(n,np.nan);fold=(t-1981)//block_years
    for block in np.unique(fold):
        test=fold==block;train=~test
        if train.sum()<max(10,k+3):continue
        model=ols(a[train],b[train])
        if model is None:continue
        # A phase variable only in the held-out block cannot have a trained coefficient.
        if np.any((~model['active'])&fit['active']):continue
        cv[test]=b[train].mean()+(a[test]-model['mean'])@model['beta']
    valid=np.isfinite(cv);cv_values[np.flatnonzero(good)[valid]]=cv[valid]
    result['n_cv_years']=int(valid.sum())
    if valid.all():
        result['blocked_cv_r2']=1-float(np.sum((b-cv)**2))/sst
        result['blocked_cv_rmse']=float(np.sqrt(np.mean((b-cv)**2)))
    else:result['blocked_cv_r2']=np.nan;result['blocked_cv_rmse']=np.nan
    return result,phases,fit_values,cv_values,contributions

def decode(value):
    return value.decode() if isinstance(value,(bytes,np.bytes_)) else str(value)

def read_yield(path,coords):
    with h5py.File(path,'r') as f:
        lat=f['lat'][:];lon=(f['lon'][:]+180)%360-180
        # Match coordinate values independently of CSV array indices.
        lat_map={round(float(v),8):i for i,v in enumerate(lat)}
        lon_map={round(float(v),8):i for i,v in enumerate(lon)}
        ii=np.array([lat_map[round(float(v),8)] for v in coords.latitude]);jj=np.array([lon_map[round(float(v),8)] for v in coords.longitude])
        if not np.array_equal(ii,coords.lat_idx.to_numpy()) or not np.array_equal(jj,coords.lon_idx.to_numpy()):raise ValueError('Pixel CSV indices do not match yield coordinates')
        units=decode(f['time'].attrs['units']);match=re.fullmatch(r'days since (\d{4}-\d{2}-\d{2})(?:.*)',units)
        if not match:raise ValueError(f'Unknown time units: {units}')
        dates=pd.Timestamp(match[1])+pd.to_timedelta(f['time'][:],unit='D');years=dates.year.to_numpy()
        if len(set(years))!=len(years):raise ValueError('Duplicate annual yield labels')
        var=f['var']
        if var.shape!=(len(lat),len(lon),len(years)):raise ValueError('Yield dimensions differ from lat,lon,time')
        values=var[:][ii,jj,:].astype(float)
        for key in ['_FillValue','missing_value']:
            if key in var.attrs:
                for fill in np.asarray(var.attrs[key]).ravel():
                    if np.isfinite(fill):values[values==fill]=np.nan
        if 'scale_factor' in var.attrs:values*=float(np.asarray(var.attrs['scale_factor']).ravel()[0])
        if 'add_offset' in var.attrs:values+=float(np.asarray(var.attrs['add_offset']).ravel()[0])
        data_units=decode(var.attrs.get('units','UNSPECIFIED_IN_DETRENDED_FILE'))
    return years,values,data_units

def plot_pixel(table,pixel,out,alignment):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm,ListedColormap
    s=table[table.pixel_id==pixel].sort_values('yield_year')
    x=s.yield_year.to_numpy();counts=s[PHASES].to_numpy().T
    upper=max(16,float(np.nanmax(counts))+1) if np.isfinite(counts).any() else 16
    bins=[0,1e-12,.25,.5,1,2,4,8,upper]
    cmap=ListedColormap(['#f7f7f7','#fff7bc','#fee391','#fec44f','#fe9929','#ec7014','#cc4c02','#7f2704']);cmap.set_bad('#9e9e9e')
    fig,axes=plt.subplots(3,1,figsize=(15,10),sharex=True,gridspec_kw={'height_ratios':[2,2,1.2]},layout='constrained')
    edges=np.r_[x-.5,x[-1]+.5]
    mesh=axes[0].pcolormesh(edges,np.arange(7)-.5,counts,cmap=cmap,norm=BoundaryNorm(bins,cmap.N),shading='flat')
    axes[0].set_yticks(range(6),PHASES);axes[0].invert_yaxis();axes[0].set_title('Observed climate-threshold counts by phase',fontsize=12)
    cb=fig.colorbar(mesh,ax=axes[0],orientation='vertical',fraction=.025,pad=.015,ticks=[0,.25,.5,1,2,4,8]);cb.set_label('Mean count per native cell',fontsize=9)
    axes[1].plot(x,s.yield_detrended,'o-',color='#222222',label='Observed detrended yield')
    axes[1].plot(x,s.fitted_yield,'-',color='#c14532',label='Six-phase fit (in sample)')
    axes[1].plot(x,s.blocked_cv_prediction,'--',color='#2463a6',label='Held-out year-block prediction')
    axes[1].set_ylabel('Yield: original file units');axes[1].legend(fontsize=9,ncol=3);axes[1].grid(axis='y',alpha=.2)
    for p in PHASES:axes[2].plot(x,s[f'associated_deviation_{p}'],label=p,lw=1.3)
    axes[2].axhline(0,color='#888888',lw=.8);axes[2].set_ylabel('Fitted phase deviation\n(original yield units)');axes[2].legend(ncol=6,fontsize=9)
    axes[2].set_xlabel('Yield-year label');axes[2].set_xticks(x[::2])
    fig.suptitle(f'MAIZE | Pixel {pixel} | Annual phase exposure and yield\nYear alignment: {alignment} · observational associations, not causal loss attribution',fontsize=14)
    fig.supxlabel('EST–FIL: heat episodes; MAT: precipitation-threshold days. Counts are spatial means, not unique regional events.\nPhase deviations are centered fitted associations; they are not percentages of yield or independent causal contributions.',fontsize=9)
    for ext in ['png','pdf']:fig.savefig(out/f'pixel_{pixel}_annual_history.{ext}',dpi=200,facecolor='white')
    plt.close(fig)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=Path('C:/Users/paola/Tesis'))
    ap.add_argument('--min-years',type=int,default=20)
    ap.add_argument('--block-years',type=int,default=6)
    ap.add_argument('--pixel',type=int,help='Pixel for the annual-history figure; default first selected pixel')
    ap.add_argument('--year-alignment',choices=['both','same-label','maturity-year'],default='both')
    args=ap.parse_args()
    if args.min_years<10 or not 2<=args.block_years<=12:ap.error('min-years >=10; block-years 2–12')
    root=args.root;base=root/'03_Resultados/Agroclima/vigente';started=time.perf_counter()
    source=base/'ejecuciones/maize_seis_fases_GEE_1981_2016/resumen_GDHY_anual.csv'
    coords_path=root/'02_Procesados/Pixeles_correlacion_vigentes/pixeles_maize.csv'
    yield_path=root/'02_Procesados/GDHY_detrend/maize_yield_1981_2016_DETREND_clean.nc'
    coords=pd.read_csv(coords_path).sort_values('h5_index').reset_index(drop=True)
    if coords.pixel_id.duplicated().any():raise ValueError('Duplicate pixels')
    mapping=dict(zip(coords.pixel_id,range(len(coords))));shape=(len(coords),36,6)
    counts=np.full(shape,np.nan);seen=np.zeros(shape,bool);ends=np.full((len(coords),36),-1,int);rule_sets={p:set() for p in PHASES}
    print(f'CPU local: {len(coords):,} píxeles × 36 temporadas × seis fases. Sin GEE, ONI, MJO ni descargas.',flush=True)
    print('Se conservan conteos y rendimientos originales. Tiempo aún no medido; se muestra progreso.',flush=True)
    columns=['pixel_id','season_year','phase','quality','mean_count_per_native_cell','start','end','variable','operator','threshold','min_days','count_unit']
    rows=0
    for d in pd.read_csv(source,usecols=columns,chunksize=100000):
        d=d[d.pixel_id.isin(mapping)&d.season_year.between(1981,2016)].copy()
        if d.empty:continue
        i=d.pixel_id.map(mapping).to_numpy(int);j=d.season_year.to_numpy(int)-1981;k=d.phase.map(dict(zip(PHASES,range(6)))).to_numpy(int)
        slots=np.ravel_multi_index((i,j,k),shape)
        if len(np.unique(slots))!=len(slots) or seen[i,j,k].any():raise ValueError('Duplicate pixel-year-phase records')
        seen[i,j,k]=True;v=d.mean_count_per_native_cell.to_numpy(float)
        good=d.quality.eq('OK').to_numpy()&np.isfinite(v)
        if (v[good]<0).any():raise ValueError('Negative climate counts')
        counts[i,j,k]=np.where(good,v,np.nan)
        mat=k==5;ends[i[mat],j[mat]]=pd.to_datetime(d.loc[mat,'end']).dt.year.to_numpy()
        for p,var,op,threshold,minimum,unit in d[['phase','variable','operator','threshold','min_days','count_unit']].drop_duplicates().itertuples(index=False,name=None):rule_sets[p].add((var,op,float(threshold),int(minimum),unit))
        rows+=len(d);print(f'Lectura: {rows:,}/{np.prod(shape):,} filas | {time.perf_counter()-started:.0f} s',flush=True)
    if not seen.all():raise ValueError('Missing pixel-year-phase records; no result published')
    if any(len(v)!=1 for v in rule_sets.values()):raise ValueError('Mixed phase rules')
    yield_years,yield_values,units=read_yield(yield_path,coords);ymap=dict(zip(yield_years,range(len(yield_years))))
    stamp=time.strftime('%Y%m%d_%H%M%S');out=base/'rendimiento/maize_seis_fases'/stamp;out.mkdir(parents=True,exist_ok=False)
    sy=np.arange(1981,2017);audit=coords[['pixel_id','latitude','longitude']].copy()
    audit['seasons_maturity_in_different_year']=(ends!=sy[None,:]).sum(axis=1)
    audit['maturity_year_is_harvest_proxy']=True;audit.to_csv(out/'year_alignment_audit.csv',index=False)
    modes=['same-label','maturity-year'] if args.year_alignment=='both' else [args.year_alignment]
    for mode in modes:
        destination=out/mode;destination.mkdir();paired=[];summaries=[];coefficients=[];combinations=[]
        for idx,p in enumerate(coords.itertuples()):
            years=sy.copy() if mode=='same-label' else ends[idx].copy()
            if len(set(years))!=len(years):raise ValueError('Season-to-yield mapping is not one-to-one')
            y=np.array([yield_values[idx,ymap[v]] if v in ymap else np.nan for v in years])
            x=counts[idx];result,phase_rows,fit,cv,contrib=estimate(x,y,years,args.min_years,args.block_years)
            result.update(pixel_id=int(p.pixel_id),latitude=p.latitude,longitude=p.longitude);summaries.append(result)
            for r in phase_rows:r.update(pixel_id=int(p.pixel_id),latitude=p.latitude,longitude=p.longitude);coefficients.append(r)
            frame=pd.DataFrame(x,columns=PHASES)
            frame['pixel_id']=int(p.pixel_id);frame['season_year']=sy;frame['yield_year']=years
            frame['yield_detrended']=y;frame['fitted_yield']=fit;frame['blocked_cv_prediction']=cv
            frame['complete_pair']=np.isfinite(x).all(axis=1)&np.isfinite(y)
            complete=np.isfinite(x).all(axis=1)
            frame['event_combination']=['+'.join(PHASES[j] for j in range(6) if row[j]>0) or 'NONE' if ok else 'INCOMPLETE_CLIMATE' for row,ok in zip(x,complete)]
            for j,phase in enumerate(PHASES):frame[f'associated_deviation_{phase}']=contrib[:,j]
            frame['year_alignment']=mode;paired.append(frame)
            for combo,g in frame[frame.complete_pair].groupby('event_combination'):
                combinations.append(dict(pixel_id=int(p.pixel_id),combination=combo,n_years=len(g),mean_yield=float(g.yield_detrended.mean()),median_yield=float(g.yield_detrended.median()),years=';'.join(g.yield_year.astype(str))))
            if (idx+1)%500==0:print(f'{mode}: píxeles {idx+1:,}/{len(coords):,} | {time.perf_counter()-started:.0f} s',flush=True)
        table=pd.concat(paired,ignore_index=True)
        table.to_csv(destination/'paired_annual_counts_yield.csv.gz',index=False,compression='gzip')
        pd.DataFrame(summaries).to_csv(destination/'pixel_model_summary.csv',index=False)
        pd.DataFrame(coefficients).to_csv(destination/'phase_associations.csv',index=False)
        pd.DataFrame(combinations).to_csv(destination/'observed_combinations.csv',index=False)
        pid=args.pixel if args.pixel is not None else int(coords.pixel_id.iloc[0])
        if pid not in mapping:raise ValueError('--pixel is not in selected crop pixels')
        plot_pixel(table,pid,destination,mode)
    report=dict(pixels=len(coords),years=[1981,2016],modes=modes,elapsed_seconds=time.perf_counter()-started,yield_units=units,
        source=str(source),yield_source=str(yield_path),source_sha256=digest(source),
        yield_sha256=digest(yield_path),code_sha256=digest(Path(__file__)),
        rules={p:list(v)[0] for p,v in rule_sets.items()},
        interpretation='Per-pixel observational OLS with all variable phases simultaneously. Pearson is marginal. No p-values or causal/financial loss attribution.',
        caveats=['Detrended yield file lacks units and harvest-year convention metadata. No percentage or monetary loss conversion.',
        'Both year mappings are sensitivity scenarios, not alternatives chosen for best fit. Maturity end-year is a harvest proxy, not a verified GDHY year convention.',
        'Rank-deficient phase designs are not assigned separate coefficients. Constants have no estimated coefficient; collinearity warnings remain.',
        'Centered phase deviations sum to fitted yield minus fitted mean; they are model terms, not independent causal shares.',
        'Partial R2 values are unique conditional associations and do not sum to total R2. Shared explained variation is not allocated.',
        'Six-year held-out blocks by default; no validation leakage from fitting/scaling on held-out blocks. Original detrending may have used all years, so CV is exploratory.',
        'Zero counts are retained; incomplete climate and missing yield are excluded. No no-event reference is invented where none exists.',
        'Calendar/threshold approximations and spatial-mean units retained. MAT counts rain days, not heat episodes. FIL 32.7 source discrepancy remains.',
        '35–36 annual samples limit precision; no modeled phase interactions or causal identification. Global spatial dependence not assessed.'])
    (out/'completed.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    repo=root/'Repositorio/tesis-cereal-climate/outputs/agroclima_vigente/rendimiento/maize_seis_fases'/stamp
    if (root/'Repositorio/tesis-cereal-climate').is_dir():shutil.copytree(out,repo)
    print(f'Terminado. Resultados: {out}',flush=True)

if __name__=='__main__':main()
