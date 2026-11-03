"""Pilot using cached daily temperatures only; no Earth Engine requests."""
import argparse
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from correlacion_oni_amenazas import read_oni

ROOT=Path('C:/Users/paola/Tesis')
CACHE=ROOT/'02_Procesados/Clima_ERA5_Land_cache/diario_UTC'
OUT=ROOT/'03_Resultados/Agroclima/vigente/diagnosticos/piloto_pearson'
BASE=ROOT/'03_Resultados/Agroclima/vigente/correlaciones/maize_ONI_v6'

def pearson(x,y):
    x=np.asarray(x,float);y=np.asarray(y,float)
    ok=np.isfinite(x)&np.isfinite(y);x=x[ok];y=y[ok]
    if len(x)<20 or np.std(x)<1e-12 or np.std(y)<1e-12:return np.nan,len(x)
    return float(np.corrcoef(x,y)[0,1]),len(x)

def episode_confirmation(hot):
    """One flag on second hot day of each run, including cross-month runs."""
    prev=hot.shift(1,fill_value=False);before=hot.shift(2,fill_value=False)
    return hot & prev & ~before

def anomaly(s):
    # Month/day climatology avoids leap-year shifts after February.
    a=s-s.groupby(s.index.strftime('%m-%d')).transform('mean')
    valid=a.notna();t=np.arange(len(a),dtype=float)
    if valid.sum()>2:
        fit=np.polyfit(t[valid],a[valid],1);a=a-np.polyval(fit,t)
    return a

