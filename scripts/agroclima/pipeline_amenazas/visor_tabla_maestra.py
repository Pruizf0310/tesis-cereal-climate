"""Visor local de solo lectura para explorar todas las variables de la tesis."""
import argparse
import csv
from functools import lru_cache
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import io
import json
import math
from pathlib import Path
import sqlite3
import time
from urllib.parse import urlparse,parse_qs
import webbrowser

ROOT=Path('C:/Users/paola/Tesis/03_Resultados/Agroclima/vigente')
SOURCES={
 'rendimiento':ROOT/'rendimiento/cruce_anual_ONI_MJO_20261020_183145/cruce_rendimiento.sqlite',
 'oni_mjo':ROOT/'correlaciones/maize_ONI_frecuencias/matriz_integrada_ONI_MJO_20261020_163424/matriz_integrada.sqlite'}
GRAIN={
 'pares_anuales':'Píxel × temporada × fase agrícola × correspondencia del año de rendimiento. No sumar ambas correspondencias.',
 'rendimiento':'Píxel × año etiquetado en GDHY; sin repetir por fase.',
 'anual':'Píxel × temporada × fase agrícola.',
 'mjo_mensual':'Píxel × temporada × fase × año calendario × mes × ONI mensual × estado MJO observado.',
 'matriz_calculo':'Resumen MJO mensual con atributos anuales repetidos. No sumar los atributos anuales entre estas filas.',
 'matriz_con_contexto_oni':'Resumen mensual × contraste ONI regional. Los atributos anuales y regionales se repiten.',
 'correlaciones_regionales':'Región × fase × correspondencia de año × variable analizada.',
 'series_regionales_anuales':'Región × fase × correspondencia de año × variable × temporada. Un punto por temporada.',
 'pearson_por_pixel':'Píxel × fase × correspondencia de año × variable. Pearson puntual, sin IC.',
 'contexto_regional_oni':'Región × fase × contraste ONI. IC regionales, no IC por píxel ni MJO.'}
