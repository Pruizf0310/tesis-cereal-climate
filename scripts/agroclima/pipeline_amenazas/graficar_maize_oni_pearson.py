"""Plot existing Pearson results only: no climate downloads or correlation recalculation."""
import argparse
import hashlib
import json
import shutil
import time
import uuid
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from resumen_amenazas_maize import boundaries

PHASES=['EST','VEG','REP','FLO','FIL','MAT']
NAMES=['Establishment','Vegetative growth','Reproductive development','Flowering','Grain filling','Maturation']

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=Path('C:/Users/paola/Tesis'))
    ap.add_argument('--run',type=Path,help='Completed Pearson run folder; defaults to latest completed run')
    args=ap.parse_args();root=args.root
    parent=root/'03_Resultados/Agroclima/vigente/correlaciones/maize_ONI_Pearson'
    run=args.run or Path(json.loads((parent/'ultima_ejecucion.json').read_text(encoding='utf-8'))['output'])
    if not (run/'provenance.json').is_file():raise ValueError('The selected run is not complete')
    source=run/'pearson_by_pixel_phase.csv';df=pd.read_csv(source)
    if df.duplicated(['phase','pixel_id']).any():raise ValueError('Duplicate pixel/phase results')
    if set(df.phase)!=set(PHASES):raise ValueError('Missing or unknown phase')
    coords=df[df.phase=='EST'][['pixel_id','latitude','longitude']].reset_index(drop=True)
    r=np.rint((coords.latitude.to_numpy()+89.75)/.5).astype(int)
    c=np.rint((coords.longitude.to_numpy()+179.75)/.5).astype(int)
    outline=boundaries(root/'Repositorio/tesis-cereal-climate/web-v2/public/data/world_outline.geojson')
    fig=plt.figure(figsize=(18,13.5),facecolor='white')
    gs=fig.add_gridspec(4,2,height_ratios=[1,1,1,.045],left=.015,right=.985,top=.935,bottom=.085,hspace=.075,wspace=.025)
    # Discrete, explicitly labeled intervals improve contrast without changing r.
    bounds=[-1,-.6,-.4,-.2,-.1,.1,.2,.4,.6,1]
    cmap=ListedColormap(['#08306b','#08519c','#2171b5','#6baed6','#fffdf7','#fdae6b','#f16913','#d7301f','#7f0000'])
    cmap.set_bad((0,0,0,0));norm=BoundaryNorm(bounds,cmap.N)
    summary=[]
    for p,(phase,name) in enumerate(zip(PHASES,NAMES)):
        sub=df[df.phase==phase].set_index('pixel_id').reindex(coords.pixel_id)
        if sub.phase.isna().any():raise ValueError('Different pixel selection between phases')
        good=(sub.status=='OK')&np.isfinite(sub.pearson_r)
        if (sub.loc[good,'pearson_r'].abs()>1.00000001).any():raise ValueError('Invalid coefficient')
        rules=sub[['variable','operator','threshold','min_days','count_unit']].drop_duplicates()
        if len(rules)!=1:raise ValueError(f'Mixed rules: {phase}')
        rule=rules.iloc[0];symbol={'>=':'≥','>':'>','<=':'≤','<':'<'}.get(rule.operator,rule.operator)
        if rule.variable=='tmax_c':
            label=f'Daily Tmax {symbol}{rule.threshold:g} °C · ≥{int(rule.min_days)} consecutive days'
        elif rule.variable=='precip_mm':label=f'Daily precipitation {symbol}{rule.threshold:g} mm · daily occurrences'
        else:raise ValueError(f'Unknown variable {rule.variable}')
        panel=gs[p//2,p%2].subgridspec(2,1,height_ratios=[.10,1],hspace=.005)
        header=fig.add_subplot(panel[0]);header.set_axis_off()
        header.text(0,.96,f'{phase} · {name}',fontsize=10,fontweight='bold',ha='left',va='top',color='#263746')
        header.text(0,.02,label,fontsize=7.5,ha='left',va='bottom',color='#52616e')
        ax=fig.add_subplot(panel[1]);ax.set_facecolor('#f5f7f8')
        gray=np.full((360,720),np.nan);gray[r[~good],c[~good]]=1
        grid=np.full((360,720),np.nan);grid[r[good],c[good]]=sub.loc[good,'pearson_r'].to_numpy()
        ax.pcolormesh(np.arange(-180,180.5,.5),np.arange(-90,90.5,.5),gray,cmap=ListedColormap(['#c5c9cd']),rasterized=True)
        mesh=ax.pcolormesh(np.arange(-180,180.5,.5),np.arange(-90,90.5,.5),grid,cmap=cmap,norm=norm,rasterized=True)
        if outline:ax.add_collection(LineCollection(outline,colors='#bdc6cd',linewidths=.35))
        ax.set(xlim=(-180,180),ylim=(-58,82));ax.set_aspect('equal',adjustable='box');ax.set_xticks([]);ax.set_yticks([])
        for spine in ax.spines.values():spine.set_visible(False)
        summary.append(dict(phase=phase,valid_pearson=int(good.sum()),undefined=int((~good).sum()),
            min_valid_years=int(sub.loc[good,'n_valid_years'].min()),max_valid_years=int(sub.loc[good,'n_valid_years'].max())))
    cb=fig.colorbar(mesh,cax=fig.add_subplot(gs[3,:]),orientation='horizontal',ticks=bounds,spacing='uniform')
    cb.set_label('Pearson r · blue: negative association | cream: −0.1 to +0.1 | orange/red: positive association',fontsize=8,labelpad=5)
    cb.outline.set_visible(False);cb.ax.tick_params(length=0,labelsize=8)
    fig.text(.015,.975,'ONI–occurrence correlation',fontsize=16,fontweight='bold',color='#263746')
    fig.text(.015,.952,'MAIZE · Six phenological phases · 1981–2016 · ONI ERSSTv6',fontsize=9,color='#52616e')
    fig.legend(handles=[Line2D([],[],marker='s',linestyle='',markerfacecolor='#c5c9cd',markeredgecolor='#c5c9cd',label='Gray: undefined correlation / insufficient data')],
        loc='lower left',bbox_to_anchor=(.01,.015),frameon=False,fontsize=8)
    fig.text(.40,.026,'Discrete color intervals; coefficients unchanged. Colors do not indicate statistical significance.',fontsize=8,color='#52616e')
    output=run/'figures';output.mkdir(exist_ok=True)
    stamp=time.strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:6];saved=[]
    for extension in ['png','pdf']:
        path=output/f'pearson_ONI_maize_six_phases_{stamp}.{extension}'
        with path.open('xb') as handle:fig.savefig(handle,format=extension,dpi=240,facecolor='white')
        saved.append(path);print(path,flush=True)
    plt.close(fig)
    pd.DataFrame(summary).to_csv(output/'figure_coverage.csv',index=False)
    (output/'figure_provenance.json').write_text(json.dumps(dict(source=str(source),
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),figures=[str(p) for p in saved],scale=[-1,1],color_intervals=bounds,summary=summary),indent=2),encoding='utf-8')
    if (root/'Repositorio/tesis-cereal-climate').is_dir():
        mirror=root/'Repositorio/tesis-cereal-climate/outputs/agroclima_vigente/correlaciones/maize_ONI_Pearson'/run.name/'figures'
        shutil.copytree(output,mirror,dirs_exist_ok=True)

if __name__=='__main__':main()
