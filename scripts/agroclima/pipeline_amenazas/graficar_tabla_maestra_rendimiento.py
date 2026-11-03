"""Revision grafica de amenaza-rendimiento desde la tabla maestra anual validada."""
import argparse
import itertools
import json
from pathlib import Path
import re
import sqlite3
import time
import unicodedata
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from cruzar_matriz_rendimiento import correlations
from contrastes_frecuencias_oni import sha

PHASES=['EST','VEG','FLO','REP','FIL','MAT']
NAMES={'EST':'Establecimiento','VEG':'Vegetativa','FLO':'Floración','REP':'Reproductiva','FIL':'Llenado','MAT':'Maduración'}
ALIGN={'same-label':'Año de la temporada','maturity-year':'Año del fin de MAT'}
INK='#243e4b';BLUE='#286d8c';ORANGE='#b66b39';MUTED='#607680'
ORDER=['América del Norte','América Central','Caribe','América del Sur','Europa occidental','Europa meridional','Europa oriental',
 'África septentrional','África occidental','África central','África oriental','África austral','Asia occidental','Asia central',
 'Asia meridional','Asia oriental','Asia sudoriental','Australia y Nueva Zelanda']


def slug(s):
    return re.sub(r'[^a-zA-Z0-9]+','_',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode()).strip('_')


def influence(s,min_years=30):
    g=s.dropna(subset=['exposicion_media','z_rendimiento_medio']).sort_values('temporada')
    x=g.exposicion_media.to_numpy(float);y=g.z_rendimiento_medio.to_numpy(float);years=g.temporada.to_numpy(int)
    r,n=correlations(x[None,:],y[None,:]);base=float(r[0]);details=[]
    result=dict(n_anios_comprobados=len(g),r_recalculado=base,r_sin_un_anio_min=np.nan,r_sin_un_anio_max=np.nan,
      r_sin_dos_anios_min=np.nan,r_sin_dos_anios_max=np.nan,anio_mas_influyente=np.nan,
      max_cambio_r_un_anio=np.nan,cambio_signo_al_retirar_un_anio=False,cambio_signo_al_retirar_dos_anios=False,
      pares_anios_examinados=0)
    if not np.isfinite(base) or len(g)<min_years:return result,details
    xx=np.tile(x,(len(g),1));np.fill_diagonal(xx,np.nan)
    rs,ns=correlations(xx,np.tile(y,(len(g),1)));rs[ns<min_years]=np.nan
    for year,rr in zip(years,rs):details.append(dict(anio_retirado=int(year),pearson_sin_anio=float(rr),cambio_r=float(rr-base)))
    if np.isfinite(rs).any():
        k=int(np.nanargmax(np.abs(rs-base)))
        result.update(r_sin_un_anio_min=float(np.nanmin(rs)),r_sin_un_anio_max=float(np.nanmax(rs)),
          anio_mas_influyente=int(years[k]),max_cambio_r_un_anio=float(abs(rs[k]-base)),
          cambio_signo_al_retirar_un_anio=bool(np.any(np.sign(rs[np.isfinite(rs)])!=np.sign(base))))
    pairs=list(itertools.combinations(range(len(g)),2))
    if len(g)-2>=min_years:
        xx=np.tile(x,(len(pairs),1));ii=np.arange(len(pairs));jj=np.array(pairs)
        xx[ii,jj[:,0]]=np.nan;xx[ii,jj[:,1]]=np.nan
        rr,nn=correlations(xx,np.tile(y,(len(pairs),1)));rr[nn<min_years]=np.nan
        finite=np.isfinite(rr)
        if finite.any():
            imin=int(np.nanargmin(rr));imax=int(np.nanargmax(rr))
            result.update(r_sin_dos_anios_min=float(np.nanmin(rr)),r_sin_dos_anios_max=float(np.nanmax(rr)),
              cambio_signo_al_retirar_dos_anios=bool(np.any(np.sign(rr[finite])!=np.sign(base))),pares_anios_examinados=int(finite.sum()),
              anios_r_min=f'{years[pairs[imin][0]]},{years[pairs[imin][1]]}',anios_r_max=f'{years[pairs[imax][0]]},{years[pairs[imax][1]]}')
    return result,details