D={
 'pixel_id':('Identificación','ID','Identificador del píxel GDHY; no es una observación temporal.'),
 'latitud':('Ubicación','grados','Latitud del centro del píxel.'),
 'longitud':('Ubicación','grados','Longitud del centro del píxel.'),
 'temporada':('Calendario','año','Etiqueta de la temporada agrícola; puede abarcar dos años calendario.'),
 'fase':('Calendario','categoría','EST establecimiento; VEG vegetativa; FLO floración; REP reproductiva; FIL llenado; MAT maduración.'),
 'inicio':('Calendario','fecha','Inicio de la ventana agrícola usada para calcular la amenaza.'),
 'fin':('Calendario','fecha','Fin de esa ventana agrícola.'),
 'dias_ventana':('Calendario','días','Duración de la ventana, incluidos sus extremos.'),
 'dias_validos':('Cobertura','días','Días válidos del cálculo climático anual.'),
 'episodios':('Amenaza','episodios medios','Episodios de calor, media espacial. Para MAT consultar conteo_original y su unidad.'),
 'dias_afectados_equiv':('Amenaza','días equivalentes','Suma de las fracciones espaciales afectadas por día; admite decimales.'),
 'episodios_100d':('Amenaza','episodios / 100 días','Conteo de episodios de calor normalizado por duración; no es porcentaje.'),
 'pct_dias_afectados':('Amenaza','%','100 × días afectados equivalentes / días válidos; medida principal de exposición.'),
 'oni_ventana':('ONI','°C del índice','Promedio ONI de los meses de la ventana, ponderado por sus días.'),
 'cat_oni':('ONI','categoría','Categoría del ONI de la ventana: frío ≤−0,5; cálido ≥0,5; neutral entre esos límites.'),
 'estado_cobertura':('Cobertura','categoría','Estado de cobertura registrado al construir la matriz; consultar también las columnas de recuperación y soporte fijo.'),
 'calidad_origen':('Cobertura','categoría','Calidad informada por el cálculo original, conservada como procedencia.'),
 'fraccion_cobertura_origen':('Cobertura','fracción 0–1','Cobertura espacial informada originalmente, antes de la recuperación sobre soporte fijo.'),
 'variable_climatica':('Regla','categoría','Variable climática a la que se aplica el umbral.'),
 'operador':('Regla','operador','Comparación aplicada al umbral, conservada del cálculo.'),
 'umbral':('Regla','según variable','Umbral aplicado; su unidad depende de la variable climática. No confundir °C con mm.'),
 'duracion_min_dias':('Regla','días','Duración mínima de una racha para que cumpla la regla de amenaza.'),
 'unidad_conteo_origen':('Regla','texto','Unidad del conteo original: calor cuenta episodios; MAT cuenta días de lluvia >10 mm.'),
 'conteo_original':('Amenaza','según unidad_conteo_origen','Conteo medio espacial por temporada y fase. Admite decimales; no sumar episodios y días como una única amenaza.'),
 'par_frecuencia_oni_valido':('Cobertura','0/1','Indica si el par de exposición anual y ONI es válido; cero observado no es dato faltante.'),
 'cobertura_temporal_completa':('Cobertura','0/1','Indica cobertura temporal completa sobre el soporte climático utilizado.'),
 'estado_cobertura_espacial':('Cobertura','categoría','Soporte espacial completo o parcial fijo; las celdas permanentemente sin datos se excluyen.'),
 'fraccion_area_climatica_util':('Cobertura','fracción 0–1','Fracción de área con clima utilizable; no equivale a proporción de área cultivada.'),
 'celdas_validas_soporte_fijo':('Cobertura','celdas','Número de celdas climáticas válidas en el soporte fijo.'),
 'celdas_excluidas_sin_datos':('Cobertura','celdas','Celdas climáticas permanentemente vacías excluidas del soporte.'),
 'recuperado_desde_cache':('Cobertura','0/1','Indica recuperación local desde las series climáticas originales.'),
 'anio_fin_mat':('Calendario','año','Año en que termina MAT, usado como aproximación al año de cosecha.'),
 'region':('Ubicación','categoría','Región geográfica provisional asignada al centro del píxel.'),
 'dias_par_oni_mjo_valido':('MJO','días','Días de la ventana con el cruce clima–ONI–MJO válido.'),
 'fraccion_dias_mjo_debil':('MJO','fracción 0–1','Días con amplitud MJO ≤1 / días con par ONI–MJO válido.'),
 'fraccion_dias_mjo_activa':('MJO','fracción 0–1','Días con amplitud MJO >1 / días con par ONI–MJO válido.'),
 'cobertura_par_oni_mjo':('MJO','fracción 0–1','Días con par válido / duración total de la ventana.'),
 'alineacion':('Calendario','categoría','same-label: mismo año de temporada. maturity-year: año del fin de MAT. No escoger por mayor correlación.'),
 'anio_rendimiento':('Rendimiento','año','Año del rendimiento enlazado según la correspondencia seleccionada.'),
 'rendimiento_sin_tendencia':('Rendimiento','unidad del archivo local','Serie ya detrendida; puede ser negativa. El NetCDF procesado no declara unidades, por lo que no se interpreta como % de pérdida.'),
 'z_rendimiento':('Rendimiento','desviaciones estándar','Rendimiento detrendido centrado y dividido por su desviación muestral en los años disponibles del píxel.'),
 'anios_rendimiento_disponibles':('Rendimiento','años','Cantidad de años de rendimiento válidos para el píxel. Tener 35 años es válido.'),
 'par_amenaza_rendimiento_valido':('Cobertura','0/1','Par válido para exposición porcentual y z de rendimiento.'),
 'pearson_r':('Análisis','−1 a 1','Asociación lineal. No demuestra causalidad ni representa porcentaje de pérdida.'),
 'ic95_inferior':('Análisis','Pearson r o unidad del contraste','Límite inferior del intervalo; interpretar con la tabla de origen.'),
 'ic95_superior':('Análisis','Pearson r o unidad del contraste','Límite superior del intervalo; interpretar con la tabla de origen.'),
 'exposicion_media':('Análisis','según variable','Promedio regional de la variable analizada sobre pares válidos; revisar variable.'),
 'z_rendimiento_medio':('Análisis','z medio','Promedio de anomalías z sobre los mismos pares válidos que la exposición regional.'),
 'variable':('Análisis','nombre de columna','Medida analizada: porcentaje de días, conteo u ONI continuo.'),
 'pixeles_pareados':('Cobertura','píxeles','Píxeles con par válido en la temporada regional.'),
 'pixeles_elegibles':('Cobertura','píxeles','Soporte de píxeles con el mínimo de pares requerido.'),
 'temporadas_validas':('Cobertura','temporadas','Años que cumplen cobertura suficiente para el análisis regional.'),
 'pares_validos':('Cobertura','pares anuales','Pares usados en el coeficiente del píxel o registro resumido; no días independientes.')}
for i in range(1,9):D[f'fraccion_dias_mjo_{i}']=('MJO','fracción 0–1',f'Días con MJO activa en fase {i} / días con par ONI–MJO válido. No es la fase fenológica del cultivo.')


def quote(s):return '"'+s.replace('"','""')+'"'


