"""Consolidacion local y auditable de matriz anual, MJO mensual y contexto regional."""
import argparse
import json
import sqlite3
import time
from pathlib import Path
import numpy as np
import pandas as pd
from rutas_resultados_oni import resultados_oni
from contrastes_frecuencias_oni import sha

KEYS=['pixel_id','temporada','fase','anio_calendario','mes','cat_oni_mes','estado_mjo']
SUMS=['dias_observados','dias_clima_validos','dias_par_valido','dias_afectados_total','dias_afectados_par_valido','ocurrencias_total','ocurrencias_par_valido']


def aggregate_chunk(d):
    d=d.rename(columns={'fase_cultivo':'fase'})
    d['anio_calendario']=pd.to_numeric(d.fecha.str[:4],errors='raise')
    valid=d.par_clima_oni_mjo_valido.astype(str).str.lower().isin(['true','1'])
    climate=np.isfinite(d.fraccion_afectada)
    if (valid & (~climate | d.cat_oni_mes.isna() | d.estado_mjo.isna())).any():
        raise ValueError('Par valido sin clima o indices')
    if (d.fraccion_afectada.dropna().lt(-1e-9)|d.fraccion_afectada.dropna().gt(1+1e-9)).any():
        raise ValueError('Fraccion afectada fuera de [0,1]')
    d['dias_observados']=1
    d['dias_clima_validos']=climate.astype(int)
    d['dias_par_valido']=valid.astype(int)
    d['dias_afectados_total']=d.fraccion_afectada
    d['dias_afectados_par_valido']=d.fraccion_afectada.where(valid,0)
    d['ocurrencias_total']=d.ocurrencias_calificadas_dia
    d['ocurrencias_par_valido']=d.ocurrencias_calificadas_dia.where(valid,0)
    # min_count preserves missing values; missing exposure is never an observed zero.
    return d.groupby(KEYS,dropna=False,sort=False)[SUMS].sum(min_count=1).reset_index()


def export_query(c,query,path):
    first=True
    for part in pd.read_sql_query(query,c,chunksize=100000):
        part.to_csv(path,index=False,mode='w' if first else 'a',header=first,encoding='utf-8-sig' if first else 'utf-8',na_rep='')
        first=False


