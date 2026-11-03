"""Local descriptive ONI / ONI-MJO probabilities from verified daily native cache."""
import argparse
import gzip
import hashlib
import json
import shutil
import time
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from correlacion_oni_amenazas import read_oni
from fechas_ocurrencias_core import qualifying_runs

PHASES=['EST','VEG','REP','FLO','FIL','MAT']
STATES=['Cool','Neutral','Warm']
MJO=['Weak']+[str(i) for i in range(1,9)]

def affected_fraction(cells,min_days):
    """Area fraction of native cells in qualifying episodes, including all run days."""
    weights=np.cos(np.deg2rad([float(c['latitude']) for c in cells]))
    flags=[]
    for c in cells:
        valid=np.asarray(c['valid']).ravel().astype(bool)
        if not valid.all():return np.full(len(valid),np.nan)
        hit=np.asarray(c['hits']).ravel()
        flag=np.zeros(len(valid))
        for start,_,end in qualifying_runs(hit,valid,min_days):flag[start:end+1]=1
        flags.append(flag)
    return weights@np.asarray(flags)/weights.sum()

def summarize(d,states,min_days,min_years):
    """Within-pixel, agricultural-phase estimates with month-matched reference."""
    records=[]
    for (pid,phase),g in d.groupby(['pixel_id','phase']):
        reference=g.groupby('month').affected.mean()
        for key,s in g.groupby(states):
            key=key if isinstance(key,tuple) else (key,)
            baseline=float(s.month.map(reference).mean())
            p=float(s.affected.mean());n=len(s);years=s.season_year.nunique()
            records.append(dict(pixel_id=pid,phase=phase,**dict(zip(states,key)),
                n_valid_days=n,n_seasons=int(years),probability=p,
                month_matched_reference=baseline,difference_pp=100*(p-baseline),
                qualified_episodes_per_100_days=100*s.mean_occurrences_qualified.mean(),
                eligible=n>=min_days and years>=min_years))
    return pd.DataFrame(records)

