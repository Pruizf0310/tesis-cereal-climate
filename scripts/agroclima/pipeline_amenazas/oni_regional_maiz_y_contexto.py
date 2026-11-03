"""Recalculate year-bootstrap regional contrasts and plot only maize cells with full context tables."""
import argparse
import json
from pathlib import Path
import sqlite3
import time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import ListedColormap,BoundaryNorm
from matplotlib.cm import ScalarMappable
from matplotlib.ticker import FuncFormatter
from oni_regional import region_contrast
from contrastes_frecuencias_oni import YEARS,season_weights,sha
from graficar_contrastes_oni_elegantes import COLORS,NAMES,equal_earth,cell_vertices,world_geometry,base_map
from rutas_resultados_oni import resultados_oni

PHASES=['EST','VEG','FLO','REP','FIL','MAT']
STATES=['frio','neutral','calido']
ORDER=['América del Norte','América Central','Caribe','América del Sur','Europa occidental','Europa meridional','Europa oriental',
       'África septentrional','África occidental','África central','África oriental','África austral',
       'Asia occidental','Asia central','Asia meridional','Asia oriental','Asia sudoriental','Australia y Nueva Zelanda']


def contextual_contrast(values,categories,weights,state,min_years,min_pixels):
    report,support=region_contrast(values,categories,weights,state,min_years)
    report['pocos_pixeles']=report['n_pixeles_elegibles']<min_pixels
    report['umbral_pocos_pixeles']=min_pixels
    report['media_historica_todas_temporadas']=float(np.nanmean(values[support],axis=1).mean()) if support.any() else np.nan
    for category in STATES:
        counts=((categories[support]==category)&np.isfinite(values[support])).sum(axis=1)
        report[f'anios_{category}_min']=int(counts.min()) if len(counts) else np.nan
        report[f'anios_{category}_mediana']=float(np.median(counts)) if len(counts) else np.nan
        report[f'anios_{category}_max']=int(counts.max()) if len(counts) else np.nan
        report[f'anios_distintos_con_alguna_observacion_{category}']=int(((categories[support]==category)&np.isfinite(values[support])).any(axis=0).sum()) if support.any() else 0
    return report,support


def freeze_scales(table):
    cfg=dict(medida='conteos_por_temporada',regla='P98 absoluto de contrastes regionales; cinco fases de calor juntas y MAT aparte',colores=COLORS)
    for name,mask in [('calor',table.fase.ne('MAT')),('MAT',table.fase.eq('MAT'))]:
        t=table[mask];values=t.diferencia.dropna().to_numpy();L=float(np.quantile(np.abs(values),.98)) if len(values) else 1.;L=L if L>0 else 1.
        ic=t[['diferencia','ic95_inferior','ic95_superior']].to_numpy(float);finite=ic[np.isfinite(ic)]
        xlim=float(np.max(np.abs(finite)))*1.08 if len(finite) and np.max(np.abs(finite))>0 else 1.
        cfg[name]=dict(limite=L,cortes=np.linspace(-L,L,10).tolist(),eje_ic=xlim)
    return cfg


def format_number(x):
    if not np.isfinite(x):return '—'
    return f'{x:.2f}'.replace('.',',')


def format_years(row,state):
    median=row[f'anios_{state}_mediana'];low=row[f'anios_{state}_min'];high=row[f'anios_{state}_max']
    if not np.isfinite(median):return '—'
    return f'{median:g} [{low:g}–{high:g}]'