def main():
    p=argparse.ArgumentParser(description=__doc__)
    base=resultados_oni()
    p.add_argument('--daily',type=Path,default=base/'tabla_B_MJO_20261020_102404')
    p.add_argument('--regional',type=Path,default=base/'ONI_regional_maiz_contexto_20261020_162635')
    p.add_argument('--matrix',type=Path,default=base/'matriz_frecuencias_ONI_corregida_20261019_165114/matriz_frecuencias_ONI.sqlite')
    p.add_argument('--output',type=Path)
    p.add_argument('--max-partitions',type=int,help='Solo para prueba: no produce una matriz completa')
    a=p.parse_args();start=time.perf_counter()
    daily_meta=json.loads((a.daily/'completed.json').read_text(encoding='utf-8'))
    regional_meta=json.loads((a.regional/'completed.json').read_text(encoding='utf-8'))
    if daily_meta.get('piloto') or regional_meta.get('prueba_parcial'):p.error('Las fuentes deben ser completas')
    if daily_meta.get('discrepancias_matriz_anual')!=0:p.error('La tabla diaria registra discrepancias')
    for source_meta in [daily_meta,regional_meta]:
        expected=source_meta.get('fuentes_sha256',{}).get(str(a.matrix.resolve()))
        if expected and expected!=sha(a.matrix):raise ValueError('Las fuentes no usan la misma matriz anual')
    files=sorted(daily_meta['filas_por_archivo'])
    if a.max_partitions:
        if a.max_partitions<1:p.error('max-partitions debe ser positivo')
        files=files[:a.max_partitions]
    out=a.output.resolve() if a.output else base/('matriz_integrada_ONI_MJO_'+time.strftime('%Y%m%d_%H%M%S'))
    out.mkdir(parents=True,exist_ok=False)
    pending=out/'matriz_integrada.pending.sqlite';c=sqlite3.connect(pending)
    c.execute('PRAGMA journal_mode=DELETE');c.execute('PRAGMA temp_store=FILE')
    src=sqlite3.connect(a.matrix.resolve().as_uri()+'?mode=ro',uri=True)
    print('Copiando matriz anual y contexto regional...',flush=True)
    for part in pd.read_sql_query('SELECT * FROM matriz',src,chunksize=100000):
        part.to_sql('anual',c,if_exists='append',index=False)
    src.close()
    mapping=pd.read_csv(a.regional/'regiones_utilizadas.csv',usecols=['pixel_id','region'])
    if mapping.pixel_id.duplicated().any():raise ValueError('Regiones solapadas')
    mapping.to_sql('regiones',c,index=False)
    pd.read_csv(a.regional/'tabla_completa_figuras.csv').to_sql('contexto_regional_oni',c,index=False)
    c.execute('CREATE UNIQUE INDEX anual_pk ON anual(pixel_id,temporada,fase)')
    c.execute('CREATE UNIQUE INDEX regiones_pk ON regiones(pixel_id)')
    c.execute('CREATE UNIQUE INDEX contexto_pk ON contexto_regional_oni(region,fase,contraste)')
    total=0;manifest=[]
    usecols=['pixel_id','temporada','fase_cultivo','fecha','mes','cat_oni_mes','estado_mjo','fraccion_afectada','ocurrencias_calificadas_dia','par_clima_oni_mjo_valido']
    for i,name in enumerate(files,1):
        path=a.daily/name;parts=[];n=0
        for chunk in pd.read_csv(path,compression='gzip',usecols=usecols,dtype={'estado_mjo':'string','cat_oni_mes':'string'},chunksize=100000):
            n+=len(chunk);parts.append(aggregate_chunk(chunk))
        if n!=daily_meta['filas_por_archivo'][name]:raise ValueError(f'Filas incorrectas: {name}')
        grouped=pd.concat(parts,ignore_index=True).groupby(KEYS,dropna=False,sort=False)[SUMS].sum(min_count=1).reset_index()
        if int(grouped.dias_observados.sum())!=n:raise ValueError('Se perdieron dias al agrupar')
        grouped.to_sql('mjo_mensual',c,if_exists='append',index=False,chunksize=20000)
        total+=n;manifest.append(dict(archivo=name,filas_diarias=n,filas_resumidas=len(grouped),sha256=sha(path)))
        print(f'{i}/{len(files)}: {name} | {total:,} dias consolidados',flush=True)
    c.execute("CREATE UNIQUE INDEX mjo_pk ON mjo_mensual(pixel_id,temporada,fase,anio_calendario,mes,COALESCE(cat_oni_mes,''),COALESCE(estado_mjo,''))")
    c.execute('CREATE INDEX mjo_grupos ON mjo_mensual(fase,mes,cat_oni_mes,estado_mjo)')
    # References include all MJO states, but exactly the same valid index pairs.
    c.executescript('''
    CREATE TABLE referencia_mes_oni AS
      SELECT pixel_id,temporada,fase,anio_calendario,mes,cat_oni_mes,
       SUM(dias_par_valido) AS dias_referencia,
       SUM(dias_afectados_par_valido) AS dias_afectados_referencia
      FROM mjo_mensual GROUP BY pixel_id,temporada,fase,anio_calendario,mes,cat_oni_mes;
    CREATE INDEX ref_pk ON referencia_mes_oni(pixel_id,temporada,fase,anio_calendario,mes,cat_oni_mes);
    CREATE VIEW matriz_calculo AS
      SELECT m.*, r.region, a.latitud,a.longitud,a.inicio,a.fin,a.dias_ventana,
       a.conteo_original AS conteo_anual,a.dias_afectados_equiv AS dias_afectados_anuales,
       a.episodios_100d,a.pct_dias_afectados,a.oni_ventana,a.cat_oni AS cat_oni_ventana,
       a.estado_cobertura_espacial,a.fraccion_area_climatica_util,
       1.0*m.dias_afectados_par_valido/NULLIF(m.dias_par_valido,0) AS fraccion_afectada_estado,
       b.dias_referencia,b.dias_afectados_referencia,
       1.0*b.dias_afectados_referencia/NULLIF(b.dias_referencia,0) AS fraccion_referencia_mes_oni,
       100.0*(m.dias_afectados_par_valido/NULLIF(1.0*m.dias_par_valido,0)-
        b.dias_afectados_referencia/NULLIF(1.0*b.dias_referencia,0)) AS diferencia_descriptiva_pp
      FROM mjo_mensual m JOIN anual a USING(pixel_id,temporada,fase)
      LEFT JOIN regiones r USING(pixel_id)
      LEFT JOIN referencia_mes_oni b ON m.pixel_id=b.pixel_id AND m.temporada=b.temporada
       AND m.fase=b.fase AND m.anio_calendario=b.anio_calendario AND m.mes=b.mes
       AND m.cat_oni_mes IS b.cat_oni_mes;
    CREATE TABLE control_reconstruccion_anual AS
      SELECT m.pixel_id,m.temporada,m.fase,SUM(m.dias_observados) AS dias_reconstruidos,
       SUM(m.ocurrencias_total) AS conteo_reconstruido,
       SUM(m.dias_afectados_total) AS afectados_reconstruidos,
       a.dias_ventana,a.conteo_original,a.dias_afectados_equiv,
       ABS(SUM(m.ocurrencias_total)-a.conteo_original) AS error_conteo,
       ABS(SUM(m.dias_afectados_total)-a.dias_afectados_equiv) AS error_afectados
      FROM mjo_mensual m JOIN anual a USING(pixel_id,temporada,fase)
      GROUP BY m.pixel_id,m.temporada,m.fase;
    CREATE TABLE cobertura_regional_mjo AS
      SELECT region,fase,mes,cat_oni_mes,estado_mjo,
       COUNT(DISTINCT CASE WHEN dias_par_valido>0 THEN pixel_id END) AS pixeles_con_datos,
       COUNT(DISTINCT CASE WHEN dias_par_valido>0 THEN temporada END) AS temporadas_con_datos,
       SUM(dias_par_valido) AS observaciones_pixel_dia,
       SUM(dias_afectados_par_valido) AS suma_exposicion_pixel_dia,
       AVG(fraccion_afectada_estado) AS media_descriptiva_fracciones_pixel_temporada_mes
      FROM matriz_calculo GROUP BY region,fase,mes,cat_oni_mes,estado_mjo;
    CREATE VIEW matriz_con_contexto_oni AS
      SELECT m.*,o.contraste AS contraste_oni_regional,o.diferencia AS diferencia_oni_regional,
       o.ic95_inferior AS ic95_inferior_oni_regional,o.ic95_superior AS ic95_superior_oni_regional,
       o.media_historica_todas_temporadas AS frecuencia_historica_regional,
       o.media_neutral AS frecuencia_neutral_regional,o.n_pixeles_elegibles AS pixeles_contexto_oni,
       o.pocos_pixeles AS pocos_pixeles_contexto_oni
      FROM matriz_calculo m LEFT JOIN contexto_regional_oni o ON m.region=o.region AND m.fase=o.fase;
    ''')
    bad=c.execute('SELECT COUNT(*) FROM control_reconstruccion_anual WHERE dias_reconstruidos!=dias_ventana OR error_conteo>1e-7 OR error_afectados>1e-7 OR error_conteo IS NULL OR error_afectados IS NULL').fetchone()[0]
    counts={t:c.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in ['anual','mjo_mensual','matriz_calculo','control_reconstruccion_anual','contexto_regional_oni','cobertura_regional_mjo']}
    if bad:raise ValueError(f'{bad} ventanas no reproducen matriz anual')
    if counts['mjo_mensual']!=counts['matriz_calculo']:raise ValueError('Union pierde o duplica filas')
    if not a.max_partitions and (total!=daily_meta['filas_diarias'] or counts['control_reconstruccion_anual']!=counts['anual']):raise ValueError('Cobertura incompleta')
    if c.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('SQLite no integro')
    c.commit()
    print('Exportando matriz plana CSV.gz y tablas de cobertura...',flush=True)
    # A single gzip stream, with one header; no Excel row limit.
    import gzip
    with gzip.open(out/'matriz_calculo.csv.gz','wt',encoding='utf-8',newline='') as f:
        for i,part in enumerate(pd.read_sql_query('SELECT * FROM matriz_calculo',c,chunksize=100000)):
            part.to_csv(f,index=False,header=i==0,na_rep='')
    for table in ['contexto_regional_oni','cobertura_regional_mjo']:
        export_query(c,'SELECT * FROM '+table,out/(table+'.csv'))
    export_query(c,'SELECT * FROM matriz_con_contexto_oni LIMIT 100',out/'ejemplo_matriz_con_contexto.csv')
    pd.DataFrame(manifest).to_csv(out/'particiones_verificadas.csv',index=False)
    c.close();pending.rename(out/'matriz_integrada.sqlite')
    report=dict(filas_diarias_consolidadas=total,tablas=counts,discrepancias_anuales=bad,prueba_parcial=bool(a.max_partitions),
      regionalizacion_provisional=regional_meta.get('regionalizacion_provisional',True),
      fuentes=dict(diaria=str(a.daily),anual=str(a.matrix),regional=str(a.regional)),
      sha256_fuentes=dict(diaria_completed=sha(a.daily/'completed.json'),anual=sha(a.matrix),regional_completed=sha(a.regional/'completed.json')),
      segundos=round(time.perf_counter()-start,2))
    (out/'LEEME.txt').write_text('Matriz local completa: anual + clima diario resumido por mes/ONI/MJO + contexto regional ONI.\nUna fila de matriz_calculo = pixel, temporada, fase, anio calendario, mes, ONI mensual, estado MJO observado. Combinaciones no observadas no se inventan como ceros. Faltantes quedan vacios; cero observado se conserva.\nmatriz_integrada.sqlite contiene anual (original completa), mjo_mensual, referencia_mes_oni, regiones, contexto_regional_oni y las vistas matriz_calculo y matriz_con_contexto_oni.\nmatriz_calculo.csv.gz es la matriz plana completa con valores anuales repetidos en cada fila correspondiente, sin celdas combinadas. No sumar esos valores anuales repetidos.\nmatriz_con_contexto_oni agrega UNA FILA POR CONTRASTE ONI REGIONAL: duplica explicitamente el grano por los dos contrastes. No usar para sumar exposicion. Los IC regionales ONI no son IC MJO ni IC por pixel.\nFracciones y diferencias en esta matriz son descriptivas dentro de pixel/temporada/mes. La referencia incluye los mismos dias MJO y usa solo pares validos. No son aun el contraste MJO estratificado entre temporadas.\nCobertura regional: observaciones_pixel_dia NO equivale a dias independientes; temporadas_con_datos cuenta temporadas distintas, sin multiplicarlas por pixeles. Media descriptiva con igual peso por fila pixel-temporada-mes, no una estimacion inferencial.\nCalor: ocurrencias anotadas en dia de calificacion, no episodios originados causalmente por MJO. MAT: ocurrencias son dias de lluvia >10 mm.\nLos CSV originales de Tabla B siguen siendo la fuente diaria completa, no se borran ni modifican. Esta matriz resumida no conserva secuencia diaria para calcular rezagos o pasajes MJO; usar los originales para esos analisis.\nSolo completed.json confirma finalizacion; prueba_parcial debe ser false para usar el conjunto completo.\n',encoding='utf-8')
    (out/'completed.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
    print(f'COMPLETO: {out}',flush=True)


if __name__=='__main__':main()
