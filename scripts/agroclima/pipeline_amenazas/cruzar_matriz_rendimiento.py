"""Cruce anual local de amenazas, ONI, exposicion MJO y rendimiento ya detrendido."""
import argparse
import gzip
import json
from pathlib import Path
import sqlite3
import time
import numpy as np
import pandas as pd
from maize_amenazas_rendimiento import read_yield
from contrastes_frecuencias_oni import season_weights,sha
from rutas_resultados_oni import resultados_oni

PHASES=['EST','VEG','FLO','REP','FIL','MAT']
YEARS=np.arange(1981,2017)


def correlations(x,y):
    """One correlation per row, pairwise finite observations; no pooled pixel-years."""
    good=np.isfinite(x)&np.isfinite(y);n=good.sum(axis=1)
    xx=np.where(good,x,0.);yy=np.where(good,y,0.)
    dx=xx.sum(axis=1)/np.maximum(n,1);dy=yy.sum(axis=1)/np.maximum(n,1)
    xc=np.where(good,x-dx[:,None],0.);yc=np.where(good,y-dy[:,None],0.)
    den=np.sqrt((xc*xc).sum(axis=1)*(yc*yc).sum(axis=1))
    r=np.divide((xc*yc).sum(axis=1),den,out=np.full(len(x),np.nan),where=(den>1e-12)&(n>=3))
    return np.clip(r,-1,1),n


