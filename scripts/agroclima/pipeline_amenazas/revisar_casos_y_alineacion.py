"""Dos pasos locales: contraste historico descriptivo y sensibilidad al anio de rendimiento."""
import argparse
import gzip
import json
from pathlib import Path
import sqlite3
import time
import numpy as np
import pandas as pd
from rutas_resultados_oni import resultados_oni
from contrastes_frecuencias_oni import sha

CASES=[
 dict(caso='EEUU_2012',pais='United States of America',anio_evento=2012,inicio_evento='2012-06-01',fin_evento='2012-08-31',
      evidencia='Calor y sequia durante reproduccion; USDA informo 123.4 bushels/acre de rendimiento en cosecha, menor desde 1995.',
      fuente='USDA NASS, Crop Production, 10 agosto 2012; USDA ERS, 20 mayo 2013',
      url='https://www.nass.usda.gov/Publications/Todays_Reports/reports/crop0812.pdf',
      url_resultado='https://www.ers.usda.gov/amber-waves/2013/june/crop-outlook-reflects-near-term-prices-and-longer-term-market-trends',
      limite='El reporte destaca Corn Belt; se extrae toda la seleccion de pixeles de EEUU, no una mascara validada del Corn Belt. Periodo junio-agosto: ventana operativa amplia, no fecha exacta de cada episodio.'),
 dict(caso='Francia_2003',pais='France',anio_evento=2003,inicio_evento='2003-06-01',fin_evento='2003-08-31',
      evidencia='Estudio JRC: rendimiento nacional de maiz aproximadamente 1.5 t/ha menor que promedio 2000-2006; calor y sequia con amortiguacion parcial por riego.',
      fuente='Van der Velde, Wriedt y Bouraoui; DOI 10.1016/j.agee.2009.08.017',
      url='https://publications.jrc.ec.europa.eu/repository/handle/JRC53947',
      url_resultado='https://publications.jrc.ec.europa.eu/repository/handle/JRC53947',
      limite='La cifra nacional incluye manejo y riego distintos de nuestra seleccion; la anomalia z no equivale a t/ha. Junio-agosto es ventana operativa amplia.'),
 dict(caso='Zambia_2015_2016',pais='Zambia',anio_evento=2016,inicio_evento='2015-10-01',fin_evento='2016-04-30',
      evidencia='Estudio FAO de campania 2015/2016: hogares afectados por sequia tuvieron rendimiento de maiz alrededor de 20% menor, condicionado al modelo.',
      fuente='Alfani et al., FAO Agricultural Development Economics Working Paper 19-02, 2019',
      url='https://www.fao.org/agrifood-economics/publications/detail/en/c/1180723/',
      url_resultado='https://www.fao.org/agrifood-economics/publications/detail/en/c/1180723/',
      limite='Encuesta de hogares afectados, no perdida nacional del 20%. Nuestra seleccion solo tiene pocos pixeles. Octubre-abril es ventana operativa de revision de la campania; no valida el calendario GDHY.')]


def compare_alignments(table):
    keys=['region','fase','variable']
    left=table[table.alineacion.eq('same-label')].drop(columns='alineacion')
    right=table[table.alineacion.eq('maturity-year')].drop(columns='alineacion')
    out=left.merge(right,on=keys,suffixes=('_same_label','_maturity_year'),how='outer',validate='one_to_one')
    finite=np.isfinite(out.pearson_r_same_label)&np.isfinite(out.pearson_r_maturity_year)
    out['cambio_r_maturity_menos_same']=out.pearson_r_maturity_year-out.pearson_r_same_label
    out['mismo_signo']=pd.Series(pd.NA,index=out.index,dtype='boolean')
    out.loc[finite,'mismo_signo']=np.sign(out.loc[finite,'pearson_r_same_label']).to_numpy()==np.sign(out.loc[finite,'pearson_r_maturity_year']).to_numpy()
    for suffix in ['same_label','maturity_year']:
        lo=out['ic95_inferior_'+suffix];hi=out['ic95_superior_'+suffix]
        out['lectura_ic_'+suffix]=np.select([lo.isna()|hi.isna(),lo.gt(0),hi.lt(0)],['no_estimado','positivo','negativo'],default='incluye_cero')
    out['misma_lectura_ic']=out.lectura_ic_same_label.eq(out.lectura_ic_maturity_year)
    return out