def plot_tables(oni,joint,out):
    fig,axes=plt.subplots(1,4,figsize=(17,6),gridspec_kw={'width_ratios':[1.3,2.6,2.6,2.6]},layout='constrained')
    cmap=plt.get_cmap('YlOrRd').copy();cmap.set_bad('#d7d7d7')
    eligible_values=pd.concat([oni.loc[oni.eligible,'probability'],joint.loc[joint.eligible,'probability']])*100
    vmax=max(1,float(eligible_values.max())) if len(eligible_values) else 1
    panels=[(oni,STATES,'oni_state','ONI only')]+[(joint[joint.oni_state==s],MJO,'mjo_state',f'ONI: {s.lower()} | daily MJO') for s in STATES]
    for ax,(table,columns,col,title) in zip(axes,panels):
        valid=table[table.eligible]
        grid=valid.groupby(['phase',col]).probability.mean().unstack(col).reindex(index=PHASES,columns=columns)*100
        im=ax.imshow(grid.to_numpy(),vmin=0,vmax=vmax,cmap=cmap,aspect='auto')
        ax.set_xticks(range(len(columns)),columns,rotation=45 if col=='oni_state' else 0,fontsize=9)
        ax.set_yticks(range(6),PHASES,fontsize=10);ax.set_title(title,fontsize=11,pad=12)
        for r in range(6):
            for c in range(len(columns)):
                value=grid.iloc[r,c]
                if np.isfinite(value):ax.text(c,r,f'{value:.1f}',ha='center',va='center',fontsize=9,color='white' if value>.6*vmax else '#222222')
    fig.colorbar(im,ax=axes,shrink=.8,label='Mean within-pixel probability (%)')
    fig.suptitle('MAIZE PILOT | Climate-threshold exposure conditional on ONI and MJO',fontsize=14)
    fig.supxlabel('Daily ONI category uses the centered 3-month index; MJO is daily. Weak: amplitude ≤1.\n'
        'Equal pixel weighting among eligible estimates; samples may differ between cells. Gray: insufficient exposure.\n'
        'Descriptive historical probabilities, not forecasts or evidence of yield loss. EST–FIL: qualifying heat-episode days; MAT: precipitation-threshold days.',fontsize=9)
    for ext in ['png','pdf']:fig.savefig(out/f'conditional_probabilities.{ext}',dpi=220,facecolor='white')
    plt.close(fig)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=Path('C:/Users/paola/Tesis'))
    ap.add_argument('--daily-run',type=Path)
    ap.add_argument('--min-days',type=int,default=30)
    ap.add_argument('--min-years',type=int,default=3)
    args=ap.parse_args();root=args.root;started=time.perf_counter()
    if args.min_days<1 or args.min_years<1:ap.error('Los mínimos deben ser positivos')
    parent=root/'03_Resultados/Agroclima/vigente/correlaciones/maize_MJO_diario'
    runs=sorted([p.parent for p in parent.glob('*/provenance.json')],key=lambda p:p.stat().st_mtime)
    run=args.daily_run or (runs[-1] if runs else None)
    if run is None:raise FileNotFoundError('No hay ejecución diaria completa')
    meta=json.loads((run/'provenance.json').read_text(encoding='utf-8'))
    if meta['index_kind']!='RMM':raise ValueError('Se requiere RMM oficial')
    if meta['annual_count_verification']['mismatches']!=0:raise ValueError('Conteos diarios no verificados')
    d=pd.read_csv(run/'daily_occurrences_with_MJO.csv.gz',parse_dates=['date'])
    if d.duplicated(['pixel_id','season_year','phase','date']).any():raise ValueError('Días duplicados')
    cache=Path(meta['climate_cache']);pieces=[]
    print(f'CPU local: {d.pixel_id.nunique()} píxeles. Sin GEE ni descargas.',flush=True)
    for (pid,year),g in d.groupby(['pixel_id','season_year']):
        stem=f'{pid}_{year}';path=cache/f'{stem}.native.json.gz'
        marker=json.loads((cache/f'{stem}.json').read_text())
        if hashlib.sha256(path.read_bytes()).hexdigest()!=marker['hashes']['native']:raise ValueError(f'Caché alterada: {stem}')
        with gzip.open(path,'rt',encoding='utf-8') as f:rows=json.load(f)
        for phase,s in g.groupby('phase'):
            s=s.sort_values('date').copy();cells=[c for c in rows if c['phase']==phase]
            if not cells:raise ValueError('Faltan celdas nativas')
            required=1 if s.count_unit.iloc[0]=='days' else int(s.min_days.iloc[0])
            values=affected_fraction(cells,required)
            if len(values)!=len(s):raise ValueError('Longitud de fase incompatible')
            s['affected']=values;pieces.append(s)
    d=pd.concat(pieces,ignore_index=True)
    # Use official supplied phase and amplitude, not an independently rotated angle convention.
    rmm=pd.read_csv(meta['index'],sep=r'\s+',skiprows=2,header=None,usecols=range(7),
        names=['year','month','day','rmm1','rmm2','mjo_phase','amplitude'])
    rmm['date']=pd.to_datetime(rmm[['year','month','day']])
    if rmm.date.duplicated().any():raise ValueError('RMM duplicado')
    rmm.loc[(rmm[['rmm1','rmm2']].abs()>=100).any(axis=1)|(~rmm.mjo_phase.between(1,8))|(~rmm.amplitude.between(0,100)),['amplitude','mjo_phase']]=np.nan
    d=d.merge(rmm[['date','mjo_phase','amplitude']],on='date',how='left',validate='many_to_one')
    oni_path=root/'01_Data/ONI/ONI_v6_2026-10-08.html';oni,*_=read_oni(oni_path)
    month_values=pd.Series(oni.to_numpy(),index=pd.to_datetime(oni.index).to_period('M'))
    d['oni']=d.date.dt.to_period('M').map(month_values)
    d['oni_state']=np.select([d.oni<=-.5,d.oni>=.5],['Cool','Warm'],default='Neutral')
    d['mjo_state']=d.mjo_phase.astype('Int64').astype(str)
    d.loc[d.amplitude<=1,'mjo_state']='Weak';d['month']=d.date.dt.month
    valid=(d.quality=='OK')&d.affected.notna()&d.oni.notna()&d.amplitude.notna()
    excluded=int((~valid).sum());d=d[valid].copy()
    a=summarize(d,['oni_state'],args.min_days,args.min_years)
    b=summarize(d,['oni_state','mjo_state'],args.min_days,args.min_years)
    out=root/'03_Resultados/Agroclima/vigente/probabilidades/maize_ONI_MJO'/time.strftime('%Y%m%d_%H%M%S')
    out.mkdir(parents=True,exist_ok=False)
    a.to_csv(out/'probabilities_ONI_by_pixel_phase.csv',index=False)
    b.to_csv(out/'probabilities_ONI_MJO_by_pixel_phase.csv',index=False)
    d.to_csv(out/'daily_exposure_ONI_MJO.csv.gz',index=False,compression='gzip')
    d.groupby(['pixel_id','season_year','phase']).agg(valid_days=('affected','size'),affected_days_equivalent=('affected','sum'),qualified_episodes_mean_native_cell=('mean_occurrences_qualified','sum')).reset_index().to_csv(out/'annual_exposure_for_yield_alignment.csv',index=False)
    plot_tables(a,b,out)
    report=dict(source=str(run),pixels=int(d.pixel_id.nunique()),rows=len(d),excluded_rows=excluded,
        oni_sha256=hashlib.sha256(oni_path.read_bytes()).hexdigest(),rmm_sha256=meta['index_sha256'],
        elapsed_seconds=time.perf_counter()-started,min_days=args.min_days,min_years=args.min_years,
        estimand='Historical probability for a uniformly sampled valid phase day and area-weighted native cell to be in a qualifying climate episode. Full observed phase-clipped runs included; episodes counted separately on qualification day.',
        limitations=['Descriptive only; no uncertainty, significance, causal or forecasting claim. Daily observations and adjacent pixels are dependent.',
        'ONI categories are monthly centered-index bins, not official ENSO episode classifications. Centered ONI is not a real-time predictor.',
        'Probability estimates are raw; tables include a month-matched within-pixel reference and differences. Neither establishes a MJO effect independent of ENSO or seasonality.',
        'Minimum exposure thresholds are display safeguards, not proof of precision. Pilot pixels are not representative of global maize.',
        'Yield not joined: planting-season labels must be reconciled with harvest-year labels. Detrended yield is not exclusively climatic variation.',
        'Current source rules retained, including FIL 32.7 C and phase-boundary clipping; source/calendar uncertainties still apply.',
        'Official RMM metadata reports a methodological change in 2014; sensitivity assessment required before firm interpretation.'])
    (out/'provenance.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    repo=root/'Repositorio/tesis-cereal-climate'
    if repo.is_dir():shutil.copytree(out,repo/'outputs/agroclima_vigente/probabilidades/maize_ONI_MJO'/out.name)
    print(f'Terminado en {report["elapsed_seconds"]:.1f} s. Resultados: {out}',flush=True)

if __name__=='__main__':main()