def boot_r(x,y,w,min_years):
    good=np.isfinite(x)&np.isfinite(y);point,n=correlations(x[None,:],y[None,:])
    if n[0]<min_years or not np.isfinite(point[0]):return float('nan'),float('nan'),float('nan'),0
    wg=w*good;count=wg.sum(axis=1)
    xx=np.where(good,x,0.);yy=np.where(good,y,0.)
    sx=wg@xx;sy=wg@yy
    cov=wg@(xx*yy)-sx*sy/np.maximum(count,1)
    vx=np.maximum(wg@(xx*xx)-sx*sx/np.maximum(count,1),0)
    vy=np.maximum(wg@(yy*yy)-sy*sy/np.maximum(count,1),0)
    den=np.sqrt(vx*vy);sample=np.divide(cov,den,out=np.full(len(w),np.nan),where=(den>1e-12)&(count>=3))
    valid=sample[np.isfinite(sample)];lo=hi=np.nan
    if len(valid)>=np.ceil(.95*len(w)):lo,hi=np.quantile(valid,[.025,.975])
    return float(point[0]),float(lo),float(hi),len(valid)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,default=resultados_oni()/'matriz_integrada_ONI_MJO_20261020_163424')
    p.add_argument('--output',type=Path)
    p.add_argument('--bootstrap',type=int,default=2000)
    p.add_argument('--seed',type=int,default=20261019)
    p.add_argument('--min-years',type=int,default=30)
    p.add_argument('--min-regional-coverage',type=float,default=.95)
    p.add_argument('--phases',default=','.join(PHASES))
    a=p.parse_args();start=time.perf_counter();phases=a.phases.split(',')
    if a.bootstrap<200 or not 3<=a.min_years<=36 or not 0<a.min_regional_coverage<=1 or not set(phases)<=set(PHASES):p.error('Parametros invalidos')
    meta=json.loads((a.input/'completed.json').read_text(encoding='utf-8'))
    if meta.get('prueba_parcial') or meta.get('discrepancias_anuales')!=0:p.error('Se necesita la matriz integrada completa y validada')
    root=Path('C:/Users/paola/Tesis')
    yp=root/'02_Procesados/GDHY_detrend/maize_yield_1981_2016_DETREND_clean.nc'
    cp=root/'02_Procesados/Pixeles_correlacion_vigentes/pixeles_maize.csv'
    coords=pd.read_csv(cp).sort_values('h5_index').reset_index(drop=True)
    years,values,units=read_yield(yp,coords)
    valid=np.isfinite(values);nvalid=valid.sum(axis=1);mean=np.nanmean(values,axis=1);sd=np.nanstd(values,axis=1,ddof=1)
    z=np.divide(values-mean[:,None],sd[:,None],out=np.full_like(values,np.nan),where=(sd[:,None]>1e-12)&(nvalid[:,None]>=a.min_years))
    yield_table=pd.DataFrame(dict(pixel_id=np.repeat(coords.pixel_id,len(years)),anio_rendimiento=np.tile(years,len(coords)),
      rendimiento_sin_tendencia=values.ravel(),z_rendimiento=z.ravel(),anios_rendimiento_disponibles=np.repeat(nvalid,len(years))))
    out=a.output.resolve() if a.output else root/'03_Resultados/Agroclima/vigente/rendimiento'/('cruce_anual_ONI_MJO_'+time.strftime('%Y%m%d_%H%M%S'))
    out.mkdir(parents=True,exist_ok=False)
    c=sqlite3.connect((a.input/'matriz_integrada.sqlite').resolve().as_uri()+'?mode=ro',uri=True)
    dest=sqlite3.connect(out/'cruce_rendimiento.pending.sqlite')
    yield_table.to_sql('rendimiento',dest,index=False,chunksize=20000)
    dest.execute('CREATE UNIQUE INDEX rendimiento_pk ON rendimiento(pixel_id,anio_rendimiento)')
    # Maturity year is only a sensitivity proxy, not a verified GDHY harvest convention.
    maturity=pd.read_sql_query("SELECT pixel_id,temporada,CAST(substr(fin,1,4) AS INTEGER) AS anio_fin_mat FROM anual WHERE fase='MAT'",c)
    mapping=pd.read_sql_query('SELECT * FROM regiones',c)
    weights=season_weights(a.bootstrap,a.seed)
    np.savez_compressed(out/'bootstrap_temporadas.npz',temporadas=YEARS,pesos=weights.astype(np.uint8),semilla=a.seed)
    summaries=[];audit=[];series=[];pixel_results=[];pair_rows=0
    print(f'Rendimiento: {len(coords):,} pixeles; {int((nvalid==35).sum()):,} con 35 anios; dos correspondencias temporales.',flush=True)
    for phase in phases:
        print(f'{phase}: leyendo matriz anual y resumiendo exposicion MJO...',flush=True)
        annual=pd.read_sql_query('SELECT * FROM anual WHERE fase=?',c,params=(phase,))
        annual=annual.merge(maturity,on=['pixel_id','temporada'],validate='one_to_one').merge(mapping,on='pixel_id',how='left',validate='many_to_one')
        mj=pd.read_sql_query('''SELECT pixel_id,temporada,estado_mjo,SUM(dias_par_valido) AS dias_estado
          FROM mjo_mensual WHERE fase=? GROUP BY pixel_id,temporada,estado_mjo''',c,params=(phase,))
        piv=mj.pivot(index=['pixel_id','temporada'],columns='estado_mjo',values='dias_estado').fillna(0)
        # The state table has already retained days with missing indices separately.
        for state in ['debil']+[str(i) for i in range(1,9)]:
            if state not in piv:piv[state]=0
        total=piv[['debil']+[str(i) for i in range(1,9)]].sum(axis=1)
        mjannual=pd.DataFrame(index=piv.index);mjannual['dias_par_oni_mjo_valido']=total
        for state in ['debil']+[str(i) for i in range(1,9)]:mjannual['fraccion_dias_mjo_'+state]=piv[state]/total.replace(0,np.nan)
        mjannual['fraccion_dias_mjo_activa']=piv[[str(i) for i in range(1,9)]].sum(axis=1)/total.replace(0,np.nan)
        annual=annual.merge(mjannual.reset_index(),on=['pixel_id','temporada'],validate='one_to_one')
        annual['cobertura_par_oni_mjo']=annual.dias_par_oni_mjo_valido/annual.dias_ventana
        for alignment in ['same-label','maturity-year']:
            d=annual.copy();d['alineacion']=alignment
            d['anio_rendimiento']=d.temporada if alignment=='same-label' else d.anio_fin_mat
            d=d.merge(yield_table,on=['pixel_id','anio_rendimiento'],how='left',validate='many_to_one')
            d['par_amenaza_rendimiento_valido']=d.par_frecuencia_oni_valido.eq(1)&np.isfinite(d.pct_dias_afectados)&np.isfinite(d.z_rendimiento)
            if d.duplicated(['pixel_id','temporada','fase','alineacion']).any():raise ValueError('Cruce anual duplicado')
            d.to_sql('pares_anuales',dest,index=False,if_exists='append',chunksize=20000)
            with gzip.open(out/f'pares_{phase}_{alignment}.csv.gz','wt',encoding='utf-8',newline='') as f:d.to_csv(f,index=False,na_rep='')
            pair_rows+=len(d)
            audit.append(dict(fase=phase,alineacion=alignment,filas=len(d),pares_validos=int(d.par_amenaza_rendimiento_valido.sum()),
              anios_no_disponibles=int((~d.anio_rendimiento.isin(years)).sum()),pares_pixel_35_anios=int((d.par_amenaza_rendimiento_valido & d.anios_rendimiento_disponibles.eq(35)).sum())))
            for metric in ['pct_dias_afectados','conteo_original','oni_ventana']:
                x=d.pivot(index='pixel_id',columns='temporada',values=metric).reindex(columns=YEARS)
                y=d.pivot(index='pixel_id',columns='temporada',values='z_rendimiento').reindex(index=x.index,columns=YEARS)
                ok=d.pivot(index='pixel_id',columns='temporada',values='par_frecuencia_oni_valido').reindex(index=x.index,columns=YEARS).eq(1).to_numpy()
                xx=np.where(ok,x.to_numpy(float),np.nan);yy=y.to_numpy(float)
                rr,nn=correlations(xx,yy);rr[nn<a.min_years]=np.nan
                pixel_results.extend(dict(pixel_id=int(pid),fase=phase,alineacion=alignment,variable=metric,pearson_r=float(r),pares_validos=int(n),
                    estado='estimado' if np.isfinite(r) else 'insuficiente_o_constante') for pid,r,n in zip(x.index,rr,nn))
                reg=d[['pixel_id','region']].drop_duplicates().set_index('pixel_id').reindex(x.index).region
                for region in reg.dropna().unique():
                    ids=np.flatnonzero(reg.eq(region).to_numpy() & (nn>=a.min_years))
                    if len(ids):
                        vx=xx[ids];vy=yy[ids];good=np.isfinite(vx)&np.isfinite(vy);counts=good.sum(axis=0)
                        sx=np.divide(np.where(good,vx,0).sum(axis=0),counts,out=np.full(36,np.nan),where=counts>0)
                        sy=np.divide(np.where(good,vy,0).sum(axis=0),counts,out=np.full(36,np.nan),where=counts>0)
                        enough=counts>=np.ceil(a.min_regional_coverage*len(ids));sx[~enough]=np.nan;sy[~enough]=np.nan
                    else:counts=np.zeros(36,int);sx=np.full(36,np.nan);sy=sx.copy()
                    r,lo,hi,B=boot_r(sx,sy,weights,a.min_years)
                    summaries.append(dict(region=region,fase=phase,alineacion=alignment,variable=metric,principal=metric=='pct_dias_afectados',
                      pixeles_elegibles=len(ids),pocos_pixeles=len(ids)<30,temporadas_validas=int((np.isfinite(sx)&np.isfinite(sy)).sum()),
                      pearson_r=r,ic95_inferior=lo,ic95_superior=hi,replicas_estimables=B,
                      estado='estimado' if np.isfinite(lo) else 'sin_ic_estimable',cobertura_regional_minima=a.min_regional_coverage))
                    series.extend(dict(region=region,fase=phase,alineacion=alignment,variable=metric,temporada=int(t),
                      exposicion_media=float(u),z_rendimiento_medio=float(v),pixeles_pareados=int(n),pixeles_elegibles=len(ids)) for t,u,v,n in zip(YEARS,sx,sy,counts))
            print(f'{phase} / {alignment}: matriz anual, Pearson por pixel y bootstrap regional completos.',flush=True)
    tables={'correlaciones_regionales':pd.DataFrame(summaries),'series_regionales_anuales':pd.DataFrame(series),
      'pearson_por_pixel':pd.DataFrame(pixel_results),'auditoria_correspondencia_anual':pd.DataFrame(audit)}
    for name,df in tables.items():df.to_sql(name,dest,index=False,chunksize=20000);df.to_csv(out/(name+'.csv'),index=False,encoding='utf-8-sig',na_rep='')
    dest.execute('CREATE UNIQUE INDEX pares_pk ON pares_anuales(pixel_id,temporada,fase,alineacion)')
    if dest.execute('SELECT COUNT(*) FROM pares_anuales').fetchone()[0]!=len(coords)*36*len(phases)*2:raise ValueError('Matriz anual incompleta')
    if dest.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('SQLite no integro')
    dest.commit();dest.close();c.close();(out/'cruce_rendimiento.pending.sqlite').rename(out/'cruce_rendimiento.sqlite')
    report=dict(filas_pares_anuales=pair_rows,pixeles=len(coords),pixeles_con_35_anios=int((nvalid==35).sum()),
      bootstrap=a.bootstrap,semilla=a.seed,min_anios=a.min_years,prueba_parcial=set(phases)!=set(PHASES),
      alineacion_documental_verificada=False,escenarios=['same-label','maturity-year'],unidad_archivo_rendimiento=units,
      rendimiento_ya_detrendido=True,z='centrado y desviacion estandar muestral por pixel en anios disponibles; no se vuelve a quitar tendencia',
      regionalizacion_provisional=meta.get('regionalizacion_provisional',True),
      fuentes_sha256={str(yp):sha(yp),str(cp):sha(cp),str(a.input/'completed.json'):sha(a.input/'completed.json'),str(Path(__file__).resolve()):sha(Path(__file__))},
      segundos=round(time.perf_counter()-start,2))
    (out/'LEEME.txt').write_text('Una fila de pares_anuales = pixel x temporada x fase x escenario de correspondencia con rendimiento. Sin replicas diarias del rendimiento.\nSe usan los conteos corregidos y el rendimiento del archivo ya detrendido; z usa desviacion muestral por pixel. Minimo 30 anios: los pixeles con 35 son validos. Valores negativos detrendidos se conservan.\nDos escenarios pendientes de verificar documentalmente: same-label y maturity-year (fin de MAT, aproximacion de cosecha). No escoger el escenario por mayor correlacion.\nPearson principal: porcentaje de dias afectados frente a z. Conteos y ONI continuo son analisis separados. Pearson por pixel es puntual, sin IC.\nCorrelacion regional: un punto por temporada; cada punto promedia solo pares pixel-anio validos, con igual peso por pixel. Se exige >=95% del soporte de pixeles con >=30 pares anuales. La composicion puede variar hasta 5%; las cantidades por temporada estan guardadas. Los IC remuestrean 36 temporadas compartidas, nunca pixeles. Son exploratorios y no corrigen autocorrelacion ni multiplicidad.\nExposicion MJO anual: fraccion de dias por estado entre los dias con par ONI-MJO valido; se informa cobertura. Se agrega para continuar, no se ajusta aun un modelo de rendimiento con 8 fases MJO.\nLos resultados regionales usan regiones provisionales. Sin modelos causales, seleccion de mejor fase ni graficos en esta ejecucion.\nSolo completed.json confirma finalizacion; prueba_parcial debe ser false.\n',encoding='utf-8')
    (out/'completed.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True);print(f'COMPLETO: {out}',flush=True)


if __name__=='__main__':main()