def clean(ax):
    ax.spines[['top','right']].set_visible(False)
    ax.spines[['bottom','left']].set_color('#c7d1d5')
    ax.grid(color='#e7ecee',lw=.5);ax.set_axisbelow(True);ax.tick_params(labelsize=8,colors=MUTED)


def save(fig,out,name,dpi,formats):
    for ext in formats:fig.savefig(out/f'{name}.{ext}',dpi=dpi,facecolor='white')
    plt.close(fig)


def overview(t,order,alignment,out,dpi,formats):
    fig,axes=plt.subplots(1,6,figsize=(18,9.5),sharey=True)
    fig.subplots_adjust(left=.17,right=.98,bottom=.13,top=.83,wspace=.20)
    fig.text(.04,.955,'Maíz · amenaza y rendimiento',fontsize=23,fontweight='bold',color=INK)
    fig.text(.04,.914,f'{ALIGN[alignment]} · porcentaje de días afectados frente a anomalía de rendimiento',fontsize=12,color=MUTED)
    for ax,phase in zip(axes,PHASES):
        d=t[t.alineacion.eq(alignment)&t.fase.eq(phase)].set_index('region').reindex(order)
        ax.axvline(0,color='#8d9fa6',lw=.8,ls='--')
        for i,(_,r) in enumerate(d.iterrows()):
            if i%2==0:ax.axhspan(i-.5,i+.5,color='#f4f7f8',zorder=0)
            if np.isfinite(r.pearson_r):
                color=BLUE if r.pearson_r<0 else ORANGE
                if np.isfinite(r.ic95_inferior) and np.isfinite(r.ic95_superior):ax.plot([r.ic95_inferior,r.ic95_superior],[i,i],color=color,lw=1.3)
                ax.plot(r.pearson_r,i,'o',ms=4,color=color)
                if r.cambio_signo_al_retirar_dos_anios:ax.plot(.94,i,'D',ms=3.4,color='#a87937')
            else:ax.text(0,i,'—',ha='center',va='center',color=MUTED)
        ax.set_xlim(-1.04,1.04);ax.set_xticks([-1,-.5,0,.5,1]);ax.set_ylim(len(order)-.5,-.5)
        ax.set_title(f'{phase}\n{NAMES[phase]}',fontsize=11,color=INK,pad=14)
        ax.set_yticks(np.arange(len(order)));clean(ax);ax.tick_params(axis='y',length=0)
        ax.set_xlabel('Pearson r',fontsize=9,color=MUTED)
    axes[0].set_yticklabels(order,fontsize=9,color=INK)
    fig.text(.04,.065,'Puntos: Pearson regional. Barras: IC 95 % por bootstrap de temporadas. Azul: más exposición asociada con menor rendimiento.',fontsize=9,color=MUTED)
    fig.text(.04,.035,'◆ Cambia el signo al retirar alguna pareja de años; es sensibilidad, no una prueba de significancia. Regiones y calendario aún en revisión.',fontsize=9,color=MUTED)
    save(fig,out,'01_resumen_'+alignment,dpi,formats)


