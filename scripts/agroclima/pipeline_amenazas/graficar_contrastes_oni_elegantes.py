"""Equal Earth cell maps of original and detrended ONI contrasts, with frozen shared scales."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection, LineCollection
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.cm import ScalarMappable
from matplotlib.ticker import FuncFormatter
from rutas_resultados_oni import resultados_oni

NAMES=dict(EST='Establecimiento',VEG='Crecimiento vegetativo',FLO='Floración',REP='Desarrollo reproductivo',FIL='Llenado de grano',MAT='Maduración')
HEAT=['EST','VEG','FLO','REP','FIL']
COLORS=['#174c6b','#397b9b','#76a6bd','#bed3dc','#faf9f5','#f1d5b5','#dda56f','#bc7339','#8a461d']


def equal_earth(lon,lat):
    """Spherical Equal Earth, unit radius; equations from OSGeo/PROJ eqearth.cpp."""
    lam=np.deg2rad(lon);theta=np.arcsin(np.sqrt(3)/2*np.sin(np.deg2rad(lat)))
    t2=theta*theta;t6=t2*t2*t2
    x=lam*np.cos(theta)/(np.sqrt(3)/2*(1.340264-3*.081106*t2+t6*(7*.000893+9*.003796*t2)))
    y=theta*(1.340264-.081106*t2+t6*(.000893+.003796*t2))
    return np.stack([x,y],axis=-1)


def cell_vertices(lon,lat):
    x=np.asarray(lon)[:,None]+np.array([-.25,.25,.25,-.25])[None,:]
    y=np.asarray(lat)[:,None]+np.array([-.25,-.25,.25,.25])[None,:]
    return equal_earth(x,y)


def world_geometry(path):
    geo=json.loads(path.read_text(encoding='utf-8'));polygons=[];lines=[]
    def ring(coords):
        a=np.asarray(coords,float)[:,:2]
        if len(a)<3:return
        jumps=np.flatnonzero(np.abs(np.diff(a[:,0]))>180)+1
        for part in np.split(a,jumps):
            if len(part)>1:lines.append(equal_earth(part[:,0],part[:,1]))
        if not len(jumps):polygons.append(equal_earth(a[:,0],a[:,1]))
    for feature in geo['features']:
        g=feature.get('geometry')
        if not g:continue
        parts=[g['coordinates']] if g['type']=='Polygon' else g['coordinates'] if g['type']=='MultiPolygon' else []
        for p in parts:ring(p[0])
    return polygons,lines


def base_map(ax,land,coasts):
    ax.set_facecolor('white')
    ax.add_collection(PolyCollection(land,facecolors='#f1f2ef',edgecolors='none',zorder=0))
    grid=[]
    for lon in [-120,-60,0,60,120]:grid.append(equal_earth(np.full(151,lon),np.linspace(-60,85,151)))
    for lat in [-30,0,30,60]:grid.append(equal_earth(np.linspace(-180,180,361),np.full(361,lat)))
    ax.add_collection(LineCollection(grid,colors='#dce0dd',linewidths=.28,zorder=1))
    ax.add_collection(LineCollection(coasts,colors='#aeb8b7',linewidths=.25,zorder=4))
    ax.set(xlim=(-2.73,2.73),ylim=(-1.13,1.32));ax.set_aspect('equal');ax.axis('off')


def draw_panel(ax,part,value,ic,land,coasts,cmap,norm):
    base_map(ax,land,coasts)
    verts=cell_vertices(part.longitud,part.latitud);v=part[value].to_numpy(float);ok=np.isfinite(v)
    face=cmap(norm(np.nan_to_num(v)))
    ax.add_collection(PolyCollection(verts[ok],facecolors=face[ok],edgecolors='none',rasterized=True,zorder=3))
    insufficient=~part[ic].to_numpy(bool)&ok
    if insufficient.any():
        ax.add_collection(PolyCollection(verts[insufficient],facecolors='none',edgecolors='#555b60',linewidths=0,hatch='....',rasterized=True,zorder=5))
    if (~ok).any():ax.add_collection(PolyCollection(verts[~ok],facecolors='#d5d6d3',edgecolors='#777',linewidths=0,hatch='///',zorder=5))
    return int(insufficient.sum()),int((~ok).sum())


def render(frame,phases,label,value,ic,config,land,coasts,out,dpi,formats):
    heat=phases!=['MAT'];key='calor' if heat else 'MAT';limits=config[key]['cortes'];L=config[key]['limite']
    cmap=ListedColormap(COLORS);norm=BoundaryNorm(limits,cmap.N,clip=True)
    height=15.0 if heat else 5.8
    fig,axes=plt.subplots(len(phases),2,figsize=(14,height),squeeze=False)
    fig.patch.set_facecolor('white')
    fig.subplots_adjust(left=.045,right=.975,bottom=.17 if heat else .36,top=.855 if heat else .72,wspace=.055,hspace=.15)
    title='Calor · frecuencia de episodios' if heat else 'Lluvia en maduración · días afectados'
    fig.text(.05,.965 if heat else .94,title,fontsize=22,fontweight='bold',color='#24383f',va='top')
    subtitle='Contrastes ONI · maíz de secano · 1981–2016'
    fig.text(.05,.935 if heat else .87,subtitle,fontsize=11,color='#52636a',va='top')
    fig.text(.05,.91 if heat else .81,'Principal · exposición observada' if label=='original' else 'Sensibilidad · anomalías respecto a tendencia lineal',fontsize=10.5,color='#52636a',va='top')
    for j,text in enumerate(['CÁLIDO − NEUTRAL','FRÍO − NEUTRAL']):
        box=axes[0,j].get_position();fig.text(box.x0+.5*box.width,.883 if heat else .745,text,ha='center',fontsize=10,fontweight='bold',color='#334c56')
    no_ic=0;missing=0
    for i,phase in enumerate(phases):
        for j,state in enumerate(['calido','frio']):
            part=frame[(frame.fase==phase)&frame.contraste.eq(state+'_menos_neutral')]
            if len(part)!=10923 or part.pixel_id.duplicated().any():raise ValueError('Panel incompleto o duplicado')
            a,b=draw_panel(axes[i,j],part,value,ic,land,coasts,cmap,norm);no_ic+=a;missing+=b
        if heat:axes[i,0].text(.015,1.025,f'{phase}  ·  {NAMES[phase]}',transform=axes[i,0].transAxes,fontsize=10,fontweight='bold',color='#334c56',va='bottom')
    # Histogram and discrete scale share bin edges and are fixed across both versions.
    vals=frame.loc[frame.fase.isin(phases),value].dropna().to_numpy()
    hist_y=.105 if heat else .25;bar_y=.083 if heat else .19
    hist_ax=fig.add_axes([.22,hist_y,.56,.031 if heat else .07])
    clipped=np.clip(vals,-L,L);hist,bins=np.histogram(clipped,bins=limits)
    hist_ax.bar((bins[:-1]+bins[1:])/2,hist,width=np.diff(bins)*.94,color=COLORS,edgecolor='none')
    hist_ax.set_xlim(-L,L);hist_ax.axis('off')
    cax=fig.add_axes([.22,bar_y,.56,.012 if heat else .027])
    cb=fig.colorbar(ScalarMappable(norm=norm,cmap=cmap),cax=cax,orientation='horizontal',boundaries=limits,extend='both',ticks=[-L,-L/2,0,L/2,L])
    cb.outline.set_visible(False);cb.ax.tick_params(labelsize=9,length=2,color='#87969b')
    cb.ax.xaxis.set_major_formatter(FuncFormatter(lambda x,pos:f'{x:.2g}'.replace('-', '−')))
    unit='Diferencia de episodios por 100 días' if heat else 'Diferencia en puntos porcentuales de días afectados'
    cb.set_label(unit,fontsize=10,labelpad=5,color='#334c56')
    low=int((vals < -L).sum());high=int((vals > L).sum())
    note=f'Histograma: observaciones píxel–contraste · fuera de escala: {low:,} abajo / {high:,} arriba'.replace(',','.')
    fig.text(.5,.039 if heat else .087,note,ha='center',fontsize=8,color='#64757a')
    fig.text(.05,.021 if heat else .043,
        f'Equal Earth · celdas 0,5° · puntos: IC no estimable ({no_ic:,}) · gris rayado: sin dato ({missing:,})'.replace(',','.'),fontsize=8,color='#64757a')
    fig.text(.05,.009 if heat else .014,'Blanco: clase central alrededor de cero. IC exploratorios; sin FDR. Los 58 píxeles de soporte espacial parcial fijo se conservan.',fontsize=7.5,color='#64757a')
    stem=f'mapa_ONI_{key}_{label}'
    for fmt in formats:
        fig.savefig(out/(stem+'.'+fmt),dpi=dpi,facecolor='white',metadata={'Creator':'Matplotlib / tesis ONI'})
    plt.close(fig)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sensitivity',type=Path,required=True,help='Carpeta de sensibilidad terminada')
    p.add_argument('--output',type=Path)
    p.add_argument('--outline',type=Path,default=Path('C:/Users/paola/Tesis/Repositorio/tesis-cereal-climate/web-v2/public/data/world_outline.geojson'))
    p.add_argument('--scales',type=Path,help='Configuracion ya congelada; no se recalcula')
    p.add_argument('--dpi',type=int,default=450)
    p.add_argument('--formats',default='png,svg')
    args=p.parse_args();source=args.sensitivity.resolve()
    if not (source/'completed.json').is_file():p.error('La sensibilidad no esta terminada')
    if args.dpi<100:p.error('dpi debe ser >=100')
    formats=args.formats.split(',')
    if not set(formats)<=set(['png','svg']):p.error('Formatos admitidos: png,svg')
    out=args.output.resolve() if args.output else resultados_oni()/('mapas_ONI_'+time.strftime('%Y%m%d_%H%M%S'))
    if out.exists():p.error('La salida ya existe')
    frame=pd.read_csv(source/'comparacion_sensibilidad.csv')
    frame['ic_original_estimado']=frame.estado_ic.eq('estimado')
    if frame.ic_sin_tendencia_estimado.dtype!=bool:frame['ic_sin_tendencia_estimado']=frame.ic_sin_tendencia_estimado.astype(str).str.lower().eq('true')
    if args.scales:config=json.loads(args.scales.read_text(encoding='utf-8'))
    else:
        config=dict(proyeccion='Equal Earth esferica R=1',version=1,metodo='P98 de |delta| agrupando ambos contrastes y ambas versiones; calor comun, MAT aparte',paleta=COLORS)
        for key,mask in [('calor',frame.fase.isin(HEAT)),('MAT',frame.fase.eq('MAT'))]:
            vals=frame.loc[mask,['diferencia','diferencia_sin_tendencia']].to_numpy().ravel();vals=vals[np.isfinite(vals)]
            L=float(np.quantile(np.abs(vals),.98));L=L if L>0 else 1.
            config[key]=dict(limite=L,cortes=np.linspace(-L,L,10).tolist())
    for key in ['calor','MAT']:
        b=np.array(config[key]['cortes']);L=config[key]['limite']
        if len(b)!=10 or not np.all(np.diff(b)>0) or not np.allclose(b,-b[::-1]) or not np.isclose(b[-1],L):raise ValueError('Escala invalida')
    out.mkdir(parents=True)
    (out/'escalas_congeladas.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
    land,coasts=world_geometry(args.outline)
    plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none','hatch.linewidth':.22,'savefig.pad_inches':.05})
    for label,value,ic in [('original','diferencia','ic_original_estimado'),('sin_tendencia','diferencia_sin_tendencia','ic_sin_tendencia_estimado')]:
        for phases in [HEAT,['MAT']]:
            render(frame,phases,label,value,ic,config,land,coasts,out,args.dpi,formats)
            print(f'Mapa {label}: {"calor" if phases==HEAT else "MAT"} exportado',flush=True)
    (out/'completed.json').write_text(json.dumps(dict(entrada=str(source),dpi=args.dpi,formatos=formats,
        figuras=4,escalas='escalas_congeladas.json',
        proyeccion_fuente='https://github.com/OSGeo/PROJ/blob/master/src/projections/eqearth.cpp',
        limites='Mapas exploratorios de contraste, sin inferencia regional; histogramas cuentan pixeles-contraste, no evidencia independiente. Regiones pendientes.',
        fuentes_sha256={str(source/'comparacion_sensibilidad.csv'):hashlib.sha256((source/'comparacion_sensibilidad.csv').read_bytes()).hexdigest(),str(args.outline):hashlib.sha256(args.outline.read_bytes()).hexdigest()}),ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'COMPLETO: {out}',flush=True)


if __name__=='__main__':main()