def plot_panel(table,cells,supports,phase,contrast,order,scales,land,coasts,out,dpi,formats,min_pixels,provisional):
    t=table[table.fase.eq(phase)&table.contraste.eq(contrast)].set_index('region').reindex(order)
    s=scales['MAT' if phase=='MAT' else 'calor'];norm=BoundaryNorm(s['cortes'],len(COLORS),clip=True);cmap=ListedColormap(COLORS)
    fig=plt.figure(figsize=(24,11));fig.patch.set_facecolor('white')
    ax=fig.add_axes([.025,.29,.40,.50]);forest=fig.add_axes([.59,.20,.13,.59]);details=fig.add_axes([.735,.20,.245,.59])
    title='Cálido − neutral' if contrast.startswith('calido') else 'Frío − neutral'
    unit='días de lluvia por temporada' if phase=='MAT' else 'episodios por temporada'
    fig.text(.035,.956,f'{phase} · {NAMES[phase]}  |  {title}',fontsize=23,fontweight='bold',color='#253f4b',va='top')
    fig.text(.035,.913,f'Maíz · 1981–2016 · diferencia regional de {unit}',fontsize=12,color='#54717d',va='top')
    fig.text(.035,.875,'Regiones provisionales' if provisional else 'Regiones según asignación guardada',fontsize=10,color='#8d7145',va='top')
    base_map(ax,land,coasts)
    # This is the whole analysis maize footprint, never a country or continent fill.
    ax.add_collection(PolyCollection(cell_vertices(cells.longitud,cells.latitud),facecolors='#cdd5d9',edgecolors='none',rasterized=True,zorder=2))
    support=supports[supports.fase.eq(phase)&supports.contraste.eq(contrast)]
    eligible=support[support.elegible].merge(cells,on=['pixel_id','region'],validate='one_to_one')
    for region,part in eligible.groupby('region'):
        r=t.loc[region]
        if not np.isfinite(r.diferencia):continue
        ax.add_collection(PolyCollection(cell_vertices(part.longitud,part.latitud),facecolors=[cmap(norm(r.diferencia))],edgecolors='none',rasterized=True,zorder=3))
        if r.pocos_pixeles:
            xy=equal_earth(part.longitud.mean(),part.latitud.mean())
            ax.text(xy[0],xy[1],'†',fontsize=19,fontweight='bold',color='#9a652c',ha='center',va='center',zorder=7,
                    bbox=dict(boxstyle='circle,pad=.08',facecolor='white',edgecolor='#c9aa7f',linewidth=.6,alpha=.95))
    ax.set_title('Solo píxeles de maíz del análisis',loc='left',fontsize=12,color='#3d5d6c',pad=10)
    y=np.arange(len(order));forest.set_ylim(len(order)-.5,-.5);details.set_ylim(len(order)-.5,-.5);details.set_xlim(0,1)
    forest.set_xlim(-s['eje_ic'],s['eje_ic']);forest.axvline(0,color='#8b9da4',lw=.7,ls='--')
    forest.grid(axis='x',color='#e4e9eb',lw=.5);forest.set_axisbelow(True)
    forest.set_yticks(y,[r+(' †' if t.loc[r,'pocos_pixeles'] else '') for r in order],fontsize=9.5,color='#354f5b')
    forest.tick_params(axis='y',length=0,pad=8);forest.tick_params(axis='x',labelsize=9)
    forest.xaxis.set_major_locator(plt.MaxNLocator(5));forest.xaxis.set_major_formatter(FuncFormatter(lambda x,p:f'{x:.2g}'.replace('-','−')))
    forest.set_title('Diferencia e IC 95 %',fontsize=10,color='#3d5d6c',pad=15)
    forest.set_xlabel('Diferencia de\n'+unit,fontsize=9,color='#526c78')
    for side in ['top','right','left']:forest.spines[side].set_visible(False)
    forest.spines['bottom'].set_color('#c6d0d5')
    cols=[.045,.205,.365,.58,.775,.955]
    for x,label in zip(cols,['Frío','Neutral','Cálido','Histórica','Neutral','Píxeles']):
        details.text(x,1.026,label,transform=details.transAxes,ha='center',fontsize=9.2,fontweight='bold',color='#354f5b')
    details.text(.205,1.087,'Años: mediana [mín–máx]',transform=details.transAxes,ha='center',fontsize=9.5,color='#526c78')
    details.text(.68,1.087,'Media por temporada',transform=details.transAxes,ha='center',fontsize=9.5,color='#526c78')
    details.axis('off')
    for i,(_,r) in enumerate(t.iterrows()):
        if i%2==0:
            forest.axhspan(i-.5,i+.5,color='#f7f9fa',zorder=0);details.axhspan(i-.5,i+.5,color='#f7f9fa',zorder=0)
        if np.isfinite(r.diferencia):
            if r.estado_ic=='estimado':forest.plot([r.ic95_inferior,r.ic95_superior],[i,i],color='#58717e',lw=1.1,marker='|',markersize=4)
            forest.scatter(r.diferencia,i,s=28,facecolor=cmap(norm(r.diferencia)),edgecolor='#3e5967',linewidth=.7,zorder=4)
        values=[format_years(r,c) for c in STATES]+[format_number(r.media_historica_todas_temporadas),format_number(r.media_neutral),str(int(r.n_pixeles_elegibles))]
        for j,(x,value) in enumerate(zip(cols,values)):
            details.text(x,i,value,ha='center',va='center',fontsize=9,color='#9a652c' if r.pocos_pixeles and j==5 else '#405c69',fontweight='bold' if r.pocos_pixeles and j==5 else 'normal')
    # Explicit counts/years and raw frequency are visible, not hidden in a caption.
    histogram=fig.add_axes([.085,.19,.28,.032]);v=t.diferencia.dropna().to_numpy();L=s['limite'];hist,bins=np.histogram(np.clip(v,-L,L),bins=s['cortes'])
    histogram.bar((bins[:-1]+bins[1:])/2,hist,width=np.diff(bins)*.94,color=COLORS,edgecolor='none');histogram.set_xlim(-L,L);histogram.axis('off')
    cax=fig.add_axes([.085,.164,.28,.014]);cb=fig.colorbar(ScalarMappable(norm=norm,cmap=cmap),cax=cax,orientation='horizontal',extend='both',boundaries=s['cortes'],ticks=[-L,-L/2,0,L/2,L])
    cb.outline.set_visible(False);cb.ax.tick_params(labelsize=9,length=2);cb.ax.xaxis.set_major_formatter(FuncFormatter(lambda x,p:f'{x:.2g}'.replace('-','−')))
    cb.set_label('Diferencia de '+unit,fontsize=10,color='#4d6976')
    fig.text(.035,.095,f'† Menos de {min_pixels} píxeles elegibles: aviso de cobertura; la región se conserva. Gris en el maíz: sin soporte suficiente para este contraste.',fontsize=9.5,color='#607984')
    fig.text(.035,.069,'Los años por categoría varían entre píxeles por sus calendarios: se muestra mediana y rango, nunca la suma de píxeles×años como años independientes.',fontsize=9.3,color='#607984')
    fig.text(.035,.044,'Histórica: media de todas las temporadas; Neutral: frecuencia de referencia del contraste. Ambas usan los mismos píxeles elegibles que la diferencia.',fontsize=9.3,color='#607984')
    fig.text(.035,.021,'IC: bootstrap de años compartidos, sin remuestrear píxeles. El color es un resumen regional sobre el maíz observado; no es una estimación local ni causal.',fontsize=9.3,color='#607984')
    stem=f'{phase}_{contrast}_maiz_contexto'
    for fmt in formats:fig.savefig(out/(stem+'.'+fmt),dpi=dpi,facecolor='white',metadata={'Creator':'Matplotlib / tesis'})
    plt.close(fig)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True,help='Salida regional previa para reutilizar su asignacion')
    p.add_argument('--matrix',type=Path)
    p.add_argument('--output',type=Path)
    p.add_argument('--bootstrap',type=int,default=2000)
    p.add_argument('--seed',type=int,default=20261019)
    p.add_argument('--min-years',type=int,default=5)
    p.add_argument('--min-pixels',type=int,default=30,help='Umbral descriptivo de cobertura; marca, no excluye')
    p.add_argument('--dpi',type=int,default=300)
    p.add_argument('--formats',default='png,svg')
    p.add_argument('--phases',default=','.join(PHASES),help='Omitir para todas las fases; selector para prueba')
    p.add_argument('--outline',type=Path,default=Path('C:/Users/paola/Tesis/Repositorio/tesis-cereal-climate/web-v2/public/data/world_outline.geojson'))
    args=p.parse_args();started=time.perf_counter();source=args.input.resolve()
    if not (source/'completed.json').is_file():p.error('Entrada no terminada')
    meta=json.loads((source/'completed.json').read_text(encoding='utf-8'))
    if meta.get('modo_medida')!='seasonal':p.error('Usar conteos por temporada')
    phases=args.phases.split(',');formats=args.formats.split(',')
    if not phases or len(set(phases))!=len(phases) or not set(phases)<=set(PHASES):p.error('Fases incorrectas')
    if not set(formats)<=set(['png','svg']) or args.dpi<100 or args.min_pixels<1 or args.bootstrap<200 or not 2<=args.min_years<=36:p.error('Parametros invalidos')
    matrix=args.matrix.resolve() if args.matrix else resultados_oni()/'matriz_frecuencias_ONI_corregida_20261019_165114/matriz_frecuencias_ONI.sqlite'
    c=sqlite3.connect(matrix.as_uri()+'?mode=ro',uri=True)
    mapping=pd.read_csv(source/'regiones_utilizadas.csv',usecols=['pixel_id','region']).dropna(subset=['region'])
    if mapping.pixel_id.duplicated().any():raise ValueError('Asignacion regional duplicada')
    coords=pd.read_sql_query('SELECT DISTINCT pixel_id,latitud,longitud FROM matriz',c)
    cells=coords.merge(mapping,on='pixel_id',how='inner',validate='one_to_one')
    if len(cells)!=len(mapping):raise ValueError('Asignacion incluye pixeles desconocidos')
    out=args.output.resolve() if args.output else resultados_oni()/('ONI_regional_maiz_contexto_'+time.strftime('%Y%m%d_%H%M%S'))
    out.mkdir(parents=True,exist_ok=False)
    weights=season_weights(args.bootstrap,args.seed)
    # 36 years per replicate, same draws across all regions, pixels and phases.
    if weights.shape!=(args.bootstrap,36) or not (weights.sum(axis=1)==36).all():raise ValueError('Remuestreo de anios invalido')
    np.savez_compressed(out/'bootstrap_anios_compartidos.npz',temporadas=YEARS,pesos=weights.astype(np.uint8),semilla=args.seed)
    estimates=[];support_rows=[]
    for phase in phases:
        annual=pd.read_sql_query('SELECT pixel_id,temporada,cat_oni,conteo_original,par_frecuencia_oni_valido,estado_cobertura_espacial FROM matriz WHERE fase=?',c,params=(phase,))
        annual=annual.merge(mapping,on='pixel_id',how='inner',validate='many_to_one')
        annual.loc[annual.par_frecuencia_oni_valido.ne(1),'conteo_original']=np.nan
        if annual.duplicated(['pixel_id','temporada']).any():raise ValueError('Claves anuales duplicadas')
        for region,part in annual.groupby('region',sort=True):
            v=part.pivot(index='pixel_id',columns='temporada',values='conteo_original').reindex(columns=YEARS)
            cat=part.pivot(index='pixel_id',columns='temporada',values='cat_oni').reindex(index=v.index,columns=YEARS).to_numpy()
            for state in ['calido','frio']:
                r,support=contextual_contrast(v.to_numpy(float),cat,weights,state,args.min_years,args.min_pixels)
                r.update(region=str(region),fase=phase,contraste=state+'_menos_neutral',unidad='dias_lluvia_por_temporada' if phase=='MAT' else 'episodios_por_temporada',
                    bootstrap_unidad='temporada',bootstrap_replicas=args.bootstrap,semilla=args.seed,ponderacion='igual_por_pixel',
                    n_pixeles_soporte_parcial=int(part.loc[part.pixel_id.isin(v.index[support]) & part.estado_cobertura_espacial.eq('parcial_fija'),'pixel_id'].nunique()))
                estimates.append(r)
                support_rows.extend(dict(region=str(region),fase=phase,contraste=state+'_menos_neutral',pixel_id=int(pid),elegible=bool(ok)) for pid,ok in zip(v.index,support))
        print(f'{phase}: IC por anios, anos de cada categoria y frecuencia historica calculados',flush=True)
    table=pd.DataFrame(estimates);support=pd.DataFrame(support_rows)
    expected=mapping.region.nunique()*len(phases)*2
    if len(table)!=expected or table.duplicated(['region','fase','contraste']).any():raise ValueError('Tabla de estimaciones incompleta')
    if not np.allclose(table.diferencia,table.media_categoria-table.media_neutral,equal_nan=True):raise ValueError('Diferencia inconsistente')
    if (table.ic95_inferior>table.ic95_superior).any():raise ValueError('IC invertido')
    table.to_csv(out/'tabla_completa_figuras.csv',index=False,encoding='utf-8-sig',na_rep='')
    support.to_csv(out/'soporte_pixeles_por_contraste.csv',index=False,encoding='utf-8-sig')
    # Explicit map table: each painted cell traces back to a regional estimate.
    map_table=support.merge(cells,on=['pixel_id','region'],validate='many_to_one').merge(table[['region','fase','contraste','diferencia','pocos_pixeles','media_neutral','media_historica_todas_temporadas']],on=['region','fase','contraste'],validate='many_to_one')
    map_table.to_csv(out/'tabla_celdas_del_mapa.csv.gz',index=False,compression='gzip',na_rep='')
    mapping.to_csv(out/'regiones_utilizadas.csv',index=False,encoding='utf-8-sig')
    cfg=freeze_scales(table);(out/'escalas_congeladas.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
    pending=out/'tablas_figuras.pending.sqlite';dest=sqlite3.connect(pending)
    table.to_sql('tabla_figuras',dest,index=False,chunksize=5000);map_table.to_sql('celdas_mapa',dest,index=False,chunksize=5000)
    dest.execute('CREATE UNIQUE INDEX clave_figuras ON tabla_figuras(region,fase,contraste)')
    dest.execute('CREATE UNIQUE INDEX clave_celdas ON celdas_mapa(pixel_id,fase,contraste)')
    if dest.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('SQLite no integro')
    dest.commit();dest.close();pending.rename(out/'tablas_figuras.sqlite');c.close()
    # Check that the map masks contain exactly the eligible maize cells.
    if len(map_table)!=len(cells)*len(phases)*2:raise ValueError('Celdas del mapa incompletas')
    read=pd.read_csv(out/'tabla_completa_figuras.csv');pd.testing.assert_frame_equal(read,table,check_dtype=False,check_exact=False,rtol=1e-10,atol=1e-12)
    land,coasts=world_geometry(args.outline);names=set(table.region);order=[r for r in ORDER if r in names]+sorted(names-set(ORDER))
    plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none'})
    for phase in phases:
        for contrast in ['calido_menos_neutral','frio_menos_neutral']:
            plot_panel(table,cells,support,phase,contrast,order,cfg,land,coasts,out,args.dpi,formats,args.min_pixels,meta.get('regionalizacion_provisional',True))
            print(f'MAPA: {phase} {contrast}; solo maiz y tabla lateral completa',flush=True)
    (out/'LEEME.txt').write_text('VERSION: solo maiz, IC por anios y contexto visible.\n1. Bootstrap de 36 temporadas con reemplazo: mismos anios para todos los pixeles y regiones; nunca pixeles como replicas. No es una permutacion de etiquetas ONI.\n2. Panel lateral: anios frio/neutral/calido como mediana [min-max] entre pixeles del soporte. Historica: media de todas las temporadas; Neutral: frecuencia de referencia del contraste, mismo soporte.\n3. Solo se colorean celdas de maiz elegibles. El valor es el resumen regional repetido en esas celdas, no el contraste estimado individualmente por pixel.\n4. Cruz/daga: menos del umbral de pixeles elegibles. Umbral descriptivo por defecto 30, editable; no es regla de significancia y no elimina regiones.\n5. Todas las estimaciones y contexto estan en tabla_completa_figuras.csv/SQLite; tabla_celdas_del_mapa.csv.gz documenta cada celda y elegibilidad.\nLos IC conservan el soporte fijo, requieren >=95% replicas estimables y >=5 temporadas por categoria y pixel. No corrigen autocorrelacion ENSO ni multiplicidad.\nCalor: episodios medios por temporada; MAT: dias medios con lluvia >10 mm por temporada. Conteos decimales validos; no compararlos como tasas entre ventanas de distinta duracion.\nRegiones siguen siendo las aportadas por el analisis previo, sin redefinicion guiada por resultados.\n',encoding='utf-8')
    report=dict(entrada=str(source),filas_estimaciones=len(table),celdas_documentadas=len(map_table),figuras=len(phases)*2,formatos=formats,
        bootstrap_unidad='temporada',remuestreo_pixeles=False,bootstrap_replicas=args.bootstrap,semilla=args.seed,min_anios_categoria=args.min_years,
        umbral_pocos_pixeles=args.min_pixels,regiones_pocos_pixeles=table.loc[table.pocos_pixeles,'region'].unique().tolist(),
        regionalizacion_provisional=meta.get('regionalizacion_provisional',True),prueba_parcial=set(phases)!=set(PHASES),
        fuentes_sha256={str(matrix):sha(matrix),str(source/'regiones_utilizadas.csv'):sha(source/'regiones_utilizadas.csv'),str(Path(__file__).resolve()):sha(Path(__file__))},
        segundos=round(time.perf_counter()-started,2))
    (out/'completed.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'COMPLETO: {out}',flush=True)


if __name__=='__main__':main()
