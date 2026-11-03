"""Actual regional choropleth maps and confidence-interval panels in seasonal count units."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection,LineCollection
from matplotlib.colors import ListedColormap,BoundaryNorm
from matplotlib.cm import ScalarMappable
from matplotlib.ticker import FuncFormatter
from graficar_contrastes_oni_elegantes import equal_earth,world_geometry,base_map,COLORS,NAMES
from proponer_regiones_oni import LABELS
from rutas_resultados_oni import resultados_oni

PHASES=['EST','VEG','FLO','REP','FIL','MAT']
ORDER=['América del Norte','América Central','Caribe','América del Sur','Europa occidental','Europa meridional','Europa oriental',
       'África septentrional','África occidental','África central','África oriental','África austral',
       'Asia occidental','Asia central','Asia meridional','Asia oriental','Asia sudoriental','Australia y Nueva Zelanda']


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda:f.read(4*1024*1024),b''):h.update(part)
    return h.hexdigest()


def geographical_regions(path):
    """Use the exact country SUBREGION rule used by the geographical proposal."""
    geo=json.loads(path.read_text(encoding='utf-8'));regions={};edges={}
    for f in geo['features']:
        name=LABELS.get(f['properties'].get('SUBREGION'));g=f.get('geometry')
        if not name or not g:continue
        parts=[g['coordinates']] if g['type']=='Polygon' else g['coordinates'] if g['type']=='MultiPolygon' else []
        regions.setdefault(name,[]);edges.setdefault(name,Counter())
        for polygon in parts:
            outer=np.asarray(polygon[0],float)[:,:2]
            if not np.any(np.abs(np.diff(outer[:,0]))>180):regions[name].append(equal_earth(outer[:,0],outer[:,1]))
            for ring in polygon:
                a=np.asarray(ring,float)[:,:2]
                for first,last in zip(a[:-1],a[1:]):
                    if abs(first[0]-last[0])>180:continue
                    first=tuple(np.round(first,7));last=tuple(np.round(last,7))
                    if first!=last:edges[name][tuple(sorted((first,last)))]+=1
    borders={}
    for name,counts in edges.items():
        borders[name]=[equal_earth(np.array([a[0],b[0]]),np.array([a[1],b[1]])) for (a,b),n in counts.items() if n%2]
    return regions,borders


def limits(frame):
    config=dict(medida='conteos_por_temporada',metodo='P98 de |diferencia|; cinco fases de calor y ambos contrastes juntos; MAT independiente',colores=COLORS)
    for key,mask in [('calor',frame.fase.ne('MAT')),('MAT',frame.fase.eq('MAT'))]:
        g=frame[mask];v=g.diferencia.to_numpy(float);v=v[np.isfinite(v)]
        L=float(np.quantile(np.abs(v),.98)) if len(v) else 1.;L=L if L>0 else 1.
        endpoints=g[['diferencia','ic95_inferior','ic95_superior']].to_numpy(float).ravel();endpoints=endpoints[np.isfinite(endpoints)]
        axis_max=float(np.max(np.abs(endpoints)))*1.08 if len(endpoints) and np.max(np.abs(endpoints))>0 else 1.
        config[key]=dict(limite=L,cortes=np.linspace(-L,L,10).tolist(),limite_eje_intervalos=axis_max)
    return config


def draw_ci(ax,g,order,norm,cmap,xlim):
    y=np.arange(len(order));indexed=g.set_index('region').reindex(order)
    for i,(_,r) in enumerate(indexed.iterrows()):
        if not np.isfinite(r.diferencia):continue
        color=cmap(norm(r.diferencia));estimable=r.estado_ic=='estimado' and np.isfinite(r.ic95_inferior) and np.isfinite(r.ic95_superior)
        separated=estimable and (r.ic95_inferior>0 or r.ic95_superior<0)
        if estimable:
            ax.plot([r.ic95_inferior,r.ic95_superior],[i,i],color='#3f555e' if separated else '#89979d',lw=1.1,zorder=2)
            ax.plot([r.ic95_inferior,r.ic95_superior],[i,i],marker='|',markersize=5,linestyle='none',color='#677b83',zorder=2)
        ax.scatter(r.diferencia,i,s=31,facecolor=color,edgecolor='#2a414d' if separated else '#7e8e95',linewidth=.7,zorder=3,marker='o' if estimable else 'x')
    labels=[f'{name}  [{int(indexed.loc[name,"n_pixeles_elegibles"])}]' for name in order]
    ax.set_yticks(y,labels,fontsize=8.6,color='#344e5a');ax.invert_yaxis();ax.set_xlim(-xlim,xlim)
    ax.axvline(0,color='#82969f',lw=.7,ls='--',zorder=0)
    ax.set_axisbelow(True);ax.grid(axis='x',color='#e5e9eb',lw=.5)
    ax.tick_params(axis='y',length=0,pad=6);ax.tick_params(axis='x',labelsize=9,color='#a2adb2',length=3)
    for side in ['top','right','left']:ax.spines[side].set_visible(False)
    ax.spines['bottom'].set_color('#c5ced2');ax.xaxis.set_major_formatter(FuncFormatter(lambda x,pos:f'{x:.2g}'.replace('-','−')))
    ax.set_title('Diferencia e IC del 95 % · [píxeles elegibles]',fontsize=10,loc='left',color='#405c68',pad=12)


def render_phase(frame,phase,order,geometry,borders,land,coasts,config,out,dpi,formats,provisional):
    g=frame[frame.fase.eq(phase)];key='MAT' if phase=='MAT' else 'calor';s=config[key]
    cmap=ListedColormap(COLORS);norm=BoundaryNorm(s['cortes'],len(COLORS),clip=True)
    fig=plt.figure(figsize=(18,12));fig.patch.set_facecolor('white')
    unit='días de lluvia por temporada' if phase=='MAT' else 'episodios por temporada'
    fig.text(.04,.962,f'{phase} · {NAMES[phase]}',fontsize=23,fontweight='bold',color='#263f4d',va='top')
    fig.text(.04,.922,f'ONI y frecuencia regional · maíz · 1981–2016 · diferencia de {unit}',fontsize=11,color='#526d79',va='top')
    if provisional:fig.text(.04,.894,'REGIONES PROVISIONALES · propuesta geográfica basada en el mapa de países',fontsize=9,color='#8a6b3c',va='top')
    for j,(state,title) in enumerate([('calido','Cálido − neutral'),('frio','Frío − neutral')]):
        bottom=.535 if j==0 else .155
        ax=fig.add_axes([.035,bottom,.54,.30]);ci=fig.add_axes([.735,bottom,.235,.30])
        base_map(ax,land,coasts)
        part=g[g.contraste.eq(state+'_menos_neutral')].set_index('region')
        for name in order:
            r=part.loc[name];value=r.diferencia;polys=geometry[name]
            if not np.isfinite(value):face='#d6dadd';hatch='///';style='dotted';color='#a0aaae'
            else:
                face=cmap(norm(value));hatch=None if r.estado_ic=='estimado' else '....'
                separated=r.estado_ic=='estimado' and (r.ic95_inferior>0 or r.ic95_superior<0)
                style='solid' if separated else (0,(2,2));color='#354e59' if separated else '#8e9ea5'
            ax.add_collection(PolyCollection(polys,facecolors=[face],edgecolors='none',hatch=hatch,rasterized=True,zorder=2))
            ax.add_collection(LineCollection(borders[name],colors=[color],linewidths=.55,linestyles=style,zorder=5))
        ax.set_title(title,fontsize=14,fontweight='bold',loc='left',color='#2e4a58',pad=10)
        draw_ci(ci,g[g.contraste.eq(state+'_menos_neutral')],order,norm,cmap,s['limite_eje_intervalos'])
        ci.set_xlabel('Diferencia de '+unit,fontsize=9,color='#405c68')
    # A single discrete scale per figure; fixed for all five heat figures.
    histax=fig.add_axes([.19,.093,.43,.023]);values=g.diferencia.dropna().to_numpy();L=s['limite'];counts,edges=np.histogram(np.clip(values,-L,L),bins=s['cortes'])
    histax.bar((edges[:-1]+edges[1:])/2,counts,width=np.diff(edges)*.94,color=COLORS,edgecolor='none');histax.set_xlim(-L,L);histax.axis('off')
    cax=fig.add_axes([.19,.072,.43,.012]);cb=fig.colorbar(ScalarMappable(norm=norm,cmap=cmap),cax=cax,orientation='horizontal',boundaries=s['cortes'],extend='both',ticks=[-L,-L/2,0,L/2,L])
    cb.outline.set_visible(False);cb.ax.tick_params(labelsize=9,length=2);cb.ax.xaxis.set_major_formatter(FuncFormatter(lambda x,pos:f'{x:.2g}'.replace('-','−')))
    fig.text(.65,.09,'Borde sólido: IC excluye cero\nBorde discontinuo: IC incluye cero\nPunteado: IC no estimable',fontsize=8.5,color='#5b737e',va='center',linespacing=1.5)
    fig.text(.04,.033,'El relleno representa el resumen regional, no una predicción para cada lugar. Igual peso por píxel; la categoría ONI se conserva por ventana local.',fontsize=8.5,color='#5b737e')
    fig.text(.04,.015,'Calor: escala común entre fases. MAT: escala propia. Histogramas cuentan regiones–contraste. IC sin ajuste de multiplicidad o autocorrelación ENSO.',fontsize=8,color='#5b737e')
    for fmt in formats:fig.savefig(out/f'ONI_regional_{phase}_por_temporada.{fmt}',dpi=dpi,facecolor='white',metadata={'Creator':'Matplotlib / tesis'})
    plt.close(fig)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True,help='Carpeta terminada ONI_regional_conteos_temporada')
    p.add_argument('--output',type=Path)
    p.add_argument('--outline',type=Path,default=Path('C:/Users/paola/Tesis/Repositorio/tesis-cereal-climate/web-v2/public/data/world_outline.geojson'))
    p.add_argument('--scales',type=Path)
    p.add_argument('--dpi',type=int,default=400)
    p.add_argument('--formats',default='png,svg')
    args=p.parse_args();source=args.input.resolve()
    if not (source/'completed.json').is_file():p.error('La entrada no esta terminada')
    meta=json.loads((source/'completed.json').read_text(encoding='utf-8'))
    if meta.get('modo_medida')!='seasonal':p.error('Este script necesita conteos POR TEMPORADA, no tasas por 100 dias')
    formats=args.formats.split(',')
    if args.dpi<100 or not set(formats)<=set(['png','svg']):p.error('Revisar dpi >=100 y formatos png,svg')
    frame=pd.read_csv(source/'contrastes_regionales.csv')
    if len(frame)!=meta['filas_contrastes'] or frame.duplicated(['region','fase','contraste']).any():raise ValueError('Resultados duplicados o incompletos')
    if set(frame.fase)!=set(PHASES) or set(frame.contraste)!={'calido_menos_neutral','frio_menos_neutral'}:raise ValueError('Fases/contrastes incompletos')
    if not np.allclose(frame.diferencia,frame.media_categoria-frame.media_neutral,equal_nan=True):raise ValueError('Las diferencias no coinciden con las medias')
    if (frame.ic95_inferior>frame.ic95_superior).any():raise ValueError('Intervalos invertidos')
    if not frame.loc[frame.estado_ic.eq('estimado'),['ic95_inferior','ic95_superior']].notna().all().all():raise ValueError('IC marcado estimado pero ausente')
    if not frame[frame.fase.eq('MAT')].unidad.eq('dias_lluvia_por_temporada').all() or not frame[frame.fase.ne('MAT')].unidad.eq('episodios_por_temporada').all():raise ValueError('Unidades incorrectas')
    geometry,borders=geographical_regions(args.outline)
    missing=set(frame.region)-set(geometry)
    if missing:raise ValueError('Regiones sin geometria: '+str(missing)+'. Se requiere mapa compatible con la regionalizacion elegida.')
    assignments=pd.read_csv(source/'regiones_utilizadas.csv')
    # Fail rather than applying the country SUBREGION geometry to a different rule.
    if 'pais_referencia' not in assignments or 'nota' not in assignments:raise ValueError('La asignacion no acredita la propuesta geografica basada en Natural Earth; aportar geometria compatible antes de graficar.')
    proposal=resultados_oni()/'propuesta_regiones_geograficas_20261020/propuesta.json'
    if not proposal.is_file() or json.loads(proposal.read_text(encoding='utf-8'))['sha256']!=sha(args.outline):raise ValueError('Mapa distinto al que definio las regiones')
    original=pd.read_csv(proposal.parent/'regiones_propuestas_para_revisar.csv',usecols=['pixel_id','region'])
    comparison=assignments[['pixel_id','region']].merge(original,on='pixel_id',how='left',suffixes=('_usada','_geografica'),validate='one_to_one')
    assigned=comparison.region_usada.notna()
    if not comparison.loc[assigned,'region_usada'].eq(comparison.loc[assigned,'region_geografica']).all():raise ValueError('Asignacion modificada: no se pintan poligonos que ya no corresponden')
    names=set(frame.region);order=[name for name in ORDER if name in names]+sorted(names-set(ORDER))
    if len(frame)!=len(order)*6*2:raise ValueError('Faltan resultados por region/fase/contraste')
    out=args.output.resolve() if args.output else resultados_oni()/('mapas_ONI_regionales_temporada_'+time.strftime('%Y%m%d_%H%M%S'))
    if out.exists():p.error('La salida ya existe')
    config=json.loads(args.scales.read_text(encoding='utf-8')) if args.scales else limits(frame)
    if config.get('medida')!='conteos_por_temporada':raise ValueError('Las escalas no son de conteos por temporada')
    for key in ['calor','MAT']:
        b=np.asarray(config[key]['cortes']);L=config[key]['limite']
        if len(b)!=10 or not np.all(np.diff(b)>0) or not np.allclose(b,-b[::-1]) or not np.isclose(b[-1],L):raise ValueError('Escala invalida')
        mask=frame.fase.eq('MAT') if key=='MAT' else frame.fase.ne('MAT')
        endpoints=frame.loc[mask,['diferencia','ic95_inferior','ic95_superior']].to_numpy(float)
        if np.nanmax(np.abs(endpoints))>config[key]['limite_eje_intervalos']:raise ValueError('El eje de intervalos recortaria valores; usar limites completos')
    out.mkdir(parents=True,exist_ok=False)
    (out/'escalas_regionales_congeladas.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
    land,coasts=world_geometry(args.outline);plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none','hatch.linewidth':.3})
    for phase in PHASES:
        render_phase(frame,phase,order,geometry,borders,land,coasts,config,out,args.dpi,formats,meta.get('regionalizacion_provisional',True))
        print(f'MAPA REGIONAL {phase}: calido/frio, IC laterales y unidades por temporada',flush=True)
    (out/'LEEME.txt').write_text('Seis figuras: una por fase; cada una con mapas calido-neutral/frio-neutral y paneles de intervalos.\nCalor: episodios medios por temporada; MAT: dias medios de lluvia por temporada, NO porcentajes.\nEl mapa pinta la media regional en sus poligonos, no una estimacion local de todos sus puntos. Regiones provisionales segun Natural Earth SUBREGION por pais.\nEscala comun para calor y propia de MAT. IC completos en el panel lateral, sin truncar a la escala de color.\nBorde solido: IC excluye cero; discontinuo: incluye cero; punteado: no estimable. No ajuste FDR ni autocorrelacion.\nLas tasas por 100 dias anteriores se conservan. No se modifica ninguna estimacion ni los datos MJO.\nLos territorios/transcontinentales heredan la regionalizacion propuesta, pendiente de revision.\n',encoding='utf-8')
    (out/'completed.json').write_text(json.dumps(dict(entrada=str(source),figuras=6,formatos=formats,dpi=args.dpi,unidades='conteos_por_temporada',regionalizacion_provisional=meta.get('regionalizacion_provisional',True),
        fuentes_sha256={str(source/'contrastes_regionales.csv'):sha(source/'contrastes_regionales.csv'),str(args.outline):sha(args.outline),str(Path(__file__).resolve()):sha(Path(__file__))}),ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'COMPLETO: {out}',flush=True)


if __name__=='__main__':main()