def regional_scatter(region,t,series,out,dpi,formats,ylim):
    fig,axes=plt.subplots(2,6,figsize=(20,9),sharey=True)
    fig.subplots_adjust(left=.065,right=.97,bottom=.16,top=.82,wspace=.22,hspace=.43)
    fig.text(.04,.95,region+' · exposición y rendimiento',fontsize=23,fontweight='bold',color=INK)
    fig.text(.04,.91,'Un punto por temporada · colores = año · etiquetas = los dos años más influyentes al retirarlos',fontsize=11,color=MUTED)
    norm=Normalize(1981,2016);cm=plt.get_cmap('viridis')
    for j,phase in enumerate(PHASES):
        both=series[series.region.eq(region)&series.fase.eq(phase)]
        xmax=float(both.exposicion_media.max()) if both.exposicion_media.notna().any() else 1
        xmax=max(.01,xmax*1.12)
        for row,alignment in enumerate(ALIGN):
            ax=axes[row,j];s=both[both.alineacion.eq(alignment)].dropna(subset=['exposicion_media','z_rendimiento_medio']).sort_values('temporada')
            r=t[t.region.eq(region)&t.fase.eq(phase)&t.alineacion.eq(alignment)].iloc[0]
            ax.scatter(s.exposicion_media,s.z_rendimiento_medio,c=s.temporada,cmap=cm,norm=norm,s=29,edgecolors='white',linewidths=.4,zorder=3)
            if len(s)>=3 and s.exposicion_media.std()>1e-12:
                fit=np.polyfit(s.exposicion_media,s.z_rendimiento_medio,1);xx=np.array([s.exposicion_media.min(),s.exposicion_media.max()]);ax.plot(xx,np.polyval(fit,xx),color=BLUE,lw=1,alpha=.65)
                base=float(r.pearson_r);infs=[]
                for idx in s.index:
                    sub=s.drop(idx);rr,_=correlations(sub.exposicion_media.to_numpy()[None,:],sub.z_rendimiento_medio.to_numpy()[None,:]);infs.append((abs(rr[0]-base),idx))
                for _,idx in sorted(infs,reverse=True)[:2]:
                    v=s.loc[idx];ax.annotate(str(int(v.temporada)),(v.exposicion_media,v.z_rendimiento_medio),xytext=(4,5),textcoords='offset points',fontsize=7,color=INK)
            ax.axhline(0,color='#a5b3b9',lw=.7);ax.set_xlim(-.02*xmax,xmax);ax.set_ylim(-ylim,ylim);clean(ax)
            ax.set_title(phase+' · '+NAMES[phase],fontsize=10,color=INK)
            ci=f'[{r.ic95_inferior:.2f}, {r.ic95_superior:.2f}]' if np.isfinite(r.ic95_inferior) else 'no estimable'
            ax.text(.03,.97,f'r = {r.pearson_r:.2f} · n = {int(r.temporadas_validas)}\nIC 95 % {ci}',transform=ax.transAxes,va='top',fontsize=8,color=INK,bbox=dict(facecolor='white',alpha=.85,edgecolor='none',pad=2))
            ax.set_xlabel('Días afectados (%)',fontsize=9,color=MUTED)
            if j==0:ax.set_ylabel(ALIGN[alignment]+'\nAnomalía de rendimiento (z)',fontsize=10,color=INK)
    cbax=fig.add_axes([.32,.075,.36,.014]);plt.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cm),cax=cbax,orientation='horizontal',ticks=[1981,1990,2000,2010,2016]);cbax.tick_params(labelsize=8)
    fig.text(.04,.025,'Recta: ajuste descriptivo dentro de muestra. Cada punto promedia pares válidos, con cobertura regional ≥95 %. No es una predicción ni una pérdida porcentual.',fontsize=9,color=MUTED)
    save(fig,out,'02_dispersion_'+slug(region),dpi,formats)


