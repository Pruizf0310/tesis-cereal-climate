"""Three empirical probability profiles: ONI cool, neutral and warm. No GEE."""
import argparse
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from graficar_perfiles_mjo import profiles,STATES,MJO

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=Path('C:/Users/paola/Tesis'))
    ap.add_argument('--phase',default='EST',choices=['EST','VEG','REP','FLO','FIL','MAT'])
    ap.add_argument('--source',type=Path)
    scope=ap.add_mutually_exclusive_group(required=True)
    scope.add_argument('--bbox',nargs=4,type=float,metavar=('WEST','SOUTH','EAST','NORTH'))
    scope.add_argument('--pixel',type=int)
    ap.add_argument('--name')
    args=ap.parse_args()
    parent=args.root/'03_Resultados/Agroclima/vigente/probabilidades'/f'maize_{args.phase}_global_1981_2016'
    runs=sorted(parent.glob('*/completed.json'),key=lambda p:p.stat().st_mtime)
    source=args.source or (runs[-1].parent if runs else None)
    if source is None or not (source/'completed.json').exists():raise FileNotFoundError('No completed source run')
    d=pd.read_csv(source/'probabilities_ONI_MJO.csv',dtype={'mjo_state':str})
    if not d.phase.eq(args.phase).all():raise ValueError('Wrong source phase')
    if args.bbox:
        w,s,e,n=args.bbox
        if not -180<=w<e<=180 or not -90<=s<n<=90:ap.error('Invalid bounding box')
        d=d[d.longitude.between(w,e)&d.latitude.between(s,n)].copy()
        label=args.name or f'Region ({w:g}, {s:g}, {e:g}, {n:g})'
    else:
        d=d[d.pixel_id==args.pixel].copy();label=args.name or f'Pixel {args.pixel}'
    if d.empty:raise ValueError('No joint data in selection')
    if d.duplicated(['pixel_id','oni_state','mjo_state']).any():raise ValueError('Duplicate estimates')
    # Same pixels for all three ONI curves at each MJO state: avoid confusing ONI contrasts with geographic composition.
    matched=[];coverage=[]
    for mjo in MJO:
        state=d[(d.mjo_state==mjo)&d.eligible.eq(True)]
        counts=state.groupby('pixel_id').oni_state.nunique()
        ids=counts[counts==3].index
        matched.append(state[state.pixel_id.isin(ids)])
        coverage.append(dict(mjo_state=mjo,matched_pixels=len(ids)))
    selected=pd.concat(matched,ignore_index=True)
    if selected.empty:raise ValueError('No MJO state has sufficient exposure in all three ONI categories. Choose a larger region; do not treat missing estimates as zeros.')
    result=profiles(selected)
    fig,(ax,coverage_ax)=plt.subplots(2,1,figsize=(12,7),sharex=True,gridspec_kw={'height_ratios':[4,1]},layout='constrained')
    colors={'Cool':'#2463a6','Neutral':'#555555','Warm':'#c53a32'}
    for state in STATES:
        s=result[result.oni_state==state].set_index('mjo_state').reindex(MJO)
        y=100*s.probability_median.to_numpy()
        # Weak MJO is a separate category, not phase zero; no line joins it to phase 1.
        ax.plot(np.arange(1,9),y[1:],'o-',color=colors[state],lw=2,markersize=5,label=f'ONI {state.lower()}')
        if np.isfinite(y[0]):ax.scatter([0],[y[0]],color=colors[state],s=45,marker='s')
    ax.set_ylabel('Historical daily exposure probability (%)',fontsize=11)
    ax.set_ylim(bottom=0);ax.grid(axis='y',alpha=.2);ax.legend(frameon=False,ncol=3)
    ax.set_title(f'MAIZE | {args.phase} | {label} | 1981–2016\nProbability conditional on daily MJO state and monthly centered ONI',fontsize=13,pad=15)
    count=np.array([r['matched_pixels'] for r in coverage]);coverage_ax.bar(range(9),count,color='#adb9c4')
    for i,value in enumerate(count):coverage_ax.annotate(str(value),(i,value),xytext=(0,3),textcoords='offset points',ha='center',fontsize=9)
    coverage_ax.set_ylabel('Matched\npixels');coverage_ax.margins(y=.3)
    coverage_ax.set_xticks(range(9),['Weak']+[str(i) for i in range(1,9)])
    coverage_ax.set_xlabel('MJO state: weak (amplitude ≤1); active phases 1–8 (amplitude >1)')
    for a in [ax,coverage_ax]:
        a.spines[['top','right']].set_visible(False);a.axvline(.5,color='#999999',lw=.8,ls=':')
    fig.supxlabel('Regional curves: equal-pixel medians; the same eligible pixels are used across ONI categories at each MJO state.\n'
        'Pixel composition can change between MJO states. Lines connect categories; phase 8 cycles back to phase 1.\n'
        'Raw descriptive probabilities, not seasonally adjusted effects, forecasts, confidence intervals or evidence of yield loss.',fontsize=9)
    out=source/'probability_curves'/time.strftime('%Y%m%d_%H%M%S');out.mkdir(parents=True,exist_ok=False)
    for ext in ['png','pdf']:fig.savefig(out/f'MJO_probability_curves.{ext}',dpi=220,facecolor='white')
    plt.close(fig)
    result.to_csv(out/'curve_values.csv',index=False);pd.DataFrame(coverage).to_csv(out/'matched_coverage.csv',index=False)
    (out/'provenance.json').write_text(json.dumps(dict(source=str(source),bbox=args.bbox,pixel=args.pixel,
        summary='Median among pixels eligible in all three ONI categories within each MJO state. Geographic composition may vary between states.'),indent=2),encoding='utf-8')
    import shutil
    repo=args.root/'Repositorio/tesis-cereal-climate/outputs/agroclima_vigente/probabilidades'/source.parent.name/source.name/'probability_curves'/out.name
    repo.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(out,repo)
    print(f'Sin GEE. Curvas PNG/PDF y valores guardados en: {out}',flush=True)

if __name__=='__main__':main()
