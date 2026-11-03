"""Recover annual exposures on verified fixed spatial supports; never edit the input matrix."""
import argparse
import csv
from datetime import date
import gzip
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import time
from rutas_resultados_oni import resultados_oni

RUNS = dict(EST='01118480a325e93d',VEG='0955242f426ffa57',REP='ba9e0e3286c7e384',
            FLO='4e3c0e35ac33f725',FIL='a445419ee76712f0',MAT='a7342fb2d9bf24a2')
PHASE_ORDER = "CASE fase WHEN 'EST' THEN 1 WHEN 'VEG' THEN 2 WHEN 'REP' THEN 3 WHEN 'FLO' THEN 4 WHEN 'FIL' THEN 5 ELSE 6 END"


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda:f.read(4*1024*1024),b''):h.update(part)
    return h.hexdigest()


def measure(cells, minimum, is_rain):
    """Use only full cells; caller must prove their support fixed over all windows."""
    signature=[];area=0.;total_area=0.;episodes=0.;affected=0.;days=None
    for cell in cells:
        valid=cell['valid'];hits=cell['hits']
        if days is None:days=len(valid)
        if len(valid)!=days or len(hits)!=days or not days:raise ValueError('Series truncadas')
        if not set(valid)<=set([0,1]) or not set(hits)<=set([0,1]):raise ValueError('Flags no binarios')
        n=sum(valid);state='complete' if n==days else 'empty' if n==0 else 'partial'
        if state=='partial':raise ValueError('Hueco temporal: no se recupera automaticamente')
        key=(float(cell['x']),float(cell['y']));signature.append((key,state))
        weight=math.cos(math.radians(float(cell['latitude'])));total_area+=weight
        if state=='empty':continue
        area+=weight;length=0;counts=0;hit_days=0
        for hit in list(hits)+[0]:
            if hit:length+=1
            else:
                if length >= minimum:
                    counts+=length if is_rain else 1
                    hit_days+=length
                length=0
        episodes+=weight*counts;affected+=weight*hit_days
    if len({x[0] for x in signature})!=len(signature):raise ValueError('Celdas duplicadas')
    if not area or not total_area:raise ValueError('Ninguna celda completa disponible')
    return dict(signature=tuple(sorted(signature)),dias=days,conteo=episodes/area,
                dias_afectados=affected/area,fraccion_area=area/total_area,
                celdas_utiles=sum(s=='complete' for _,s in signature),celdas_excluidas=sum(s=='empty' for _,s in signature))


