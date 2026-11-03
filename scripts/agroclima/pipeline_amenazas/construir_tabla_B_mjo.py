"""Reconstruct the complete daily climate/ONI/RMM table from local native caches only."""
import argparse
import csv
from contextlib import ExitStack
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import time
import numpy as np
import pandas as pd
from correlacion_oni_amenazas import read_oni
from corregir_matriz_cobertura_espacial import RUNS
from rutas_resultados_oni import resultados_oni


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()


def reconstruct(cells,minimum,rain):
    n=len(cells[0]['valid']);weights=[];affected=[];counts=[];signature=[]
    for cell in cells:
        valid=np.asarray(cell['valid'],bool);hit=np.asarray(cell['hits'],bool)
        if len(valid)!=n or len(hit)!=n:raise ValueError('Series truncadas')
        signature.append((float(cell['x']),float(cell['y']),bool(valid.all())))
        if not valid.any():continue
        if not valid.all():raise ValueError('Huecos temporales: no recuperar automaticamente')
        edges=np.diff(np.r_[False,hit,False].astype(int));starts=np.flatnonzero(edges==1);ends=np.flatnonzero(edges==-1)
        a=np.zeros(n);c=np.zeros(n)
        for first,last in zip(starts,ends):
            if last-first>=minimum:
                a[first:last]=1
                if rain:c[first:last]=1
                else:c[first+minimum-1]=1
        weights.append(np.cos(np.deg2rad(cell['latitude'])));affected.append(a);counts.append(c)
    if not weights:raise ValueError('Sin celdas completas')
    w=np.asarray(weights);w=w/w.sum()
    return w@np.asarray(affected),w@np.asarray(counts),tuple(sorted(signature))