def connect(source):
    if source not in SOURCES:raise ValueError('Fuente desconocida')
    path=SOURCES[source]
    if not path.is_file():raise ValueError('No existe la base: '+str(path))
    if not (path.parent/'completed.json').is_file():raise ValueError('Base sin registro de finalización')
    c=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
    c.execute('PRAGMA query_only=ON')
    deadline=time.monotonic()+45;c.set_progress_handler(lambda:int(time.monotonic()>deadline),10000)
    return c


@lru_cache(maxsize=4)
def catalog(source):
    with connect(source) as c:
        return [dict(r) for r in c.execute("SELECT name,type FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' ORDER BY name")]


def schema(c,source,table):
    if table not in {t['name'] for t in catalog(source)}:raise ValueError('Tabla desconocida')
    result=[]
    for r in c.execute('PRAGMA table_info('+quote(table)+')'):
        name=r['name'];group,unit,description=D.get(name,('Otra variable','Consultar origen','Columna conservada del origen. Su significado debe consultarse en LEEME.txt y en la definición de la tabla; no se infiere automáticamente.'))
        result.append(dict(nombre=name,tipo=r['type'],grupo=group,unidad=unit,descripcion=description,numerica=any(x in r['type'].upper() for x in ['INT','REAL','NUM','FLOAT','DOUBLE'])))
    return result


def query_parts(c,p):
    source=p.get('source','rendimiento');table=p.get('table','pares_anuales');cols=schema(c,source,table);names={x['nombre'] for x in cols}
    filters=p.get('filters',[])
    if len(filters)>12:raise ValueError('Demasiados filtros')
    sql=[];args=[]
    for f in filters:
        name=f['column'];op=f.get('op','eq')
        if name not in names or op not in ['eq','gte','lte','null','notnull']:raise ValueError('Filtro inválido')
        if op in ['null','notnull']:sql.append(quote(name)+(' IS NULL' if op=='null' else ' IS NOT NULL'))
        else:sql.append(quote(name)+{'eq':' = ?','gte':' >= ?','lte':' <= ?'}[op]);args.append(f['value'])
    return cols,names,quote(table),(' WHERE '+' AND '.join(sql)) if sql else '',args


def run_query(p,action):
    source=p.get('source','rendimiento')
    with connect(source) as c:
        cols,names,table,where,args=query_parts(c,p)
        if action=='schema':return dict(columns=cols,grain=GRAIN.get(p.get('table'), 'Consultar la clave y documentación de esta tabla.'),path=str(SOURCES[source]))
        if action=='rows':
            selected=p.get('columns') or [x['nombre'] for x in cols]
            if not set(selected)<=names:raise ValueError('Columnas inválidas')
            limit=max(1,min(int(p.get('limit',50)),200));offset=max(0,int(p.get('offset',0)))
            q='SELECT '+','.join(map(quote,selected))+' FROM '+table+where+' LIMIT ? OFFSET ?'
            rows=[dict(r) for r in c.execute(q,args+[limit+1,offset])]
            return dict(rows=rows[:limit],has_more=len(rows)>limit,offset=offset,columns=selected)
        if action=='count':return dict(count=c.execute('SELECT COUNT(*) FROM '+table+where,args).fetchone()[0])
        if action=='profile':
            name=p.get('column');col=next((x for x in cols if x['nombre']==name),None)
            if col is None:raise ValueError('Variable desconocida')
            exact=bool(p.get('exact'));q='SELECT '+quote(name)+' AS v FROM '+table+where+('' if exact else ' LIMIT 10000')
            extra=',MIN(v) minimo,MAX(v) maximo,AVG(v) media,SUM(CASE WHEN v=0 THEN 1 ELSE 0 END) ceros' if col['numerica'] else ''
            stats=dict(c.execute('SELECT COUNT(*) filas,COUNT(v) presentes,COUNT(*)-COUNT(v) faltantes'+extra+' FROM ('+q+')',args).fetchone())
            categories=[dict(r) for r in c.execute('SELECT v valor,COUNT(*) cantidad FROM ('+q+') GROUP BY v ORDER BY cantidad DESC LIMIT 25',args)] if not col['numerica'] else []
            return dict(stats=stats,categories=categories,scope='Todas las filas filtradas' if exact else 'Primeras 10.000 filas filtradas; muestra de lectura, no aleatoria ni representativa',definition=col)
        if action=='plot':
            x=p.get('x');y=p.get('y');numeric={v['nombre'] for v in cols if v['numerica']}
            if x not in numeric or y not in numeric:raise ValueError('Elegir dos variables numéricas')
            mode=p.get('mode','sample');clause=where+(' AND ' if where else ' WHERE ')+quote(x)+' IS NOT NULL AND '+quote(y)+' IS NOT NULL'
            if mode=='annual':
                if 'temporada' not in names:raise ValueError('Esta tabla no tiene temporada')
                required=[n for n in ['fase','alineacion','region','variable'] if n in names]
                applied={f['column'] for f in p.get('filters',[]) if f.get('op','eq')=='eq'}
                if not set(required)<=applied:raise ValueError('Para un punto por temporada, fija un valor de: '+', '.join(required))
                q='SELECT temporada etiqueta,AVG('+quote(x)+') x,AVG('+quote(y)+') y,COUNT(*) n FROM '+table+clause+' GROUP BY temporada ORDER BY temporada'
                caption='Un punto por temporada: medias de X e Y sobre las mismas filas con ambos valores. La cobertura puede variar. Sin inferencia ni IC nuevos.'
            else:
                label='temporada' if 'temporada' in names else 'NULL'
                q='SELECT '+label+' etiqueta,'+quote(x)+' x,'+quote(y)+' y,1 n FROM '+table+clause+' LIMIT 1000'
                caption='Primeras 1.000 filas con X e Y válidos. Muestra de lectura no aleatoria. Los píxeles del mismo año no son réplicas temporales independientes.'
            return dict(points=[dict(r) for r in c.execute(q,args)],caption=caption,x=x,y=y)
        if action=='export':
            selected=p.get('columns') or [x['nombre'] for x in cols]
            if not set(selected)<=names:raise ValueError('Columnas inválidas')
            rows=c.execute('SELECT '+','.join(map(quote,selected))+' FROM '+table+where+' LIMIT 100001',args)
            data=rows.fetchall()
            if len(data)>100000:raise ValueError('El filtro supera 100.000 filas. Restringe región, fase o años antes de exportar; no se exporta una tabla truncada.')
            s=io.StringIO(newline='');w=csv.writer(s);w.writerow(selected);w.writerows([['' if v is None else v for v in row] for row in data]);return s.getvalue()
    raise ValueError('Acción desconocida')


