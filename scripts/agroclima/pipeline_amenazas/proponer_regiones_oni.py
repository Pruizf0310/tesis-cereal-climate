"""Propose geographical subregions from an existing Natural Earth country map, without ONI results."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path as PolygonPath
from matplotlib.collections import PolyCollection
from matplotlib.patches import Patch
from rutas_resultados_oni import resultados_oni
from graficar_contrastes_oni_elegantes import equal_earth,cell_vertices,world_geometry,base_map

LABELS={'Northern America':'América del Norte','Central America':'América Central','Caribbean':'Caribe','South America':'América del Sur',
 'Northern Africa':'África septentrional','Western Africa':'África occidental','Middle Africa':'África central','Eastern Africa':'África oriental','Southern Africa':'África austral',
 'Northern Europe':'Europa septentrional','Western Europe':'Europa occidental','Eastern Europe':'Europa oriental','Southern Europe':'Europa meridional',
 'Western Asia':'Asia occidental','Central Asia':'Asia central','Southern Asia':'Asia meridional','Eastern Asia':'Asia oriental','South-Eastern Asia':'Asia sudoriental',
 'Australia and New Zealand':'Australia y Nueva Zelanda','Melanesia':'Melanesia','Micronesia':'Micronesia','Polynesia':'Polinesia'}


def contains_ring(ring,points):
    ring=np.asarray(ring,float)[:,:2].copy()
    ring[:,0]=np.rad2deg(np.unwrap(np.deg2rad(ring[:,0])))
    p=points.copy();p[:,0]+=360*np.rint((ring[:,0].mean()-p[:,0])/360)
    low=ring.min(axis=0);high=ring.max(axis=0)
    use=(p[:,0]>=low[0]-1e-9)&(p[:,0]<=high[0]+1e-9)&(p[:,1]>=low[1]-1e-9)&(p[:,1]<=high[1]+1e-9)
    result=np.zeros(len(p),bool)
    result[use]=PolygonPath(ring).contains_points(p[use],radius=1e-9)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path('C:/Users/paola/Tesis'))
    p.add_argument('--outline',type=Path)
    p.add_argument('--output',type=Path)
    args=p.parse_args();root=args.root.resolve()
    outline=args.outline or root/'Repositorio/tesis-cereal-climate/web-v2/public/data/world_outline.geojson'
    matrix=resultados_oni(root)/'matriz_frecuencias_ONI_corregida_20261019_165114/matriz_frecuencias_ONI.sqlite'
    c=sqlite3.connect(matrix.resolve().as_uri()+'?mode=ro',uri=True)
    d=pd.read_sql_query('SELECT DISTINCT pixel_id,latitud,longitud FROM matriz ORDER BY pixel_id',c);c.close()
    points=d[['longitud','latitud']].to_numpy();matches=[[] for _ in range(len(d))]
    geo=json.loads(outline.read_text(encoding='utf-8'))
    for f in geo['features']:
        g=f.get('geometry');props=f['properties'];sub=props.get('SUBREGION')
        if not g or sub not in LABELS:continue
        polygons=[g['coordinates']] if g['type']=='Polygon' else g['coordinates'] if g['type']=='MultiPolygon' else []
        inside=np.zeros(len(d),bool)
        for polygon in polygons:
            hit=contains_ring(polygon[0],points)
            for hole in polygon[1:]:hit &= ~contains_ring(hole,points)
            inside|=hit
        for i in np.flatnonzero(inside):matches[i].append((sub,props.get('ADMIN','')))
    regions=[];states=[];countries=[];notes=[]
    for items in matches:
        subs=sorted({a for a,b in items});admin=sorted({b for a,b in items})
        regions.append(LABELS[subs[0]] if len(subs)==1 else None)
        states.append('propuesta_por_centro' if len(subs)==1 else 'sin_interseccion_del_centro' if not subs else 'frontera_ambigua')
        countries.append(' / '.join(admin));notes.append('Atributo SUBREGION del país; revisar territorios y países transcontinentales' if len(subs)==1 else 'Revisar geométricamente; no se asignó por vecino cercano')
    d['region']=regions;d['estado_asignacion']=states;d['pais_referencia']=countries;d['nota']=notes
    out=args.output.resolve() if args.output else resultados_oni(root)/('propuesta_regiones_'+time.strftime('%Y%m%d_%H%M%S'))
    out.mkdir(parents=True,exist_ok=False)
    d.to_csv(out/'regiones_propuestas_para_revisar.csv',index=False,encoding='utf-8-sig',na_rep='')
    d.loc[d.region.isna()].to_csv(out/'pixeles_sin_asignacion.csv',index=False,encoding='utf-8-sig')
    summary=d.dropna(subset=['region']).groupby('region').agg(n_pixeles=('pixel_id','size'),lat_min=('latitud','min'),lat_max=('latitud','max'),lon_min=('longitud','min'),lon_max=('longitud','max')).reset_index()
    summary.to_csv(out/'resumen_regiones.csv',index=False,encoding='utf-8-sig')
    land,coasts=world_geometry(outline);fig,ax=plt.subplots(figsize=(15,8.5));base_map(ax,land,coasts)
    names=sorted(d.region.dropna().unique());palette=plt.get_cmap('tab20');handles=[]
    for i,name in enumerate(names):
        sub=d[d.region.eq(name)];color=palette(i%20)
        ax.add_collection(PolyCollection(cell_vertices(sub.longitud,sub.latitud),facecolors=[color],edgecolors='none',rasterized=True,zorder=3))
        handles.append(Patch(facecolor=color,label=f'{name} ({len(sub):,})'))
    unassigned=d[d.region.isna()]
    if len(unassigned):
        pos=equal_earth(unassigned.longitud,unassigned.latitud);ax.scatter(pos[:,0],pos[:,1],s=4,c='#303a40',marker='x',linewidths=.5,zorder=5)
        handles.append(Patch(facecolor='#303a40',label=f'Sin asignación ({len(unassigned)})'))
    fig.suptitle('Propuesta geográfica para revisar · píxeles de maíz',x=.055,ha='left',fontsize=20,color='#243e4c')
    fig.text(.055,.91,'Subregiones del mapa Natural Earth · asignación por centro del píxel · independiente de ONI y rendimiento',fontsize=10,color='#5c717b')
    fig.subplots_adjust(left=.03,right=.74,top=.86,bottom=.09)
    fig.legend(handles=handles,loc='center right',bbox_to_anchor=(.995,.5),fontsize=8.5,frameon=False)
    fig.text(.055,.035,'Propuesta provisional, no regionalización agroclimática. Revisar fronteras, costa y territorios antes de fijarla.',fontsize=9,color='#5c717b')
    fig.savefig(out/'mapa_regiones_propuestas.png',dpi=180,facecolor='white');plt.close(fig)
    metadata=dict(estado='PROPUESTA_PARA_REVISAR',pixeles=len(d),asignados=int(d.region.notna().sum()),sin_asignar=int(d.region.isna().sum()),regiones=names,
        regla='Centro del pixel dentro de pais; atributo SUBREGION de Natural Earth. Sin proximidad ni resultados ONI.',
        limitaciones='Subregiones amplias atribuidas al pais; no son zonas de cultivo. Revisar territorios y paises transcontinentales; costas/islas pueden quedar sin asignar a escala 1:110m.',
        fuente=str(outline),sha256=hashlib.sha256(outline.read_bytes()).hexdigest())
    (out/'propuesta.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:metadata[k] for k in ['pixeles','asignados','sin_asignar','regiones']},ensure_ascii=False,indent=2),flush=True)
    print(f'PROPUESTA: {out}',flush=True)


if __name__=='__main__':main()
