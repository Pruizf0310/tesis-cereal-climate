"""Seis mapas limpios del acumulado de amenazas de maíz, 1981–2016.
No consulta GEE, no utiliza ONI y no calcula correlaciones.
"""
import argparse
import json
import time
import uuid
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
from matplotlib.lines import Line2D

PHASES=['EST','VEG','REP','FLO','FIL','MAT']
NAMES=['Establishment','Vegetative growth','Reproductive development','Flowering','Grain filling','Maturation']

def boundaries(path):
    lines=[]
    def collect(g):
        if g['type']=='Polygon':lines.extend(g['coordinates'])
        elif g['type']=='MultiPolygon':
            for polygon in g['coordinates']:lines.extend(polygon)
        elif g['type']=='GeometryCollection':
            for child in g['geometries']:collect(child)
    if path.exists():
        for f in json.loads(path.read_text(encoding='utf-8')).get('features',[]):
            if f.get('geometry'):collect(f['geometry'])
    return [x for x in lines if len(x)>1 and np.abs(np.diff(np.asarray(x)[:,0])).max()<180]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=Path('C:/Users/paola/Tesis'))
    args=ap.parse_args();root=args.root;tick=time.perf_counter()
    base=root/'03_Resultados/Agroclima/vigente'
    source=base/'ejecuciones/maize_seis_fases_GEE_1981_2016/resumen_GDHY_anual.csv'
    out=base/'diagnosticos/resumen_visual_maize';out.mkdir(parents=True,exist_ok=True)
    coords=pd.read_csv(root/'02_Procesados/Pixeles_correlacion_vigentes/pixeles_maize.csv')
    if coords.pixel_id.duplicated().any():raise ValueError('Píxeles duplicados')
    lookup=dict(zip(coords.pixel_id,range(len(coords))))
    shape=(6,len(coords),36);values=np.full(shape,np.nan);seen=np.zeros(shape,bool)
    columns=['pixel_id','phase','season_year','quality','mean_count_per_native_cell','count_unit',
             'variable','operator','threshold','min_days']
    rules={phase:set() for phase in PHASES}
    total=0
    print('Acumulando resultados locales de las 36 temporadas. Sin descargas ni ONI.',flush=True)
    for df in pd.read_csv(source,usecols=columns,chunksize=100000):
        df=df[df.pixel_id.isin(lookup)&df.season_year.between(1981,2016)]
        for rule in df[['phase','variable','operator','threshold','min_days','count_unit']].drop_duplicates().itertuples(index=False,name=None):
            if rule[0] not in rules:raise ValueError('Fase desconocida')
            rules[rule[0]].add(tuple(rule[1:]))
        p=df.phase.map(dict(zip(PHASES,range(6))))
        if p.isna().any():raise ValueError('Fase desconocida')
        p=p.to_numpy(dtype=int);i=df.pixel_id.map(lookup).to_numpy(dtype=int)
        j=df.season_year.to_numpy(dtype=int)-1981
        slots=np.ravel_multi_index((p,i,j),shape)
        if len(np.unique(slots))!=len(slots) or seen[p,i,j].any():raise ValueError('Observaciones duplicadas')
        seen[p,i,j]=True
        good=(df.quality=='OK')&np.isfinite(df.mean_count_per_native_cell)
        if (df.loc[good,'mean_count_per_native_cell']<0).any():raise ValueError('Conteos negativos')
        values[p,i,j]=np.where(good,df.mean_count_per_native_cell,np.nan)
        total+=len(df)
        print(f'{total:,}/{np.prod(shape):,} filas | {time.perf_counter()-tick:.0f} s',flush=True)
    if not seen.all():raise ValueError('Faltan combinaciones píxel/fase/año')
    labels={}
    for phase,items in rules.items():
        if len(items)!=1:raise ValueError(f'La fase {phase} no tiene una única regla en los resultados: {items}')
        variable,operator,threshold,min_days,unit=next(iter(items))
        symbol={'>=':'≥','>':'>','<=':'≤','<':'<','==':'='}.get(operator,operator)
        number=f'{float(threshold):g}'
        if variable=='tmax_c' and unit=='episodes':
            labels[phase]=f'Daily Tmax {symbol}{number} °C · ≥{int(min_days)} consecutive days'
        elif variable=='precip_mm' and unit=='days':
            labels[phase]=f'Daily precipitation {symbol}{number} mm · one occurrence per day'
        else:raise ValueError(f'Revisar etiqueta de la regla: {phase}: {items}')
    n=np.isfinite(values).sum(axis=2)
    # Compare identical exposure periods: incomplete 36-year records remain gray.
    accumulated=np.where(n==36,np.nansum(values,axis=2),np.nan)
    rows=[]
    for p,phase in enumerate(PHASES):
        df=coords[['pixel_id','latitude','longitude']].copy();df['phase']=phase
        df['valid_years']=n[p];df['accumulated_1981_2016']=accumulated[p]
        df['unit']='mean_native_cell_rain_days' if phase=='MAT' else 'mean_native_cell_heat_episodes'
        rows.append(df)
    pd.concat(rows).to_csv(out/'acumulado_amenazas_por_pixel_fase.csv',index=False,encoding='utf-8-sig')
    outline=boundaries(root/'Repositorio/tesis-cereal-climate/web-v2/public/data/world_outline.geojson')
    r=np.rint((coords.latitude.to_numpy()+89.75)/.5).astype(int)
    c=np.rint((coords.longitude.to_numpy()+179.75)/.5).astype(int)
    if ((r<0)|(r>=360)|(c<0)|(c>=720)).any():raise ValueError('Coordenadas fuera de malla')
    heat=LinearSegmentedColormap.from_list('calor',['#fffaf0','#f7c86a','#eb8643','#c34c30','#7c2425'])
    rain=LinearSegmentedColormap.from_list('lluvia',['#f3f9fc','#a6d5e5','#4b9bbb','#195b82','#14364e'])
    # Zero is white; identical linear heat scale in EST, VEG, REP, FLO and FIL.
    heat.set_under('white');rain.set_under('white')
    for cm in [heat,rain]:cm.set_bad((0,0,0,0))
    max_heat=max(1,float(np.nanmax(accumulated[:5]))) if np.isfinite(accumulated[:5]).any() else 1
    max_rain=max(1,float(np.nanmax(accumulated[5]))) if np.isfinite(accumulated[5]).any() else 1
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'text.color':'#263746'})
    fig=plt.figure(figsize=(15,12),facecolor='white')
    gs=fig.add_gridspec(4,2,height_ratios=[1,1,1,.065],left=.035,right=.965,top=.88,bottom=.15,hspace=.20,wspace=.055)
    meshes={}
    for p,(phase,name) in enumerate(zip(PHASES,NAMES)):
        panel=gs[p//2,p%2].subgridspec(2,1,height_ratios=[.24,1],hspace=.02)
        header=fig.add_subplot(panel[0]);header.set_axis_off()
        header.text(0,.96,name,fontsize=13,fontweight='bold',ha='left',va='top',transform=header.transAxes)
        header.text(1,.96,phase,fontsize=10,color='#73818d',ha='right',va='top',transform=header.transAxes)
        header.text(0,.08,labels[phase],fontsize=9,color='#637381',ha='left',va='bottom',transform=header.transAxes)
        ax=fig.add_subplot(panel[1]);ax.set_facecolor('#f5f7f8')
        grid=np.full((360,720),np.nan);grid[r,c]=accumulated[p]
        missing=np.full((360,720),np.nan);missing[r[~np.isfinite(accumulated[p])],c[~np.isfinite(accumulated[p])]]=1
        ax.pcolormesh(np.arange(-180,180.5,.5),np.arange(-90,90.5,.5),missing,cmap=ListedColormap(['#aab2ba']),rasterized=True)
        meshes['rain' if p==5 else 'heat']=ax.pcolormesh(np.arange(-180,180.5,.5),np.arange(-90,90.5,.5),grid,
            cmap=rain if p==5 else heat,vmin=1e-9,vmax=max_rain if p==5 else max_heat,rasterized=True)
        if outline:ax.add_collection(LineCollection(outline,colors='#bdc6cd',linewidths=.35))
        ax.set(xlim=(-180,180),ylim=(-58,82));ax.set_aspect('equal',adjustable='box')
        ax.set_xticks([]);ax.set_yticks([])
        for spine in ax.spines.values():spine.set_visible(False)
    for col,key,label in [(0,'heat','Cumulative heat episodes meeting threshold and duration'),(1,'rain','Cumulative days exceeding the precipitation threshold')]:
        cb=fig.colorbar(meshes[key],cax=fig.add_subplot(gs[3,col]),orientation='horizontal')
        cb.set_label(label,fontsize=10,labelpad=8);cb.outline.set_visible(False);cb.ax.tick_params(length=0,labelsize=9)
    fig.text(.035,.955,'Cumulative occurrences of threshold-defined climate conditions',fontsize=21,fontweight='bold',ha='left')
    fig.text(.035,.918,'MAIZE  |  By phenological phase and indicated threshold  |  1981–2016  |  36 seasons',fontsize=12,color='#637381',ha='left')
    fig.legend(handles=[Line2D([],[],marker='s',linestyle='',markerfacecolor='white',markeredgecolor='#aab2ba',label='No occurrences'),
        Line2D([],[],marker='s',linestyle='',markerfacecolor='#aab2ba',markeredgecolor='#aab2ba',label='Incomplete series')],
        loc='lower left',bbox_to_anchor=(.03,.045),ncol=2,frameon=False,fontsize=10)
    fig.text(.035,.032,'One occurrence per qualifying heat episode; precipitation occurrences are days. Pixel values are cumulative spatial means.',fontsize=9,color='#637381')
    fig.text(.035,.013,'Only series with 36 complete seasons are colored. Heat and precipitation use different units and scales.',fontsize=9,color='#637381')
    # Never overwrite a figure that Windows/another viewer may have open.
    # Explicit format + binary handle avoids PIL reopening an existing path in w+b.
    run_id=time.strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:6]
    saved=[]
    for suffix in ['png','pdf']:
        path=out/f'acumulado_maize_{run_id}.{suffix}'
        with path.open('xb') as handle:
            fig.savefig(handle,format=suffix,dpi=240,facecolor='white')
        saved.append(str(path))
    plt.close(fig)
    metadata=dict(source=str(source),figures=saved,rows=total,pixels=len(coords),elapsed_seconds=time.perf_counter()-tick,
        displayed_rules=labels,
        statistic='Sum across 36 seasons of mean event counts per native ERA cell within GDHY pixel. No ONI, matrix or correlations.',
        complete_pixels_per_phase=dict(zip(PHASES,(n==36).sum(axis=1).tolist())),
        heat_max=max_heat,rain_max=max_rain,
        limitations=['Only complete 36-season series colored; missing never zero.',
        'Season-year is planting label; windows may extend into next calendar year.',
        'Existing phase proxies and FIL 32.7/32.9 discrepancy retained.',
        'Counts depend on phase length and hazard definition; phase totals are not independent unique events and should not be summed together.'])
    (out/'procedencia_acumulado.json').write_text(json.dumps(metadata,indent=2,ensure_ascii=False),encoding='utf-8')
    for path in saved:print(f'Figura guardada: {path}',flush=True)
    print(f'Terminado en {metadata["elapsed_seconds"]:.1f} segundos.',flush=True)

if __name__=='__main__':main()