def daily_indices(root):
    oni_path=root/'01_Data/ONI/ONI_v6_2026-10-08.html';rmm_path=root/'01_Data/RMM/rmm_official.txt'
    oni,*_=read_oni(oni_path)
    r=pd.read_csv(rmm_path,sep=r'\s+',skiprows=2,header=None,usecols=range(7),names=['year','month','day','rmm1','rmm2','fase_mjo','amplitud_mjo'])
    r['fecha']=pd.to_datetime(r[['year','month','day']])
    if r.fecha.duplicated().any():raise ValueError('Fechas RMM duplicadas')
    valid=np.isfinite(r[['rmm1','rmm2','amplitud_mjo']]).all(axis=1)&r[['rmm1','rmm2']].abs().lt(100).all(axis=1)&r.amplitud_mjo.ge(0)&r.amplitud_mjo.lt(100)&r.fase_mjo.between(1,8)
    r['estado_mjo']=pd.Series(None,index=r.index,dtype=object)
    r.loc[valid & r.amplitud_mjo.le(1),'estado_mjo']='debil'
    r.loc[valid & r.amplitud_mjo.gt(1),'estado_mjo']=r.loc[valid & r.amplitud_mjo.gt(1),'fase_mjo'].astype(int).astype(str)
    r.loc[~valid,['rmm1','rmm2','fase_mjo','amplitud_mjo']]=np.nan
    r['mjo_valida']=valid
    return oni,r.set_index('fecha'),oni_path,rmm_path


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path('C:/Users/paola/Tesis'))
    p.add_argument('--matrix',type=Path,help='SQLite corregido; por defecto la version validada')
    p.add_argument('--output',type=Path)
    p.add_argument('--pixels',help='Lista de pixel_id separados por coma para piloto; omitir para TODOS')
    args=p.parse_args();root=args.root.resolve();started=time.perf_counter()
    matrix=args.matrix.resolve() if args.matrix else resultados_oni(root)/'matriz_frecuencias_ONI_corregida_20261019_165114/matriz_frecuencias_ONI.sqlite'
    if not (matrix.parent/'completed.json').is_file():p.error('Usar matriz corregida terminada')
    out=args.output.resolve() if args.output else resultados_oni(root)/('tabla_B_MJO_'+time.strftime('%Y%m%d_%H%M%S'))
    if out.exists():p.error('La salida debe ser nueva')
    ids=None if args.pixels is None else sorted(set(int(x) for x in args.pixels.split(',')))
    con=sqlite3.connect(matrix.as_uri()+'?mode=ro',uri=True)
    known={x[0] for x in con.execute('SELECT DISTINCT pixel_id FROM matriz')}
    if ids is not None and not set(ids)<=known:p.error('Pixel desconocido')
    oni,rmm,oni_path,rmm_path=daily_indices(root)
    out.mkdir(parents=True,exist_ok=False);partition=out/'diario_por_fase_temporada';partition.mkdir()
    schemas=['pixel_id','latitud','longitud','temporada','fase_cultivo','fecha','mes',
             'fraccion_afectada','ocurrencias_calificadas_dia','oni_mes','cat_oni_mes',
             'rmm1','rmm2','fase_mjo','amplitud_mjo','estado_mjo','mjo_valida','par_clima_oni_mjo_valido',
             'estado_cobertura_espacial','fraccion_area_climatica_util']
    sources={str(matrix):sha(matrix),str(oni_path):sha(oni_path),str(rmm_path):sha(rmm_path),str(Path(__file__).resolve()):sha(Path(__file__))}
    file_counts={};quality=[];support={};total=0;expected=0;mismatches=0;sample_written=False
    example=out/'ejemplo_diario_un_pixel.csv'
    with example.open('w',encoding='utf-8-sig',newline='') as sample:
        sample_writer=csv.writer(sample);sample_writer.writerow(schemas)
        sample_id=81973 if ids is None or 81973 in ids else ids[0]
        for phase,run in RUNS.items():
            annual=pd.read_sql_query('SELECT * FROM matriz WHERE fase=? ORDER BY pixel_id,temporada',con,params=(phase,))
            if ids is not None:annual=annual[annual.pixel_id.isin(ids)]
            if annual.empty:raise ValueError('Seleccion vacia')
            expected+=int(annual.dias_ventana.sum())
            plan_path=root/f'03_Resultados/Agroclima/vigente/probabilidades/maize_{phase}_global_1981_2016'/run/'plan.json'
            plan=json.loads(plan_path.read_text(encoding='utf-8'));sources[str(plan_path)]=sha(plan_path)
            rule=plan['identity']['rule'];minimum=1 if phase=='MAT' else int(rule['min_days'])
            phase_days=0;phase_missing=0;phase_windows=0
            with ExitStack() as stack:
                writers={}
                for year in range(1981,2017):
                    file=partition/f'{phase}_{year}.csv.gz';handle=stack.enter_context(gzip.open(file,'wt',encoding='utf-8',newline=''))
                    writers[year]=csv.writer(handle);writers[year].writerow(schemas);file_counts[file.relative_to(out).as_posix()]=0
                for i,(pid,g) in enumerate(annual.groupby('pixel_id',sort=True),1):
                    path=Path(plan['cache'])/f'{int(pid)}.json.gz';digest=sha(path)
                    if digest!=json.loads(path.with_suffix('.sha.json').read_text())['sha256']:raise ValueError(f'Cache alterado: {path}')
                    # Store cache provenance in a compact append-only manifest.
                    with (out/'fuentes_cache.csv').open('a',encoding='utf-8',newline='') as f:
                        writer=csv.writer(f)
                        if f.tell()==0:writer.writerow(['ruta','sha256'])
                        writer.writerow([str(path),digest])
                    with gzip.open(path,'rt',encoding='utf-8') as f:cache=json.load(f)
                    for row in g.itertuples():
                        cells=cache[str(row.temporada)]
                        for cell in cells:
                            if cell['phase']!=phase or int(cell['season_year'])!=row.temporada or int(cell['pixel_id'])!=pid:raise ValueError('Clave de cache distinta')
                            if cell['phase_start']!=row.inicio or cell['phase_end']!=row.fin:raise ValueError('Fechas distintas')
                            if cell['threshold']!=row.umbral or cell['operator']!=row.operador or cell['min_days']!=row.duracion_min_dias or cell['variable']!=row.variable_climatica:raise ValueError('Regla distinta')
                        affected,counts,signature=reconstruct(cells,minimum,phase=='MAT')
                        if int(pid) not in support:support[int(pid)]=signature
                        if signature!=support[int(pid)]:raise ValueError('Soporte espacial no fijo entre temporadas/fases')
                        dates=pd.date_range(row.inicio,row.fin)
                        if len(dates)!=len(affected) or len(dates)!=row.dias_validos:raise ValueError('Duracion no coincide')
                        if not np.isclose(affected.sum(),row.dias_afectados_equiv,rtol=1e-8,atol=1e-8) or not np.isclose(counts.sum(),row.conteo_original,rtol=1e-8,atol=1e-8):raise ValueError('Exposicion diaria no reproduce matriz anual')
                        v=rmm.reindex(dates);o=oni.reindex(dates.to_period('M').to_timestamp()).to_numpy(float)
                        cat=np.where(np.isnan(o),None,np.where(o<=-.5,'frio',np.where(o>=.5,'calido','neutral')))
                        valid_mjo=v.mjo_valida.fillna(False).to_numpy(bool);valid=valid_mjo&np.isfinite(o)
                        rows=[]
                        for j,date in enumerate(dates):
                            r=v.iloc[j]
                            values=[int(pid),row.latitud,row.longitud,int(row.temporada),phase,date.strftime('%Y-%m-%d'),int(date.month),
                                float(affected[j]),float(counts[j]),o[j],cat[j],r.rmm1,r.rmm2,r.fase_mjo,r.amplitud_mjo,
                                r.estado_mjo,bool(valid_mjo[j]),bool(valid[j]),row.estado_cobertura_espacial,row.fraccion_area_climatica_util]
                            rows.append(['' if x is None or (isinstance(x,(float,np.floating)) and not np.isfinite(x)) else x for x in values])
                        writers[row.temporada].writerows(rows)
                        if int(pid)==sample_id:sample_writer.writerows(rows)
                        n=len(rows);phase_days+=n;phase_windows+=1;phase_missing+=int((~valid).sum());total+=n
                        file_counts[f'diario_por_fase_temporada/{phase}_{row.temporada}.csv.gz']+=n
                    if i==1 or i%256==0 or i==annual.pixel_id.nunique():print(f'{phase}: {i:,}/{annual.pixel_id.nunique():,} pixeles | {total:,} filas diarias',flush=True)
            quality.append(dict(fase=phase,pixeles=int(annual.pixel_id.nunique()),ventanas=phase_windows,filas_diarias=phase_days,sin_par_oni_mjo=phase_missing,discrepancias_anuales=0))
    if total!=expected:raise ValueError('No coinciden filas diarias esperadas')
    print('Verificando lectura completa de los CSV gzip...',flush=True)
    for file,n in file_counts.items():
        with gzip.open(out/file,'rt',encoding='utf-8',newline='') as f:
            reader=csv.reader(f)
            if next(reader)!=schemas:raise ValueError('Esquema CSV distinto')
            if sum(1 for _ in reader)!=n:raise ValueError('Exportacion truncada')
    pd.DataFrame(quality).to_csv(out/'control_calidad.csv',index=False,encoding='utf-8-sig')
    (out/'esquema_columnas.json').write_text(json.dumps(schemas,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'LEEME.txt').write_text('Tabla B diaria global: una fila = pixel x temporada x fase_cultivo x fecha.\n216 particiones CSV.gz (fase y temporada), sin limite Excel. Ceros reales se conservan y faltantes quedan vacios.\nMJO debil: amplitud <=1; activa: >1 con fases 1..8. Codigos invalidos quedan vacios, nunca debil por defecto.\nONI del mes centrado repetido por fecha, no observaciones independientes; no es ONI promedio de ventana.\nTodos los dias climaticos se conservan aunque falte ONI/MJO. Filtrar par_clima_oni_mjo_valido para ese cruce.\nDatos sobre soporte espacial fijo verificado; no extrapolan al area sin datos.\nLos dias afectados incluyen todos los dias de rachas que cumplen duracion. Ocurrencias de calor se anotan el dia de calificacion de cada episodio; MAT cuenta dias.\nNo se calcularon todavia probabilidades estratificadas o IC: se construyo la tabla diaria para ese analisis.\nSin GEE, sin nuevas descargas. Usar solo salidas con completed.json.\n',encoding='utf-8')
    (out/'completed.json').write_text(json.dumps(dict(filas_diarias=total,particiones=len(file_counts),filas_por_archivo=file_counts,piloto=ids is not None,
        pixeles=len(known) if ids is None else len(ids),pixel_ejemplo=sample_id,fases=list(RUNS),
        clave=['pixel_id','temporada','fase_cultivo','fecha'],fuentes_sha256=sources,cache_manifest='fuentes_cache.csv',
        controles=quality,discrepancias_matriz_anual=0,segundos=round(time.perf_counter()-started,2)),ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'COMPLETO: {out}',flush=True)


if __name__=='__main__':main()
