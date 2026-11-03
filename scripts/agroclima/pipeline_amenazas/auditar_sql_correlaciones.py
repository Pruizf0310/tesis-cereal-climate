"""Auditoria reproducible de solo lectura; no calcula nuevas correlaciones."""
import argparse
import json
import sqlite3
import time
import traceback
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path('C:/Users/paola/Tesis/03_Resultados/Agroclima/vigente')
SOURCES = {
    'rendimiento': ROOT/'rendimiento/cruce_anual_ONI_MJO_20261020_183145/cruce_rendimiento.sqlite',
    'oni_mjo': ROOT/'correlaciones/maize_ONI_frecuencias/matriz_integrada_ONI_MJO_20261020_163424/matriz_integrada.sqlite',
}

def q(name):
    return '"' + name.replace('"', '""') + '"'

def records(c, sql):
    return [dict(r) for r in c.execute(sql)]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    report = {'inicio_utc': datetime.now(timezone.utc).isoformat(), 'fuentes': {},
              'alcance': 'Maiz; fuentes explicitas vigentes. No representa auditoria de otros cultivos.'}
    try:
        for source, path in SOURCES.items():
            print(f'Abriendo {source}: {path}', flush=True)
            st = path.stat()
            info = {'ruta': str(path), 'bytes': st.st_size, 'mtime_ns': st.st_mtime_ns, 'tablas': {}}
            report['fuentes'][source] = info
            c = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
            c.row_factory = sqlite3.Row
            c.execute('PRAGMA query_only=ON')
            objects = records(c, "SELECT name,type,sql FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%'")
            for obj in objects:
                name = obj['name']
                print(f'{source}: estructura {name}', flush=True)
                cols = records(c, f'PRAGMA table_info({q(name)})')
                table = {'tipo': obj['type'], 'sql': obj['sql'], 'columnas': cols,
                         'indices': records(c, f'PRAGMA index_list({q(name)})') if obj['type']=='table' else []}
                info['tablas'][name] = table
                # Las vistas pueden repetir atributos anuales; no se perfilan como observaciones independientes.
                if obj['type'] != 'table':
                    continue
                table['filas'] = c.execute(f'SELECT COUNT(*) FROM {q(name)}').fetchone()[0]
                if name not in ('anual', 'pares_anuales', 'rendimiento', 'mjo_mensual', 'pearson_por_pixel', 'correlaciones_regionales'):
                    continue
                names = {col['name'] for col in cols}
                table['muestra'] = records(c, f'SELECT * FROM {q(name)} LIMIT 3')
                dimensions = [n for n in ('fase','alineacion','cultivo','amenaza','unidad_conteo_origen','variable','estado_mjo') if n in names]
                table['categorias'] = {n: records(c, f'SELECT {q(n)}, COUNT(*) filas FROM {q(name)} GROUP BY {q(n)}') for n in dimensions}
                temporal = [n for n in ('temporada','anio_rendimiento','anio','year') if n in names]
                table['rango_temporal'] = {n: records(c, f'SELECT MIN({q(n)}) minimo, MAX({q(n)}) maximo, COUNT(DISTINCT {q(n)}) distintos FROM {q(name)}')[0] for n in temporal}
                if name in ('anual','pares_anuales','rendimiento'):
                    print(f'{source}: perfil completo {name}', flush=True)
                    expressions = []
                    for i, col in enumerate(cols):
                        n = q(col['name'])
                        expressions.append(f'SUM({n} IS NULL) AS null_{i}')
                        if any(t in col['type'].upper() for t in ('INT','REAL','FLOAT','DOUBLE','NUM')):
                            expressions.extend([f'MIN({n}) AS min_{i}', f'MAX({n}) AS max_{i}', f'SUM({n}=0) AS zero_{i}'])
                    values = dict(c.execute(f'SELECT {",".join(expressions)} FROM {q(name)}').fetchone())
                    table['perfil'] = {col['name']: {key: values[f'{key}_{i}'] for key in ('null','min','max','zero') if f'{key}_{i}' in values} for i,col in enumerate(cols)}
                    key = ['pixel_id','anio_rendimiento'] if name=='rendimiento' else ['pixel_id','temporada','fase'] + (['alineacion'] if name=='pares_anuales' else [])
                    if set(key)<=names:
                        keys = ','.join(map(q,key))
                        table['clave_candidata'] = key
                        table['grupos_duplicados'] = c.execute(f'SELECT COUNT(*) FROM (SELECT 1 FROM {q(name)} GROUP BY {keys} HAVING COUNT(*)>1)').fetchone()[0]
                if name=='pares_anuales':
                    xs = [n for n in names if n in ('pct_dias_afectados','conteo_original','oni_ventana') or n.startswith('fraccion_dias_mjo_')]
                    table['cruces_candidatos'] = []
                    for x in sorted(xs):
                        conditions = f'{q(x)} IS NOT NULL AND z_rendimiento IS NOT NULL'
                        if 'par_frecuencia_oni_valido' in names and x in ('pct_dias_afectados','conteo_original','oni_ventana'):
                            conditions += ' AND par_frecuencia_oni_valido=1'
                        summary = records(c, f'SELECT fase, alineacion, COUNT(*) pixeles, MIN(n) min_pares, MAX(n) max_pares, SUM(n>=30) pixeles_30_pares, SUM(n>=30 AND lo=hi) pixeles_x_constante FROM (SELECT pixel_id,fase,alineacion,SUM(CASE WHEN {conditions} THEN 1 ELSE 0 END) n,MIN(CASE WHEN {conditions} THEN {q(x)} END) lo,MAX(CASE WHEN {conditions} THEN {q(x)} END) hi FROM pares_anuales GROUP BY pixel_id,fase,alineacion) GROUP BY fase,alineacion')
                        table['cruces_candidatos'].append({'x':x,'y':'z_rendimiento','cobertura_pares_no_nulos':summary,
                          'nota':'Perfil preliminar; definir cobertura MJO, finitud, variacion de Y y filtros cientificos antes de correlacionar.'})
            c.close()
            after = path.stat()
            info['fuente_estable_durante_lectura'] = st.st_size==after.st_size and st.st_mtime_ns==after.st_mtime_ns
            (a.output/'auditoria.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        lines = ['# Auditoria previa a correlaciones', '', report['alcance'], '',
                 'Las fuentes se abrieron en modo de solo lectura. No se calcularon nuevas correlaciones.', '',
                 '## Inventario', '']
        for source,info in report['fuentes'].items():
            lines.append(f"- {source}: `{info['ruta']}`")
            for name,t in info['tablas'].items():
                lines.append(f"  - {name}: {t.get('filas','vista; no contada')} filas; {len(t['columnas'])} columnas; duplicados de clave: {t.get('grupos_duplicados','no evaluados')}.")
        lines += ['', '## Decisiones para construir los scripts', '',
          '- Usar pixel × temporada × fase × escenario; analizar cada escenario por separado.',
          '- Confirmar documentalmente la correspondencia del año de rendimiento; no elegirla por mayor correlacion.',
          '- Definir amenaza y unidad por fase; no equiparar conteos de eventos con dias.',
          '- Confirmar denominador de frecuencia y tratamiento de ceros, faltantes y cobertura.',
          '- MJO mensual debe agregarse a la ventana agricola sin repetir rendimiento como replicas mensuales.',
          '- Para MJO definir cobertura minima y denominador de las fracciones antes de seleccionar pares.',
          '- El perfil de pares no sustituye controles de varianza, autocorrelacion o comparaciones multiples.',
          '- Revisar pearson_por_pixel y correlaciones_regionales antes de repetir calculos existentes.',
          '- Mantener asociaciones exploratorias separadas de modelos de impacto o perdida.',
          '', 'El detalle de columnas, categorias, nulos, ceros, rangos y cobertura por cruce esta en auditoria.json.']
        (a.output/'INFORME.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        (a.output/'completed.json').write_text(json.dumps({'estado':'completo','segundos':round(time.perf_counter()-started,2),'fuentes_estables':all(x['fuente_estable_durante_lectura'] for x in report['fuentes'].values())},indent=2),encoding='utf-8')
        print('COMPLETO: '+str(a.output),flush=True)
    except Exception:
        (a.output/'failed.txt').write_text(traceback.format_exc(),encoding='utf-8')
        raise

if __name__=='__main__':
    main()