def welch_pair(a,b,size=512):
    """Hann Welch PSD/coherence; reject incomplete segments, never bridge gaps."""
    xa=[];xb=[];w=np.hanning(size)
    for i in range(0,len(a)-size+1,size//2):
        x=np.asarray(a[i:i+size]);y=np.asarray(b[i:i+size])
        if not(np.isfinite(x).all() and np.isfinite(y).all()):continue
        xa.append(np.fft.rfft((x-x.mean())*w));xb.append(np.fft.rfft((y-y.mean())*w))
    if len(xa)<3:return None
    xa=np.array(xa);xb=np.array(xb)
    sx=(abs(xa)**2).mean(0);sy=(abs(xb)**2).mean(0)
    cross=(xa*np.conj(xb)).mean(0)
    coh=np.divide(abs(cross)**2,sx*sy,out=np.full_like(sx,np.nan),where=sx*sy>1e-20)
    return np.fft.rfftfreq(size),sx*2/(w*w).sum(),coh,len(xa)

def maps(table,key,panels,coords,name,title):
    fig,axes=plt.subplots((len(panels)+2)//3,3,figsize=(12,3*((len(panels)+2)//3)),squeeze=False)
    for ax,p in zip(axes.flat,panels):
        sub=coords.merge(table[table[key]==p],on='pixel_id',how='left')
        ax.scatter(sub.longitude,sub.latitude,c='#bbb',s=65)
        good=sub.r.notna()
        ax.scatter(sub.loc[good,'longitude'],sub.loc[good,'latitude'],c=sub.loc[good,'r'],vmin=-1,vmax=1,cmap='RdBu_r',s=45)
        ax.set(title=str(p),xlabel='Longitud',ylabel='Latitud',xlim=(-75,-57),ylim=(-42,-35));ax.grid(alpha=.2)
    for ax in list(axes.flat)[len(panels):]:ax.set_visible(False)
    fig.suptitle(title+'\nPiloto regional: diez píxeles con caché; gris = Pearson no definido',fontsize=12)
    fig.tight_layout(rect=(0,0.03,0.92,.93))
    fig.colorbar(plt.cm.ScalarMappable(norm=plt.Normalize(-1,1),cmap='RdBu_r'),ax=list(axes.flat),fraction=.02,label='Pearson r')
    fig.savefig(OUT/name,dpi=160);plt.close(fig)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reuse-daily',action='store_true',help='Reuse daily aggregates from this pilot, without rereading native cache files')
    args=parser.parse_args()
    started=time.perf_counter();OUT.mkdir(parents=True,exist_ok=True)
    coords=pd.read_csv(ROOT/'02_Procesados/Pixeles_correlacion_vigentes/pixeles_maize.csv').iloc[:10].copy()
    oni,*_=read_oni(ROOT/'01_Data/ONI/ONI_v6_2026-10-08.html')
    dates=pd.date_range('1981-01-01','2016-12-31');daily={};monthly=[];coverage=[]
    for pid in coords.pixel_id:
        if args.reuse_daily:
            series=pd.read_csv(OUT/f'diario_{pid}.csv',index_col='date',parse_dates=True).reindex(dates)
            if series.index.has_duplicates:raise ValueError('Duplicate daily dates')
            daily[int(pid)]=series
            count=series.episode_confirmation.resample('MS').sum(min_count=1)
            complete=series.episode_confirmation.resample('MS').count()==count.index.days_in_month
            count=count.where(complete)
            for month in range(1,13):
                s=count[count.index.month==month];r,n=pearson(oni.reindex(s.index),s)
                monthly.append(dict(pixel_id=pid,month=month,r=r,n_years=n))
            prior=json.loads((OUT/'procedencia_piloto.json').read_text(encoding='utf-8'))
            coverage.append(next(item for item in prior['coverage'] if item['pixel_id']==int(pid)))
            continue
        files=sorted(CACHE.glob(f'era5_UTC_{pid}_*.csv'))
        df=pd.concat([pd.read_csv(f,usecols=['date','x','y','latitude','tmax_c']) for f in files],ignore_index=True)
        df['date']=pd.to_datetime(df.date);df=df[df.date.between(dates[0],dates[-1])]
        if df.duplicated(['date','x','y']).any():raise ValueError(f'Duplicate native cell/day: {pid}')
        temp=df.pivot(index='date',columns=['x','y'],values='tmax_c').reindex(dates)
        lat=df.drop_duplicates(['x','y']).set_index(['x','y']).latitude.reindex(temp.columns)
        weights=np.cos(np.deg2rad(lat.to_numpy()));weights/=weights.sum()
        hot=temp>=34;valid=temp.notna().all(axis=1)
        confirmed=episode_confirmation(hot)
        # Exclude confirmation day if preceding two days are unavailable.
        event_valid=valid & valid.shift(1,fill_value=False) & valid.shift(2,fill_value=False)
        series=pd.DataFrame({'tmax_mean':temp.to_numpy()@weights,
            'hot_fraction':hot.to_numpy()@weights,
            'episode_confirmation':confirmed.to_numpy()@weights},index=dates)
        series.loc[~valid,['tmax_mean','hot_fraction']]=np.nan
        series.loc[~event_valid,'episode_confirmation']=np.nan
        series.to_csv(OUT/f'diario_{pid}.csv',index_label='date');daily[int(pid)]=series
        count=series.episode_confirmation.resample('MS').sum(min_count=1)
        complete=series.episode_confirmation.resample('MS').count()==count.index.days_in_month
        count=count.where(complete)
        for month in range(1,13):
            s=count[count.index.month==month];r,n=pearson(oni.reindex(s.index),s)
            monthly.append(dict(pixel_id=pid,month=month,r=r,n_years=n))
        coverage.append(dict(pixel_id=int(pid),native_cells=len(temp.columns),valid_days=int(valid.sum()),total_days=len(dates)))
        print(f'Piloto: píxel {pid}, {valid.sum()}/{len(dates)} días completos; {time.perf_counter()-started:.1f} s',flush=True)
    monthly=pd.DataFrame(monthly);monthly.to_csv(OUT/'pearson_mensual_calor34.csv',index=False)
    maps(monthly,'month',list(range(1,13)),coords,'mapas_mensuales_pearson.png','ONI del mes vs episodios de Tmax ≥34 °C, ≥2 días')
    phase=[]
    for chunk in pd.read_csv(BASE/'pares_oni_amenaza.csv.gz',chunksize=100000):
        chunk=chunk[chunk.pixel_id.isin(coords.pixel_id)]
        if not chunk.empty:phase.append(chunk)
    phase=pd.concat(phase);phase=phase[phase.quality=='OK']
    rows=[]
    for (pid,p),sub in phase.groupby(['pixel_id','phase']):
        r,n=pearson(sub.oni_phase,sub.mean_count_per_native_cell)
        rows.append(dict(pixel_id=pid,phase=p,r=r,n_years=n))
    phase=pd.DataFrame(rows);phase.to_csv(OUT/'pearson_fenologico.csv',index=False)
    maps(phase,'phase',['EST','VEG','REP','FLO','FIL','MAT'],coords,'mapas_fenologicos_pearson.png','ONI de la ventana vs amenaza de cada fase')
    romi=pd.read_csv(ROOT/'01_Data/RMM/romi.cpcolr.1x-RMM.txt',sep=r'\s+',header=None,names=['year','month','day','flag','pc1','pc2','amplitude'])
    romi.index=pd.to_datetime(romi[['year','month','day']]);romi=romi[['pc1','pc2']].where(romi[['pc1','pc2']].abs()<20)
    spectra=[];contrasts=[]
    selected=[int(coords.pixel_id.iloc[i]) for i in [0,4,9]]
    fig,axes=plt.subplots(3,2,figsize=(12,10))
    for row,pid in enumerate(selected):
        d=daily[pid]
        # Keep calendar gaps: an index intersection could silently concatenate missing dates.
        idx=pd.date_range(max(d.index.min(),romi.index.min()),min(d.index.max(),romi.index.max()))
        signal=anomaly(d.hot_fraction).reindex(idx)
        for pc in ['pc1','pc2']:
            b=anomaly(romi[pc].reindex(idx));result=welch_pair(signal.to_numpy(),b.to_numpy())
            for lag in [0,7,14,21,28]:
                # Index from lag days earlier; positive lag means MJO precedes threat.
                r,n=pearson(b.shift(lag),signal)
                contrasts.append(dict(pixel_id=pid,index='ROMI',component=pc,lead_days=lag,r=r,n_days=n))
            if result is None:continue
            freq,power,coh,nseg=result;keep=freq>0;period=1/freq[keep]
            if pc=='pc1':axes[row,0].loglog(period,power[keep],label='Fracción diaria con Tmax ≥34 °C')
            axes[row,1].semilogx(period,coh[keep],label=f'ROMI {pc}; {nseg} segmentos')
            for f,p,c in zip(freq[keep],power[keep],coh[keep]):spectra.append(dict(pixel_id=pid,component=pc,period_days=1/f,power=p,coherence=c,segments=nseg))
        for ax in axes[row]:
            ax.axvspan(30,96,color='orange',alpha=.15);ax.set_xlim(2,512);ax.set_xlabel('Período (días)');ax.set_title(f'Píxel {pid}');ax.legend(fontsize=8);ax.grid(alpha=.2)
        axes[row,0].set_ylabel('Densidad espectral');axes[row,1].set_ylabel('Coherencia exploratoria');axes[row,1].set_ylim(0,1)
    fig.suptitle('Piloto diario: anomalías sin ciclo anual ni tendencia; banda 30–96 días\nWelch 512 días, 50% solapamiento. No es una prueba de significancia ni atribución a MJO.')
    fig.tight_layout(rect=(0,0,1,.94));fig.savefig(OUT/'espectro_y_coherencia_ROMI.png',dpi=160);plt.close(fig)
    pd.DataFrame(spectra).to_csv(OUT/'espectros_coherencia.csv',index=False)
    pd.DataFrame(contrasts).to_csv(OUT/'pearson_diario_ROMI.csv',index=False)
    report=dict(elapsed_seconds=time.perf_counter()-started,reused_daily=args.reuse_daily,coverage=coverage,spectral_pixels=selected,
        monthly_rule='Fixed exploratory heat rule Tmax >=34C >=2 consecutive days, all calendar months; count at second day; not a crop phase-specific rule.',
        phase_rules='Existing six phase outputs unchanged; MAT rain >10mm/day. Existing phase-window and FIL threshold caveats retained.',
        index='Local ROMI, not RMM; actual date intersection, normally 1991–2016.',
        limits=['Ten cached pixels in southern South America, not globally representative; selection independent of correlation.',
        'Daily indicator is area fraction of hot native cells, not number of events or loss.',
        'Monthly maps use 36 annual values per calendar month, not pooling 432 months.',
        'Pearson only; no p-values, permutations or significance claims; daily autocorrelation prevents naive independent-day inference.',
        'Full-period climatology/trend removal is exploratory, not out-of-sample prediction; ONI centered and ROMI processing can include future information.',
        'No yield or insurance validation; no missing-day interpolation; spectrum rejects incomplete 512-day segments.'])
    if args.reuse_daily:report['initial_full_run_seconds']=prior.get('initial_full_run_seconds',prior['elapsed_seconds'])
    (OUT/'procedencia_piloto.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(f'Terminado: {report["elapsed_seconds"]:.1f} segundos. {OUT}',flush=True)

if __name__=='__main__':main()