def recover_pixel(pid, rows, plans, evidence):
    expected={(y,p) for y in range(1981,2017) for p in RUNS}
    if {(r['temporada'],r['fase']) for r in rows}!=expected:raise ValueError(f'{pid}: no tiene 216 ventanas esperadas')
    indexed={(r['temporada'],r['fase']):r for r in rows};support=None;result=[]
    for phase,plan in plans.items():
        path=Path(plan['cache'])/f'{pid}.json.gz'
        marker=path.with_suffix('.sha.json')
        digest=sha(path)
        if digest!=json.loads(marker.read_text(encoding='utf-8'))['sha256']:raise ValueError(f'Cache alterado: {path}')
        evidence[str(path)]=digest
        with gzip.open(path,'rt',encoding='utf-8') as f:cache=json.load(f)
        if set(cache)!=set(map(str,range(1981,2017))):raise ValueError(f'{pid}/{phase}: faltan temporadas')
        rule=plan['identity']['rule'];minimum=1 if phase=='MAT' else int(rule['min_days'])
        for year in range(1981,2017):
            row=indexed[year,phase];cells=cache[str(year)]
            if not cells:raise ValueError('Cache sin celdas')
            for cell in cells:
                if int(cell['pixel_id'])!=pid or int(cell['season_year'])!=year or cell['phase']!=phase:raise ValueError('Clave de cache incorrecta')
                if cell['phase_start']!=row['inicio'] or cell['phase_end']!=row['fin']:raise ValueError('Ventana distinta')
                for a,b in [('threshold','umbral'),('operator','operador'),('variable','variable_climatica'),('min_days','duracion_min_dias'),('count_unit','unidad_conteo_origen')]:
                    if cell[a]!=row[b] or rule[a]!=row[b]:raise ValueError(f'Regla distinta: {a}')
            m=measure(cells,minimum,phase=='MAT')
            if support is None:support=m['signature']
            if support!=m['signature']:raise ValueError(f'{pid}: mascara espacial cambia entre fases/temporadas')
            if m['dias']!=row['dias_ventana'] or m['dias']!=(date.fromisoformat(row['fin'])-date.fromisoformat(row['inicio'])).days+1:raise ValueError('Duracion distinta')
            m.update(pixel_id=pid,temporada=year,fase=phase,oni_valido=row['oni_ventana'] is not None)
            result.append(m)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path('C:/Users/paola/Tesis'))
    parser.add_argument('--input',type=Path,required=True,help='Carpeta terminada que contiene matriz_frecuencias_ONI.sqlite y completed.json')
    parser.add_argument('--output',type=Path,help='Carpeta NUEVA para la version corregida')
    args=parser.parse_args();started=time.perf_counter();source=args.input.resolve()
    output=args.output.resolve() if args.output else resultados_oni(args.root)/('matriz_frecuencias_ONI_corregida_'+time.strftime('%Y%m%d_%H%M%S'))
    if output.exists():parser.error('La salida ya existe: usa una carpeta nueva')
    db=source/'matriz_frecuencias_ONI.sqlite';completed=source/'completed.json'
    if not db.is_file() or not completed.is_file():parser.error('La entrada no tiene una matriz terminada')
    manifest=json.loads(completed.read_text(encoding='utf-8'))
    original=sqlite3.connect(db.as_uri()+'?mode=ro',uri=True);original.row_factory=sqlite3.Row
    if original.execute('SELECT count(*) FROM matriz').fetchone()[0]!=2359368:raise ValueError('Dimension inesperada')
    invalid=[dict(r) for r in original.execute("SELECT * FROM matriz WHERE par_frecuencia_oni_valido=0 ORDER BY pixel_id,temporada,fase")]
    ids=sorted({r['pixel_id'] for r in invalid})
    ids_set=set(ids)
    if len(ids)!=58 or len(invalid)!=12528:raise ValueError('La entrada no corresponde a los 58 pixeles auditados')
    output.mkdir(parents=True,exist_ok=False)
    evidence={str(db):sha(db),str(completed):sha(completed),str(Path(__file__).resolve()):sha(Path(__file__))}
    base=args.root.resolve()/'03_Resultados/Agroclima/vigente';plans={}
    for phase,run in RUNS.items():
        path=base/f'probabilidades/maize_{phase}_global_1981_2016'/run/'plan.json'
        evidence[str(path)]=sha(path);plans[phase]=json.loads(path.read_text(encoding='utf-8'))
    recovered=[]
    for i,pid in enumerate(ids,1):
        recovered.extend(recover_pixel(pid,[r for r in invalid if r['pixel_id']==pid],plans,evidence))
        print(f'Cache verificado: pixel {i}/58 ({pid}), 36 temporadas x 6 fases; soporte fijo',flush=True)
    lookup={(r['pixel_id'],r['temporada'],r['fase']):r for r in recovered}
    annual=base/'ejecuciones/maize_seis_fases_GEE_1981_2016/resumen_GDHY_anual.csv'
    digest=sha(annual);expected=manifest['fuentes_sha256'].get(str(annual))
    # JSON source paths may use either slash style.
    if expected is None:
        expected=next((v for k,v in manifest['fuentes_sha256'].items() if Path(k).resolve()==annual.resolve()),None)
    if expected is None or expected!=digest:raise ValueError('El resumen anual no coincide con la fuente de la matriz')
    evidence[str(annual)]=digest;seen=set()
    print('Contrastando los 12.528 conteos contra el resumen original...',flush=True)
    with annual.open(encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            if int(r['pixel_id']) not in ids_set:continue
            key=(int(r['pixel_id']),int(r['season_year']),r['phase'])
            if key in seen:raise ValueError('Clave original duplicada')
            seen.add(key);m=lookup[key];value=float(r['mean_count_per_native_cell'])
            if not math.isclose(value,m['conteo'],rel_tol=1e-8,abs_tol=1e-8):raise ValueError(f'Conteo no coincide: {key}')
            m['conteo_original']=value
    if seen!=set(lookup):raise ValueError('Faltan registros originales')
    pending=output/'matriz_frecuencias_ONI.pending.sqlite';con=sqlite3.connect(pending.as_uri()+'?mode=rwc',uri=True)
    print('Copiando SQLite a una nueva version; la original se conserva...',flush=True)
    original.backup(con)
    additions={'cobertura_temporal_completa':'INTEGER','estado_cobertura_espacial':'TEXT',
        'fraccion_area_climatica_util':'REAL','celdas_validas_soporte_fijo':'INTEGER',
        'celdas_excluidas_sin_datos':'INTEGER','recuperado_desde_cache':'INTEGER'}
    for col,kind in additions.items():con.execute(f'ALTER TABLE matriz ADD COLUMN {col} {kind}')
    con.execute("UPDATE matriz SET cobertura_temporal_completa=CASE WHEN estado_cobertura='completa' THEN 1 ELSE 0 END, estado_cobertura_espacial=CASE WHEN estado_cobertura='completa' THEN 'completa' ELSE 'pendiente' END, fraccion_area_climatica_util=CASE WHEN estado_cobertura='completa' THEN 1.0 ELSE NULL END, celdas_excluidas_sin_datos=CASE WHEN estado_cobertura='completa' THEN 0 ELSE NULL END, recuperado_desde_cache=0")
    sql='''UPDATE matriz SET dias_validos=?,episodios=?,dias_afectados_equiv=?,episodios_100d=?,pct_dias_afectados=?,
        estado_cobertura='completa',conteo_original=?,par_frecuencia_oni_valido=?,cobertura_temporal_completa=1,
        estado_cobertura_espacial='parcial_fija',fraccion_area_climatica_util=?,celdas_validas_soporte_fijo=?,
        celdas_excluidas_sin_datos=?,recuperado_desde_cache=1 WHERE pixel_id=? AND temporada=? AND fase=?'''
    for m in recovered:
        rain=m['fase']=='MAT';days=m['dias']
        con.execute(sql,(days,None if rain else m['conteo_original'],m['dias_afectados'],None if rain else 100*m['conteo_original']/days,
            100*m['dias_afectados']/days,m['conteo_original'],int(m['oni_valido']),m['fraccion_area'],m['celdas_utiles'],m['celdas_excluidas'],m['pixel_id'],m['temporada'],m['fase']))
    con.commit()
    # Compare every pre-existing column on every previously valid row, not just sums.
    con.execute('ATTACH DATABASE ? AS anterior',(db.as_uri()+'?mode=ro',))
    old_cols=[r[1] for r in original.execute('PRAGMA table_info(matriz)')]
    differences=' OR '.join(f'NOT (n."{c}" IS a."{c}")' for c in old_cols)
    changed=con.execute(f'SELECT count(*) FROM matriz n JOIN anterior.matriz a USING(pixel_id,temporada,fase) WHERE a.par_frecuencia_oni_valido=1 AND ({differences})').fetchone()[0]
    if changed:raise ValueError('Se alteraron filas anteriormente validas')
    for c in ['oni_ventana','cat_oni','inicio','fin','calidad_origen','fraccion_cobertura_origen']:
        if con.execute(f'SELECT count(*) FROM matriz n JOIN anterior.matriz a USING(pixel_id,temporada,fase) WHERE NOT(n.{c} IS a.{c})').fetchone()[0]:raise ValueError(f'Se altero {c}')
    checks={
        'filas':con.execute('SELECT count(*) FROM matriz').fetchone()[0],
        'recuperadas':con.execute('SELECT count(*) FROM matriz WHERE recuperado_desde_cache=1').fetchone()[0],
        'pares_validos':con.execute('SELECT sum(par_frecuencia_oni_valido) FROM matriz').fetchone()[0],
        'alteradas_previamente_validas':changed,
        'integridad_sqlite':con.execute('PRAGMA integrity_check').fetchone()[0]}
    if checks['filas']!=2359368 or checks['recuperadas']!=12528 or checks['pares_validos']!=2359368 or checks['integridad_sqlite']!='ok':raise ValueError(checks)
    if con.execute("SELECT count(*) FROM matriz WHERE dias_validos<>dias_ventana OR pct_dias_afectados < -1e-8 OR pct_dias_afectados > 100.00000001 OR (fase='MAT' AND (episodios IS NOT NULL OR episodios_100d IS NOT NULL))").fetchone()[0]:raise ValueError('Rangos o no aplicabilidad incorrectos')
    fields=[r[1] for r in con.execute('PRAGMA table_info(matriz)')]
    print('Exportando matriz corregida completa a CSV comprimido...',flush=True)
    csv_pending=output/'matriz_frecuencias_ONI.pending.csv.gz'
    with gzip.open(csv_pending,'wt',encoding='utf-8',newline='') as f:
        w=csv.writer(f);w.writerow(fields)
        for phase in RUNS:
            w.writerows(con.execute('SELECT * FROM matriz WHERE fase=? ORDER BY pixel_id,temporada',(phase,)))
            print(f'CSV: fase {phase} exportada',flush=True)
    # Verify every exported row and column against the database, with round-trip floats.
    print('Verificando CSV frente a SQLite fila por fila...',flush=True)
    n=0
    with gzip.open(csv_pending,'rt',encoding='utf-8',newline='') as f:
        reader=csv.reader(f)
        if next(reader)!=fields:raise ValueError('Encabezado CSV incorrecto')
        for phase in RUNS:
            for row in con.execute('SELECT * FROM matriz WHERE fase=? ORDER BY pixel_id,temporada',(phase,)):
                exported=next(reader)
                if exported!=['' if v is None else str(v) for v in row]:raise ValueError(f'CSV distinto en fila {n}')
                n+=1
        if next(reader,None) is not None or n!=2359368:raise ValueError('Filas CSV incorrectas')
    sample_pid=ids[0]
    with (output/'ejemplo_pixel_recuperado_216_filas.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(fields);w.writerows(con.execute(f'SELECT * FROM matriz WHERE pixel_id=? ORDER BY temporada,{PHASE_ORDER}',(sample_pid,)))
    query="""SELECT fase,count(*) filas,sum(par_frecuencia_oni_valido) pares_validos,
        sum(recuperado_desde_cache) recuperadas,sum(estado_cobertura_espacial='parcial_fija') espacial_parcial_fija,
        sum(cat_oni='frio' AND par_frecuencia_oni_valido=1) fria_valida,
        sum(cat_oni='neutral' AND par_frecuencia_oni_valido=1) neutral_valida,
        sum(cat_oni='calido' AND par_frecuencia_oni_valido=1) calida_valida FROM matriz GROUP BY fase"""
    cursor=con.execute(query);names=[x[0] for x in cursor.description];quality=[dict(zip(names,row)) for row in cursor]
    con.execute('ALTER TABLE control_calidad RENAME TO control_calidad_anterior')
    con.execute('CREATE TABLE control_calidad ('+', '.join(f'{k} '+('TEXT' if k=='fase' else 'INTEGER') for k in names)+')')
    con.executemany('INSERT INTO control_calidad VALUES ('+','.join('?' for _ in names)+')',[list(r.values()) for r in quality])
    with (output/'control_calidad.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=names);w.writeheader();w.writerows(quality)
    con.execute('CREATE TABLE fuentes_correccion (ruta TEXT PRIMARY KEY,sha256 TEXT)')
    con.executemany('INSERT INTO fuentes_correccion VALUES (?,?)',evidence.items())
    con.commit();con.close();original.close()
    pending.rename(output/'matriz_frecuencias_ONI.sqlite');csv_pending.rename(output/'matriz_frecuencias_ONI.csv.gz')
    report=dict(version='cobertura_espacial_fija_v2',entrada=str(source),filas=checks['filas'],
        pixeles=10923,temporadas=[1981,2016],fases=list(RUNS),clave=['pixel_id','temporada','fase'],pixeles_recuperados=ids,
        controles=checks,csv_verificado_fila_por_fila=True,fuentes_correccion_sha256=evidence,
        control_por_fase=quality,segundos=round(time.perf_counter()-started,2))
    (output/'LEEME.txt').write_text(
        'VERSION CORREGIDA: una fila por pixel, temporada y fase.\n'
        'Se recuperaron 12.528 filas de 58 pixeles con soporte espacial fijo verificado en las 36 temporadas y seis fases.\n'
        'estado_cobertura=completa significa cobertura TEMPORAL completa sobre el soporte climatico disponible.\n'
        'estado_cobertura_espacial=parcial_fija identifica los 58 pixeles; fraccion_area_climatica_util registra la fraccion geometrica ponderada observada.\n'
        'Esa fraccion no mide area de maiz ni demuestra representatividad agricola. No se rellena con cero la superficie sin datos.\n'
        'Las celdas validas y excluidas se conservan fijas entre temporadas/fases. celdas_validas_soporte_fijo solo se completo en los pixeles recuperados.\n'
        'calidad_origen y fraccion_cobertura_origen conservan los valores originales; pueden indicar INCOMPLETE aunque la cobertura temporal corregida sea completa.\n'
        'recuperado_desde_cache=1 identifica las filas corregidas. Las columnas existentes de las otras 2.346.840 filas se verifican sin cambios.\n'
        'MAT cuenta dias de lluvia; episodios y episodios_100d siguen vacios. Ceros reales se conservan.\n'
        'Los indices ONI y sus categorias no cambian. No se incluyen rendimientos. Un futuro cruce usara los anios de rendimiento disponibles por pixel.\n'
        'La base anterior no se modifica. La salida solo es utilizable si existe completed.json.\n'
        'La tabla control_calidad_anterior conserva los controles heredados; control_calidad contiene los controles corregidos.\n',encoding='utf-8')
    (output/'completed.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(checks,ensure_ascii=False,indent=2),flush=True)
    print(f'COMPLETO: {output}',flush=True)


if __name__=='__main__':main()