class Handler(BaseHTTPRequestHandler):
    def log_message(self,fmt,*args):pass
    def respond(self,data,status=200,kind='application/json; charset=utf-8'):
        if isinstance(data,(dict,list)):data=json.dumps(data,ensure_ascii=False,allow_nan=False)
        body=data.encode('utf-8');self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body)
    def do_GET(self):
        try:
            path=urlparse(self.path).path
            if path=='/':return self.respond(Path(__file__).with_name('visor_tabla_maestra.html').read_text(encoding='utf-8'),kind='text/html; charset=utf-8')
            if path=='/catalog':return self.respond({key:catalog(key) for key in SOURCES if SOURCES[key].is_file()})
            self.respond({'error':'Ruta desconocida'},404)
        except Exception as e:self.respond({'error':str(e)},400)
    def do_POST(self):
        try:
            # Only this same local application may make API requests.
            origin=self.headers.get('Origin')
            if origin and origin!='http://'+self.headers.get('Host',''):raise ValueError('Origen no permitido')
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':raise ValueError('Se requiere JSON')
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=64000:raise ValueError('Solicitud demasiado grande')
            p=json.loads(self.rfile.read(size));action=urlparse(self.path).path.removeprefix('/api/')
            result=run_query(p,action)
            self.respond(result,kind='text/csv; charset=utf-8' if action=='export' else 'application/json; charset=utf-8')
        except Exception as e:self.respond({'error':str(e)},400)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--terminal',action='store_true');p.add_argument('--source',choices=list(SOURCES),default='rendimiento');p.add_argument('--table',default='pares_anuales')
    p.add_argument('--columns',help='Nombres separados por coma para la muestra en terminal');p.add_argument('--limit',type=int,default=5)
    p.add_argument('--port',type=int,default=0);p.add_argument('--no-browser',action='store_true')
    a=p.parse_args()
    if a.terminal:
        data=run_query(dict(source=a.source,table=a.table),'schema')
        print('FUENTE:',data['path']);print('UNA FILA:',data['grain']);print('\nDICCIONARIO COMPLETO:')
        for i,col in enumerate(data['columns'],1):print(f"{i:02d}. {col['nombre']} [{col['tipo']}; {col['unidad']}]\n    {col['descripcion']}")
        columns=a.columns.split(',') if a.columns else None
        rows=run_query(dict(source=a.source,table=a.table,columns=columns,limit=a.limit),'rows')
        print('\nMUESTRA (no es la tabla completa):');print(json.dumps(rows['rows'],ensure_ascii=False,indent=2));return
    server=ThreadingHTTPServer(('127.0.0.1',a.port),Handler);url=f'http://127.0.0.1:{server.server_port}'
    print('VISOR LOCAL:',url,flush=True);print('Bases abiertas en SOLO LECTURA. Ctrl+C detiene el visor. Mantén esta terminal abierta.',flush=True)
    if not a.no_browser:webbrowser.open(url)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__=='__main__':main()