def case_summary(d,case):
    keys=['fase','alineacion','anio_rendimiento']
    good=d[d.par_amenaza_rendimiento_valido.eq(1)].copy()
    good['es_negativo']=good.z_rendimiento.lt(0).astype(float)
    start=pd.to_datetime(good.inicio);end=pd.to_datetime(good.fin)
    good['solapa_evento']=start.le(pd.Timestamp(case['fin_evento']))&end.ge(pd.Timestamp(case['inicio_evento']))
    good['oni_calido']=good.cat_oni.eq('calido').astype(float)
    good['oni_frio']=good.cat_oni.eq('frio').astype(float)
    good['oni_neutral']=good.cat_oni.eq('neutral').astype(float)
    group=good.groupby(['pixel_id','fase','alineacion'])
    # Percentiles are within the same pixel, phase and alignment, including tied zeros.
    good['percentil_exposicion_pixel']=100*group.pct_dias_afectados.rank(method='average',pct=True)
    good['percentil_rendimiento_pixel']=100*group.z_rendimiento.rank(method='average',pct=True)
    result=good.groupby(keys).agg(pixeles_pareados=('pixel_id','nunique'),observaciones=('pixel_id','size'),
      z_rendimiento_medio=('z_rendimiento','mean'),z_rendimiento_mediano=('z_rendimiento','median'),
      fraccion_pixeles_z_negativo=('es_negativo','mean'),pct_dias_afectados_medio=('pct_dias_afectados','mean'),
      conteo_medio=('conteo_original','mean'),oni_ventana_medio=('oni_ventana','mean'),
      fraccion_pixeles_oni_calido=('oni_calido','mean'),fraccion_pixeles_oni_frio=('oni_frio','mean'),
      fraccion_pixeles_oni_neutral=('oni_neutral','mean'),fraccion_dias_mjo_activa_media=('fraccion_dias_mjo_activa','mean'),
      percentil_exposicion_pixel_mediano=('percentil_exposicion_pixel','median'),
      percentil_rendimiento_pixel_mediano=('percentil_rendimiento_pixel','median'),
      fraccion_ventanas_solapan_evento=('solapa_evento','mean'),inicio_min=('inicio','min'),fin_max=('fin','max')).reset_index()
    result['caso']=case['caso'];result['pais']=case['pais'];result['anio_evento']=case['anio_evento']
    result['es_anio_evento']=result.anio_rendimiento.eq(case['anio_evento'])
    result['es_vecino_dos_anios']=result.anio_rendimiento.sub(case['anio_evento']).abs().between(1,2)
    result['pocos_pixeles']=result.pixeles_pareados.lt(30)
    # Pair each event observation to its own pixel history, avoiding a changing baseline.
    baseline=good[good.anio_rendimiento.ne(case['anio_evento'])].groupby(['pixel_id','fase','alineacion']).agg(
      z_otras_temporadas=('z_rendimiento','mean'),pct_afectados_otras_temporadas=('pct_dias_afectados','mean'),n_otras_temporadas=('z_rendimiento','size')).reset_index()
    event=good[good.anio_rendimiento.eq(case['anio_evento'])].merge(baseline,on=['pixel_id','fase','alineacion'],how='left',validate='many_to_one')
    event['diferencia_z_otras_temporadas']=event.z_rendimiento-event.z_otras_temporadas
    event['diferencia_exposicion_pp_otras_temporadas']=event.pct_dias_afectados-event.pct_afectados_otras_temporadas
    event['caso']=case['caso'];event['pais']=case['pais']
    contrast=event.groupby(['caso','pais','fase','alineacion']).agg(
      observaciones_evento=('pixel_id','size'),pixeles_evento=('pixel_id','nunique'),
      z_evento=('z_rendimiento','mean'),z_otras_temporadas=('z_otras_temporadas','mean'),
      diferencia_z=('diferencia_z_otras_temporadas','mean'),
      pct_afectados_evento=('pct_dias_afectados','mean'),pct_afectados_otras_temporadas=('pct_afectados_otras_temporadas','mean'),
      diferencia_exposicion_pp=('diferencia_exposicion_pp_otras_temporadas','mean'),
      fraccion_ventanas_solapan_evento=('solapa_evento','mean')).reset_index()
    contrast['pocos_pixeles']=contrast.pixeles_evento.lt(30)
    return result,event,contrast


