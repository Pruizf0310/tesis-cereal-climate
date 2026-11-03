"""Plot saved conditional probabilities for a pixel or geographic region. No GEE."""
import argparse
import json
import shutil
import time
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

STATES=['Cool','Neutral','Warm']
MJO=['Weak']+[str(i) for i in range(1,9)]

def profiles(table):
    rows=[]
    for state in STATES:
        for mjo in MJO:
            s=table[(table.oni_state==state)&(table.mjo_state==mjo)]
            valid=s[s.eligible.eq(True)]
            record=dict(oni_state=state,mjo_state=mjo,pixels_with_data=s.pixel_id.nunique(),
                eligible_pixels=valid.pixel_id.nunique(),total_valid_days=int(valid.n_valid_days.sum()))
            for col in ['probability','month_ONI_matched_reference','MJO_difference_pp']:
                values=valid[col].dropna()
                for q,label in [(.25,'q25'),(.5,'median'),(.75,'q75')]:
                    record[f'{col}_{label}']=float(values.quantile(q)) if len(values) else np.nan
            record['median_days_per_pixel']=float(valid.n_valid_days.median()) if len(valid) else np.nan
            record['median_seasons_per_pixel']=float(valid.n_seasons.median()) if len(valid) else np.nan
            rows.append(record)
    return pd.DataFrame(rows)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=Path('C:/Users/paola/Tesis'))
    ap.add_argument('--source',type=Path,help='Folder containing completed.json and probabilities_ONI_MJO.csv')
    ap.add_argument('--phase',default='EST',choices=['EST','VEG','REP','FLO','FIL','MAT'])
    group=ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--pixel',type=int)
    group.add_argument('--bbox',nargs=4,type=float,metavar=('WEST','SOUTH','EAST','NORTH'))
    ap.add_argument('--name',default=None,help='Region name in English for figure title')
    args=ap.parse_args();root=args.root
    if args.bbox:
        w,s,e,n=args.bbox
        if not -180<=w<e<=180 or not -90<=s<n<=90:ap.error('Bounding box must have west < east and south < north')
    parent=root/'03_Resultados/Agroclima/vigente/probabilidades'/f'maize_{args.phase}_global_1981_2016'
    completed=sorted(parent.glob('*/completed.json'),key=lambda p:p.stat().st_mtime)
    source=args.source or (completed[-1].parent if completed else None)
    if source is None or not (source/'completed.json').exists():raise FileNotFoundError('No complete global run found')
    print('Solo lectura local y gráficos. Sin GEE, descargas ni recálculo climático.',flush=True)
    d=pd.read_csv(source/'probabilities_ONI_MJO.csv',dtype={'mjo_state':str})
    if args.pixel is not None:
        d=d[d.pixel_id==args.pixel].copy();label=args.name or f'Pixel {args.pixel}'
    else:
        d=d[d.longitude.between(w,e)&d.latitude.between(s,n)].copy()
        label=args.name or f'Region [{w:g}, {s:g}, {e:g}, {n:g}]'
    if d.empty:raise ValueError('No pixels with joint data in the requested selection')
    if d.duplicated(['pixel_id','oni_state','mjo_state']).any():raise ValueError('Duplicate conditional estimates')
    if not d.phase.eq(args.phase).all():raise ValueError('Source phase does not match --phase')
    if not d.probability.between(-1e-12,1+1e-12).all():raise ValueError('Probability out of bounds')
    d['probability']=d.probability.clip(0,1)
    result=profiles(d)
    out=source/'visual_profiles'/time.strftime('%Y%m%d_%H%M%S');out.mkdir(parents=True,exist_ok=False)
    result.to_csv(out/'profile_values_and_coverage.csv',index=False)
    d.to_csv(out/'selected_pixel_probabilities.csv',index=False)
    fig,axes=plt.subplots(3,3,figsize=(16,11),sharex=True,layout='constrained')
    palette=['#2463a6','#545454','#bd3b2d'];x=np.arange(9)
    max_p=max(1,100*result.probability_q75.max()) if result.probability_q75.notna().any() else 1
    max_p=max(max_p,100*result.month_ONI_matched_reference_median.max()) if result.month_ONI_matched_reference_median.notna().any() else max_p
    max_delta=max(1,float(result[['MJO_difference_pp_q25','MJO_difference_pp_q75']].abs().max().max()))
    for col,(state,color) in enumerate(zip(STATES,palette)):
        s=result[result.oni_state==state].set_index('mjo_state').reindex(MJO)
        prob=s.probability_median.to_numpy()*100;ref=s.month_ONI_matched_reference_median.to_numpy()*100
        ax=axes[0,col]
        ax.plot(x,prob,'o-',color=color,lw=1.7,label='Conditional probability')
        ax.plot(x,ref,'s--',color='#303030',lw=1.2,markersize=4,label='Month + ONI matched reference')
        if args.pixel is None:ax.fill_between(x,100*s.probability_q25.to_numpy(),100*s.probability_q75.to_numpy(),color=color,alpha=.16)
        ax.set_title(f'ONI {state.lower()}',fontsize=13);ax.set_ylim(0,min(100,max_p*1.15))
        if col==0:ax.set_ylabel('Daily exposure probability (%)')
        ax.legend(fontsize=8,loc='upper left')
        ax=axes[1,col];delta=s.MJO_difference_pp_median.to_numpy()
        ax.axhline(0,color='#444444',lw=1)
        ax.plot(x,delta,'o-',color=color,lw=1.7)
        if args.pixel is None:ax.fill_between(x,s.MJO_difference_pp_q25.to_numpy(),s.MJO_difference_pp_q75.to_numpy(),color=color,alpha=.16)
        ax.set_ylim(-max_delta*1.2,max_delta*1.2)
        if col==0:ax.set_ylabel('Change vs matched reference\n(percentage points)')
        ax=axes[2,col]
        heights=s.median_days_per_pixel.fillna(0).to_numpy()
        ax.bar(x,heights,color=color,alpha=.7)
        for i,row in enumerate(s.itertuples()):
            text=f'n={int(row.eligible_pixels)}' if args.pixel is None else (f'{int(row.median_seasons_per_pixel)}y' if np.isfinite(row.median_seasons_per_pixel) else 'no data')
            ax.annotate(text,(i,heights[i]),xytext=(0,4),textcoords='offset points',ha='center',fontsize=8,rotation=45 if args.pixel is None else 0)
        ax.margins(y=.35);ax.set_xticks(x,MJO,fontsize=10);ax.set_xlabel('Daily MJO state (Weak; active phases 1–8)')
        if col==0:ax.set_ylabel('Valid exposure days\n(median per eligible pixel)')
        for row in range(3):
            a=axes[row,col];a.grid(axis='y',alpha=.18);a.spines[['top','right']].set_visible(False)
            a.axvline(.5,color='#aaaaaa',lw=.8,ls=':')
    scope=f'{d.pixel_id.nunique():,} selected pixels'
    fig.suptitle(f'MAIZE | {args.phase} | {label} | 1981–2016\nMJO conditional probabilities within monthly centered ONI categories · {scope}',fontsize=14)
    foot='Descriptive historical associations, not forecast skill or significance. Lines connect categories; they are not smooth probability densities.'
    if args.pixel is None:
        foot+='\nPoints: median of eligible pixel estimates. Shading: spatial interquartile range, NOT a confidence interval. Pixel composition can vary by MJO state.'
        foot+='\nChanges are computed within each pixel before taking the regional median; they need not equal the difference between the two median curves.'
    else:foot+='\nNo confidence intervals estimated. Missing points: insufficient exposure, not zero probability.'
    fig.supxlabel(foot,fontsize=9)
    for ext in ['png','pdf']:fig.savefig(out/f'MJO_probability_profiles.{ext}',dpi=200,facecolor='white')
    plt.close(fig)
    (out/'provenance.json').write_text(json.dumps(dict(source=str(source),pixel=args.pixel,bbox=args.bbox,name=label,
        selected_pixels=int(d.pixel_id.nunique()),regional_summary='Equal-pixel median and spatial IQR; eligible composition varies. Descriptive only.',
        reference='Within-pixel, phase-specific baseline matched to month and ONI category using exposure weights of each MJO state.'),indent=2),encoding='utf-8')
    repo=root/'Repositorio/tesis-cereal-climate/outputs/agroclima_vigente/probabilidades'/source.parent.name/source.name/'visual_profiles'/out.name
    repo.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(out,repo)
    print(f'Gráfica, valores y cobertura: {out}',flush=True)

if __name__=='__main__':main()