def regional_series(region,series,out,dpi,formats,ylim):
    fig,axes=plt.subplots(6,2,figsize=(16,15),sharex=True)
    fig.subplots_adjust(left=.08,right=.91,bottom=.085,top=.87,hspace=.35,wspace=.32)
    fig.text(.05,.95,region+' · historia anual',fontsize=23,fontweight='bold',color=INK)
    fig.text(.05,.92,'Azul: rendimiento z (eje izquierdo) · naranja: días afectados % (eje derecho). Escalas diferentes, indicadas en los ejes.',fontsize=10,color=MUTED)
    for col,alignment in enumerate(ALIGN):
        for row,phase in enumerate(PHASES):
            ax=axes[row,col];s=series[series.region.eq(region)&series.fase.eq(phase)&series.alineacion.eq(alignment)].sort_values('temporada')
            other=series[series.region.eq(region)&series.fase.eq(phase)];xmax=max(.01,float(other.exposicion_media.max())*1.12) if other.exposicion_media.notna().any() else 1
            ax.plot(s.temporada,s.z_rendimiento_medio,'o-',color=BLUE,lw=1,ms=2.5);ax.axhline(0,color='#a8b6bc',lw=.6);ax.set_ylim(-ylim,ylim);ax.set_xlim(1980,2017);clean(ax)
            ax.set_ylabel(phase+' · z',fontsize=10,color=BLUE);ax.tick_params(axis='y',labelcolor=BLUE)
            twin=ax.twinx();twin.plot(s.temporada,s.exposicion_media,'-',color=ORANGE,lw=1,alpha=.85);twin.set_ylim(0,xmax);twin.set_ylabel('Días afectados (%)',fontsize=8,color=ORANGE);twin.tick_params(axis='y',labelsize=7,labelcolor=ORANGE);twin.spines[['top','left']].set_visible(False);twin.spines['right'].set_color('#c7d1d5')
            if row==0:ax.set_title(ALIGN[alignment],fontsize=12,color=INK,pad=15)
            if row==5:ax.set_xlabel('Temporada agrícola',fontsize=10,color=MUTED)
    fig.text(.05,.035,'Los huecos son años sin cobertura suficiente; no son ceros. z regional es el promedio de anomalías estandarizadas por píxel, no una pérdida porcentual nacional.',fontsize=9,color=MUTED)
    save(fig,out,'03_series_'+slug(region),dpi,formats)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    root=Path('C:/Users/paola/Tesis/03_Resultados/Agroclima/vigente/rendimiento')
    p.add_argument('--input',type=Path,default=root/'cruce_anual_ONI_MJO_20261020_183145')
    p.add_argument('--output',type=Path)
    p.add_argument('--regions',help='Lista separada por punto y coma; solo limita figuras regionales')
    p.add_argument('--dpi',type=int,default=220)
    p.add_argument('--formats',default='png,svg')
    a=p.parse_args();started=time.perf_counter();formats=a.formats.split(',')
    if not set(formats)<=set(['png','svg']) or a.dpi<100:p.error('Formato/dpi invalido')
    meta=json.loads((a.input/'completed.json').read_text(encoding='utf-8'))
    if meta.get('prueba_parcial'):p.error('La tabla maestra debe estar completa')
    c=sqlite3.connect((a.input/'cruce_rendimiento.sqlite').resolve().as_uri()+'?mode=ro',uri=True)
    # Read the annual regional analysis stored inside the master database: no pooled daily yield.
    t=pd.read_sql_query("SELECT * FROM correlaciones_regionales WHERE variable='pct_dias_afectados'",c)
    s=pd.read_sql_query("SELECT * FROM series_regionales_anuales WHERE variable='pct_dias_afectados'",c);c.close()
    keys=['region','fase','alineacion']
    if t.duplicated(keys).any() or s.duplicated(keys+['temporada']).any():raise ValueError('Claves duplicadas')
    stats=[];details=[]
    print('Analizando influencia de todos los anios y todas las parejas de anios...',flush=True)
    for key,part in s.groupby(keys,sort=False):
        report,rows=influence(part,int(meta.get('min_anios',30)));tags=dict(zip(keys,key));report.update(tags);stats.append(report)
        for row in rows:row.update(tags);details.append(row)
    table=t.merge(pd.DataFrame(stats),on=keys,validate='one_to_one')
    if not np.allclose(table.pearson_r,table.r_recalculado,equal_nan=True,atol=1e-8):raise ValueError('El Pearson guardado no reproduce las series')
    table['ic_incluye_cero']=table.ic95_inferior.le(0)&table.ic95_superior.ge(0)
    table['ic_estimado']=table.ic95_inferior.notna()&table.ic95_superior.notna()
    table['ancho_ic']=table.ic95_superior-table.ic95_inferior
    names=set(table.region);order=[r for r in ORDER if r in names]+sorted(names-set(ORDER))
    regions=a.regions.split(';') if a.regions else order
    if not set(regions)<=names:p.error('Region desconocida')
    out=a.output.resolve() if a.output else root/('graficos_tabla_maestra_'+time.strftime('%Y%m%d_%H%M%S'))
    out.mkdir(parents=True,exist_ok=False)
    table.to_csv(out/'revision_amenaza_rendimiento.csv',index=False,encoding='utf-8-sig',na_rep='')
    pd.DataFrame(details).to_csv(out/'influencia_cada_anio.csv',index=False,encoding='utf-8-sig',na_rep='')
    s.to_csv(out/'datos_de_las_figuras.csv',index=False,encoding='utf-8-sig',na_rep='')
    compare=table[table.alineacion.eq('same-label')].merge(table[table.alineacion.eq('maturity-year')],on=['region','fase','variable'],suffixes=('_temporada','_fin_mat'),validate='one_to_one')
    compare['diferencia_r']=compare.pearson_r_fin_mat-compare.pearson_r_temporada
    compare.to_csv(out/'comparacion_correspondencia_anual.csv',index=False,encoding='utf-8-sig',na_rep='')
    plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none','axes.titleweight':'normal'})
    finite=s.z_rendimiento_medio.dropna().to_numpy();ylim=max(1.,float(np.max(np.abs(finite)))*1.15) if len(finite) else 1.
    for alignment in ALIGN:overview(table,order,alignment,out,a.dpi,formats)
    for region in regions:
        regional_scatter(region,table,s,out,a.dpi,formats,ylim)
        regional_series(region,s,out,a.dpi,formats,ylim)
        print(f'GRAFICOS: {region}; dispersiones y series completas.',flush=True)
    (out/'LEEME.txt').write_text('Revision grafica de la tabla maestra anual.\n01: Pearson regional e IC por fase, para cada correspondencia de anio. 02: dispersiones, un punto por temporada. 03: series anuales, con ejes independientes indicados.\nLa amenaza principal es porcentaje de dias afectados; calor en EST-FIL, lluvia >10 mm en MAT. No son probabilidades de perdida. Rendimiento z proviene del archivo ya detrendido.\nCada punto regional promedia los mismos pares pixel-anio validos para exposicion y rendimiento, con cobertura minima 95% del soporte elegible. La composicion puede variar y queda registrada en datos_de_las_figuras.csv.\nLos IC originales usan 2000 temporadas compartidas, no pixeles. La influencia retira cada anio y todas las parejas de anios; exige al menos 30 pares restantes. Los cambios de signo son descriptivos y no pruebas adicionales de significancia. No son una validacion fuera de muestra.\nSe muestran todas las regiones, no solo las asociaciones fuertes. Las etiquetas de dispersion identifican los dos anios que mas cambian r al retirarlos, no necesariamente los de mayor perdida.\nLas dos correspondencias temporales se conservan sin escoger por r. La publicacion GDHY define el anio como anio de cosecha: https://www.nature.com/articles/s41597-020-0433-7 . El fin de MAT es una aproximacion al anio de cosecha; queda por verificar su correspondencia con el calendario y la temporada GDHY del archivo local.\nRegiones provisionales. Resultados exploratorios, sin ajuste por autocorrelacion o multiplicidad. Una correlacion no demuestra impacto causal ni basta para fijar un disparador de seguro: faltan validacion temporal independiente y evaluacion de desajustes entre indice y perdidas. No se calibran pagos ni primas en este script.\nSolo completed.json confirma finalizacion.\n',encoding='utf-8')
    report=dict(figuras=2+2*len(regions),formatos=formats,regiones=regions,filas_revision=len(table),
      series_temporadas=len(s),comparaciones_un_anio=len(details),limite_z_comun=ylim,
      entrada=str(a.input),fuentes_sha256={str(a.input/'completed.json'):sha(a.input/'completed.json'),str(Path(__file__).resolve()):sha(Path(__file__))},
      graficos_parciales=bool(a.regions),segundos=round(time.perf_counter()-started,2))
    (out/'completed.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(f'COMPLETO: {out}',flush=True)


if __name__=='__main__':main()