def main():
    p=argparse.ArgumentParser(description=__doc__)
    root=Path('C:/Users/paola/Tesis')
    p.add_argument('--input',type=Path,default=root/'03_Resultados/Agroclima/vigente/rendimiento/cruce_anual_ONI_MJO_20261020_183145')
    p.add_argument('--output',type=Path)
    p.add_argument('--countries',type=Path,default=resultados_oni()/'propuesta_regiones_geograficas_20261020/regiones_propuestas_para_revisar.csv')
    a=p.parse_args();start=time.perf_counter()
    meta=json.loads((a.input/'completed.json').read_text(encoding='utf-8'))
    if meta.get('prueba_parcial'):raise ValueError('Cruce de origen parcial')
    out=a.output.resolve() if a.output else a.input.parent/('revision_casos_alineacion_'+time.strftime('%Y%m%d_%H%M%S'))
    out.mkdir(parents=True,exist_ok=False)
    c=sqlite3.connect((a.input/'cruce_rendimiento.sqlite').resolve().as_uri()+'?mode=ro',uri=True)
    dest=sqlite3.connect(out/'revision.pending.sqlite')
    cases=pd.DataFrame(CASES);cases.to_csv(out/'eventos_y_fuentes_web.csv',index=False,encoding='utf-8-sig')
    countries=pd.read_csv(a.countries,usecols=['pixel_id','pais_referencia'])
    if countries.pixel_id.duplicated().any():raise ValueError('Asignacion de pais duplicada')
    contexts=[];events=[];contrasts=[];n_pairs=0
    print('PASO 1/2: extrayendo EEUU 2012, Francia 2003 y Zambia 2015/2016...',flush=True)
    for case in CASES:
        ids=countries.loc[countries.pais_referencia.eq(case['pais']),'pixel_id'].astype(int).tolist()
        if not ids:raise ValueError('Pais sin pixeles: '+case['pais'])
        frames=[]
        # Bounded batches avoid SQLite parameter limits and read all years, not only disasters.
        for offset in range(0,len(ids),500):
            batch=ids[offset:offset+500]
            frames.append(pd.read_sql_query('SELECT * FROM pares_anuales WHERE pixel_id IN ('+','.join('?' for _ in batch)+')',c,params=batch))
        d=pd.concat(frames,ignore_index=True)
        if d.duplicated(['pixel_id','temporada','fase','alineacion']).any():raise ValueError('Pares duplicados')
        if len(d)!=len(ids)*36*6*2:raise ValueError('Extraccion incompleta')
        context,event,contrast=case_summary(d,case)
        contexts.append(context);events.append(event);contrasts.append(contrast)
        with gzip.open(out/(case['caso']+'_historia_completa.csv.gz'),'wt',encoding='utf-8',newline='') as f:d.to_csv(f,index=False,na_rep='')
        d['caso']=case['caso'];d.to_sql('pares_casos',dest,index=False,if_exists='append',chunksize=20000)
        n_pairs+=len(d)
        print(f"{case['caso']}: {len(ids):,} pixeles; {len(d):,} pares anuales; eventos y anios vecinos extraidos.",flush=True)
    print('PASO 2/2: comparando alineaciones por region y fase, sin seleccionar ganadora...',flush=True)
    correlations=pd.read_csv(a.input/'correlaciones_regionales.csv')
    comparison=compare_alignments(correlations)
    if len(comparison)!=correlations[['region','fase','variable']].drop_duplicates().shape[0]:raise ValueError('Comparacion incompleta')
    tables={'eventos_y_fuentes_web':cases,'historia_anual_casos':pd.concat(contexts,ignore_index=True),
      'detalle_pixeles_evento':pd.concat(events,ignore_index=True),'evento_vs_otras_temporadas':pd.concat(contrasts,ignore_index=True),
      'sensibilidad_alineacion':comparison,'auditoria_correspondencia_anual':pd.read_csv(a.input/'auditoria_correspondencia_anual.csv')}
    tables['evento_y_vecinos']=tables['historia_anual_casos'].loc[lambda d:d.es_anio_evento|d.es_vecino_dos_anios].copy()
    tables['revision_principal_regiones']=comparison[comparison.variable.eq('pct_dias_afectados')].copy()
    for name,df in tables.items():df.to_sql(name,dest,index=False,chunksize=10000);df.to_csv(out/(name+'.csv'),index=False,encoding='utf-8-sig',na_rep='')
    dest.execute('CREATE UNIQUE INDEX casos_pk ON pares_casos(caso,pixel_id,temporada,fase,alineacion)')
    if dest.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('SQLite no integro')
    dest.commit();dest.close();c.close();(out/'revision.pending.sqlite').rename(out/'revision.sqlite')
    (out/'LEEME.txt').write_text('DOS PASOS: 1) casos historicos con fuentes web; 2) sensibilidad de asociaciones al anio asignado al rendimiento.\nSon contrastes descriptivos, no validacion causal ni prueba independiente de GDHY. Las fuentes externas pueden compartir estadisticas nacionales con GDHY; su independencia no esta acreditada.\nHistoria completa de todos los anios de los tres paises para no mostrar solo desastres. Evento y vecinos identifica anio del rendimiento +/-2. En Zambia se incluye 2015/2016 mediante anio de rendimiento 2016 y se publica tambien el contexto de 2015.\nEl pais se asigna por centro del pixel con el mapa provisional existente. EEUU no es una mascara exclusiva del Corn Belt. Zambia tiene pocos pixeles; marca <30.\nPeriodos de evento son ventanas operativas amplias para revisar solapamiento, no fechas exactas de episodios ni calendarios validados.\nResumen nacional: medias con igual peso de pixeles disponibles, no ponderadas por superficie cultivada. El rendimiento z no es porcentaje de perdida ni t/ha. Las cifras web no son directamente equivalentes. Se registra cantidad de pixeles y fechas.\nEvento vs otras temporadas usa la historia del MISMO pixel/fase/alineacion, excluyendo el anio del evento de su referencia. Sin IC espacial ni pixeles tratados como replicas temporales.\nLos casos incluyen sequia, pero la matriz actual solo mide calor y lluvia intensa en MAT; no mide deficit hidrico directamente. No atribuimos los eventos a MJO.\nSensibilidad compara r, IC y anios en ambos escenarios sin escoger por mayor correlacion. Signos o IC coincidentes no verifican la convencion documental del anio de GDHY.\nFuentes web consultadas en esta conversacion; los enlaces y el resumen de evidencia quedan guardados. No se descargan ni reinterpretan como datos anuales del modelo.\nSolo completed.json confirma finalizacion.\n',encoding='utf-8')
    report=dict(pasos_completos=2,casos=len(CASES),filas_pares_extraidos=n_pairs,
      filas_tablas={k:len(v) for k,v in tables.items()},alineacion_documental_verificada=False,
      fuentes_sha256={str(a.input/'completed.json'):sha(a.input/'completed.json'),str(a.countries):sha(a.countries),str(Path(__file__).resolve()):sha(Path(__file__))},
      segundos=round(time.perf_counter()-start,2))
    (out/'completed.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True);print(f'COMPLETO: {out}',flush=True)


if __name__=='__main__':main()
