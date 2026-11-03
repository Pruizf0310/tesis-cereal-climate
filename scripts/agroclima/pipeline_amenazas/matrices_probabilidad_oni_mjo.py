"""Saved ONI–MJO probabilities: exposure, matched changes and support. No GEE."""
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
from matplotlib.colors import BoundaryNorm,ListedColormap

STATES=['Cool','Neutral','Warm']
MJO=['Weak']+[str(i) for i in range(1,9)]

def build(table):
    rows=[]
    for state in STATES:
        for mjo in MJO:
            s=table[(table.oni_state==state)&(table.mjo_state==mjo)]
            v=s[s.eligible.eq(True)]
            rows.append(dict(oni_state=state,mjo_state=mjo,eligible_pixels=int(v.pixel_id.nunique()),
                probability_percent=float(100*v.probability.median()) if len(v) else np.nan,
                reference_percent=float(100*v.month_ONI_matched_reference.median()) if len(v) else np.nan,
                difference_pp=float(v.MJO_difference_pp.median()) if len(v) else np.nan,
                median_days=float(v.n_valid_days.median()) if len(v) else np.nan,
                median_seasons=float(v.n_seasons.median()) if len(v) else np.nan))
    return pd.DataFrame(rows)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=Path('C:/Users/paola/Tesis'))
    ap.add_argument('--source',type=Path)
    ap.add_argument('--phase',choices=['EST','VEG','REP','FLO','FIL','MAT'],default='EST')
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--pixel',type=int)
    g.add_argument('--bbox',nargs=4,type=float,metavar=('WEST','SOUTH','EAST','NORTH'))
    ap.add_argument('--name',help='English region label')
    args=ap.parse_args()
    parent=args.root/'03_Resultados/Agroclima/vigente/probabilidades'/f'maize_{args.phase}_global_1981_2016'
    runs=sorted(parent.glob('*/completed.json'),key=lambda p:p.stat().st_mtime)
    source=args.source or (runs[-1].parent if runs else None)
    if source is None or not (source/'completed.json').is_file():raise FileNotFoundError('No complete source run')
    d=pd.read_csv(source/'probabilities_ONI_MJO.csv',dtype={'mjo_state':str})
    if not d.phase.eq(args.phase).all():raise ValueError('Source phase differs from --phase')
    if d.duplicated(['pixel_id','oni_state','mjo_state']).any():raise ValueError('Duplicate conditional estimates')
    if args.pixel is not None:
        d=d[d.pixel_id==args.pixel].copy();label=args.name or f'Pixel {args.pixel}'
    else:
        w,s,e,n=args.bbox
        if not -180<=w<e<=180 or not -90<=s<n<=90:ap.error('Invalid bounding box')
        d=d[d.longitude.between(w,e)&d.latitude.between(s,n)].copy()
        label=args.name or f'Region ({w:g}, {s:g}, {e:g}, {n:g})'
    if d.empty:raise ValueError('No joint probabilities in selection')
    if not d.probability.between(-1e-12,1+1e-12).all():raise ValueError('Invalid probability')
    d['probability']=d.probability.clip(0,1)
    summary=build(d)
    if summary.eligible_pixels.sum()==0:raise ValueError('No combination has enough exposure; inspect selected_pixel_values.csv in original data or choose another region. Missing does not mean zero.')
    grids={col:summary.pivot(index='mjo_state',columns='oni_state',values=col).reindex(index=MJO,columns=STATES) for col in ['probability_percent','difference_pp','eligible_pixels','median_days','median_seasons']}
    colors=ListedColormap(['#fff7bc','#fee391','#fec44f','#fe9929','#ec7014','#cc4c02','#8c2d04'])
    colors.set_bad('#d7d7d7');bounds=[0,1,5,10,20,40,60,100]
    delta=plt.get_cmap('RdBu_r').copy();delta.set_bad('#d7d7d7')
    max_delta=max(1,float(np.nanmax(np.abs(grids['difference_pp'].to_numpy()))))
    fig,axes=plt.subplots(1,3,figsize=(14,8.5),layout='constrained')
    configs=[('probability_percent','Conditional probability (%)',colors,BoundaryNorm(bounds,colors.N)),
        ('difference_pp','Change vs month + ONI reference (pp)',delta,plt.Normalize(-max_delta,max_delta))]
    for ax,(col,title,cmap,norm) in zip(axes,configs):
        values=grids[col].to_numpy();im=ax.imshow(values,cmap=cmap,norm=norm,aspect='auto')
        for r in range(9):
            for c in range(3):
                v=values[r,c]
                if not np.isfinite(v):text='—';textcolor='#555555'
                else:
                    text=f'{v:.1f}%' if col=='probability_percent' else f'{v:+.1f}'
                    rgba=cmap(norm(v));textcolor='white' if .2126*rgba[0]+.7152*rgba[1]+.0722*rgba[2]<.5 else '#222222'
                ax.text(c,r,text,ha='center',va='center',fontsize=11,color=textcolor)
        ax.set_title(title,fontsize=11,pad=14)
        fig.colorbar(im,ax=ax,orientation='horizontal',shrink=.9,pad=.07,ticks=bounds if col=='probability_percent' else None)
    ax=axes[2];ax.set_title('Support for each estimate',fontsize=11,pad=14)
    support=grids['eligible_pixels'].to_numpy();ax.imshow(np.where(support>0,0,np.nan),cmap=ListedColormap(['#f3f5f7']),vmin=0,vmax=1,aspect='auto')
    for r in range(9):
        for c in range(3):
            n=int(support[r,c]);days=grids['median_days'].iloc[r,c];years=grids['median_seasons'].iloc[r,c]
            text=f'{n:,} px\n{days:.0f} d / {years:.0f} y' if n else 'No estimate'
            ax.text(c,r,text,ha='center',va='center',fontsize=10,color='#222222')
    for ax in axes:
        ax.set_xticks(range(3),['ONI cool','ONI neutral','ONI warm'],fontsize=10)
        ax.set_yticks(range(9),['Weak']+[f'MJO {i}' for i in range(1,9)],fontsize=10)
        ax.set_xticks(np.arange(-.5,3,1),minor=True);ax.set_yticks(np.arange(-.5,9,1),minor=True)
        ax.grid(which='minor',color='white',linewidth=2);ax.tick_params(which='minor',length=0)
        for spine in ax.spines.values():spine.set_visible(False)
    plan=json.loads((source/'plan.json').read_text(encoding='utf-8'));rule=plan['identity']['rule']
    fig.suptitle(f'MAIZE | {args.phase} | {label} | 1981–2016\n{rule["variable"]} {rule["operator"]} {rule["threshold"]}; minimum duration {rule["min_days"]} days',fontsize=14)
    regional='Regional cells: equal-pixel medians; pixel composition can differ between combinations. Support: eligible pixels and median days / seasons.\n' if args.pixel is None else 'Support: valid exposure days / seasons. Missing estimates do not mean zero probability.\n'
    fig.supxlabel(regional+'Changes are computed within pixels against a reference matched to month and ONI before regional aggregation.\n'
        'Historical daily exposure probabilities; not probability of ≥1 event per season, causal effects or forecasts. No uncertainty estimated.',fontsize=9)
    out=source/'probability_matrices'/time.strftime('%Y%m%d_%H%M%S');out.mkdir(parents=True,exist_ok=False)
    for ext in ['png','pdf']:fig.savefig(out/f'ONI_MJO_probability_matrices.{ext}',dpi=220,facecolor='white')
    plt.close(fig);summary.to_csv(out/'matrix_values.csv',index=False)
    d.to_csv(out/'selected_pixel_values.csv',index=False)
    (out/'provenance.json').write_text(json.dumps(dict(source=str(source),pixel=args.pixel,bbox=args.bbox,label=label,
        summary='Within-pixel probabilities; regional equal-pixel medians among eligible cells. Spatial composition may differ. No inference or smoothing.'),indent=2),encoding='utf-8')
    repo=args.root/'Repositorio/tesis-cereal-climate/outputs/agroclima_vigente/probabilidades'/source.parent.name/source.name/'probability_matrices'/out.name
    repo.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(out,repo)
    print(f'Sin GEE. PNG, PDF y valores: {out}',flush=True)

if __name__=='__main__':main()
