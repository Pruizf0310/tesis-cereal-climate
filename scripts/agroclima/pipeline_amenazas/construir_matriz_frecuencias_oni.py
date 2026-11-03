"""Materialize the full annual hazard/ONI matrix without climate recalculation."""
from pathlib import Path
import argparse
import csv
import gzip
import hashlib
import json
import sqlite3
import sys
import time
import numpy as np
import pandas as pd
from correlacion_oni_amenazas import read_oni, window_oni
from rutas_resultados_oni import resultados_oni

ROOT = Path('C:/Users/paola/Tesis')
BASE = ROOT / '03_Resultados/Agroclima/vigente'
OUT = None
RUNS = dict(EST='01118480a325e93d', VEG='0955242f426ffa57', REP='ba9e0e3286c7e384',
            FLO='4e3c0e35ac33f725', FIL='a445419ee76712f0', MAT='a7342fb2d9bf24a2')
KEY = ['pixel_id', 'season_year', 'phase']


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    global ROOT, BASE, OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT, help='Raíz de la tesis con 01_Data, 02_Procesados y 03_Resultados.')
    parser.add_argument('--output', type=Path, help='Carpeta NUEVA de salida. Nunca se sobrescriben resultados.')
    args = parser.parse_args()
    ROOT = args.root.resolve()
    BASE = ROOT/'03_Resultados/Agroclima/vigente'
    OUT = args.output.resolve() if args.output else resultados_oni(ROOT) / ('matriz_frecuencias_ONI_' + time.strftime('%Y%m%d_%H%M%S'))
    started = time.perf_counter()
    if OUT.exists():
        parser.error(f'La carpeta ya existe; indica otra con --output: {OUT}')
    OUT.mkdir(parents=True, exist_ok=False)
    original = BASE/'ejecuciones/maize_seis_fases_GEE_1981_2016/resumen_GDHY_anual.csv'
    pixels = ROOT/'02_Procesados/Pixeles_correlacion_vigentes/pixeles_maize.csv'
    oni_path = ROOT/'01_Data/ONI/ONI_v6_2026-10-08.html'
    sources = [original, pixels, oni_path, Path(__file__), Path(__file__).with_name('correlacion_oni_amenazas.py')]
    coords = pd.read_csv(pixels, usecols=['pixel_id', 'latitude', 'longitude'])
    assert len(coords) == 10923 and not coords.pixel_id.duplicated().any()
    oni, origin, sums, missing = read_oni(oni_path)
    oni.rename('oni').to_csv(OUT/'oni_mensual_fuente.csv', index_label='mes')
    columns = KEY + ['start', 'end', 'quality', 'mean_count_per_native_cell',
                     'variable', 'operator', 'threshold', 'min_days', 'count_unit',
                     'coverage_fraction']
    print('Leyendo conteos y calendario originales...', flush=True)
    raw = pd.read_csv(original, usecols=columns,
                      dtype={c:'category' for c in ['phase','quality','variable','operator','count_unit']})
    assert len(raw) == 10923*36*6
    assert not raw.duplicated(KEY).any()
    assert set(raw.pixel_id) == set(coords.pixel_id)
    assert set(raw.season_year) == set(range(1981,2017))
    pending = OUT/'matriz_frecuencias_ONI.pending.sqlite'
    con = sqlite3.connect(pending)
    con.execute('PRAGMA journal_mode=DELETE')
    con.execute('PRAGMA synchronous=NORMAL')
    stats = []
    examples = []
    with gzip.open(OUT/'matriz_frecuencias_ONI.csv.gz', 'wt', encoding='utf-8', newline='') as stream:
        for phase, run in RUNS.items():
            folder = BASE/f'probabilidades/maize_{phase}_global_1981_2016'/run
            annual = folder/'annual_exposure_for_yield_alignment.csv'
            plan_path = folder/'plan.json'
            sources.extend([annual, plan_path, folder/'completed.json'])
            plan = json.loads(plan_path.read_text(encoding='utf-8'))
            rule = plan['identity']['rule']
            assert rule['phase'] == phase
            a = pd.read_csv(annual)
            assert not a.duplicated(KEY).any()
            assert a.phase.eq(phase).all() and a.pixel_id.isin(coords.pixel_id).all()
            assert a.season_year.between(1981,2016).all()
            d = raw.loc[raw.phase.eq(phase)].copy()
            assert len(d) == 10923*36
            for col, expected in [('threshold',rule['threshold']),('min_days',rule['min_days']),
                                  ('variable',rule['variable']),('operator',rule['operator']),('count_unit',rule['count_unit'])]:
                assert d[col].eq(expected).all(), (phase,col,'reglas distintas')
            d = d.merge(coords, on='pixel_id', how='left', validate='many_to_one')
            a = a.rename(columns={'latitude':'daily_lat','longitude':'daily_lon'})
            d = d.merge(a, on=KEY, how='left', validate='one_to_one', indicator=True)
            matched = d['_merge'].eq('both')
            assert np.allclose(d.loc[matched,'latitude'], d.loc[matched,'daily_lat'])
            assert np.allclose(d.loc[matched,'longitude'], d.loc[matched,'daily_lon'])
            start = pd.to_datetime(d.start)
            end = pd.to_datetime(d.end)
            duration = (end-start).dt.days+1
            assert duration.gt(0).all()
            assert (d.valid_days.dropna() > 0).all()
            assert (d.valid_days.fillna(0) <= duration).all()
            valid = d.quality.eq('OK') & d.valid_days.eq(duration)
            valid &= np.isfinite(d.mean_count_per_native_cell) & np.isfinite(d.affected_days_equivalent)
            agree = np.isclose(d.mean_count_per_native_cell, d.episodes_mean_native_cell, rtol=1e-8, atol=1e-8)
            mismatch = valid & ~agree
            if mismatch.any():
                d.loc[mismatch].to_csv(OUT/f'discrepancias_{phase}.csv',index=False)
                raise ValueError(f'{phase}: {int(mismatch.sum())} conteos diarios no coinciden con originales')
            assert d.loc[valid,'affected_days_equivalent'].between(-1e-9, duration[valid]+1e-8).all()
            assert d.loc[valid,'mean_count_per_native_cell'].ge(0).all()
            x = pd.DataFrame({
                'pixel_id':d.pixel_id, 'latitud':d.latitude, 'longitud':d.longitude,
                'temporada':d.season_year, 'fase':phase, 'inicio':d.start, 'fin':d.end,
                'dias_ventana':duration, 'dias_validos':d.valid_days.astype('Int64'),
                'episodios':d.mean_count_per_native_cell.where(valid & (phase != 'MAT')),
                'dias_afectados_equiv':d.affected_days_equivalent.where(valid),
                'episodios_100d':(100*d.mean_count_per_native_cell/d.valid_days).where(valid & (phase != 'MAT')),
                'pct_dias_afectados':(100*d.affected_days_equivalent/d.valid_days).where(valid),
                'oni_ventana':window_oni(d.start, d.end, origin, sums, missing),
                'cat_oni':None,
                'estado_cobertura':np.where(valid,'completa',np.where(~matched,'sin_exposicion_anual','incompleta')),
                'calidad_origen':d.quality.astype(str),
                'fraccion_cobertura_origen':d.coverage_fraction,
                'variable_climatica':d.variable.astype(str), 'operador':d.operator.astype(str),
                'umbral':d.threshold, 'duracion_min_dias':d.min_days,
                'unidad_conteo_origen':d.count_unit.astype(str),
                'conteo_original':d.mean_count_per_native_cell.where(d.quality.eq('OK')),
                'par_frecuencia_oni_valido':False})
            # Centered monthly values are source decimals; eliminate only cumulative-sum
            # cancellation noise before applying inclusive +/-0.5 boundaries.
            x.oni_ventana = x.oni_ventana.round(12)
            x.loc[x.oni_ventana.notna(),'cat_oni'] = 'neutral'
            x.loc[x.oni_ventana.le(-.5),'cat_oni'] = 'frio'
            x.loc[x.oni_ventana.ge(.5),'cat_oni'] = 'calido'
            x['par_frecuencia_oni_valido'] = valid & x.oni_ventana.notna()
            x = x.sort_values(['pixel_id','temporada']).reset_index(drop=True)
            x.to_csv(stream,index=False,header=(phase=='EST'),na_rep='')
            x.to_sql('matriz',con,index=False,if_exists='append',chunksize=5000)
            examples.append(x.loc[x.pixel_id.eq(coords.pixel_id.min())].copy())
            stats.append(dict(fase=phase, filas=len(x), pixeles=int(x.pixel_id.nunique()),
                completas=int(valid.sum()), incompletas=int((~valid).sum()),
                sin_exposicion_anual=int((~matched).sum()), sin_oni=int(x.oni_ventana.isna().sum()),
                pares_validos=int(x.par_frecuencia_oni_valido.sum()),
                ceros_validos=int((valid & d.mean_count_per_native_cell.eq(0)).sum()),
                discrepancias_conteo=int(mismatch.sum()),
                fria=int(x.cat_oni.eq('frio').sum()),neutral=int(x.cat_oni.eq('neutral').sum()),
                calida=int(x.cat_oni.eq('calido').sum())))
            print(f'{phase}: {len(x):,} filas; {int(valid.sum()):,} completas; coincidencia conteos OK',flush=True)
    del raw
    con.execute('CREATE UNIQUE INDEX clave_matriz ON matriz(pixel_id,temporada,fase)')
    con.execute('CREATE INDEX grupos_oni ON matriz(fase,cat_oni,par_frecuencia_oni_valido)')
    con.execute('CREATE INDEX temporadas ON matriz(temporada)')
    assert con.execute('SELECT count(*) FROM matriz').fetchone()[0] == 2359368
    assert con.execute('SELECT count(*) FROM matriz WHERE fase="MAT" AND (episodios IS NOT NULL OR episodios_100d IS NOT NULL)').fetchone()[0] == 0
    assert con.execute('SELECT count(*) FROM matriz WHERE estado_cobertura<>"completa" AND (episodios IS NOT NULL OR pct_dias_afectados IS NOT NULL)').fetchone()[0] == 0
    assert con.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    pd.DataFrame(stats).to_csv(OUT/'control_calidad.csv',index=False)
    sample = pd.concat(examples).sort_values(['pixel_id','temporada','fase'],key=lambda s:s.map({p:i for i,p in enumerate(RUNS)}) if s.name=='fase' else s)
    sample.to_csv(OUT/'ejemplo_un_pixel_216_filas.csv',index=False,encoding='utf-8-sig')
    # Independent ONI check: direct calendar-month day weighting for every unique window.
    windows = pd.read_sql_query('SELECT DISTINCT inicio,fin,oni_ventana FROM matriz',con)
    max_error = 0.
    for row in windows.itertuples(index=False):
        dates = pd.date_range(row.inicio,row.fin)
        vals = oni.reindex(dates.to_period('M').to_timestamp()).to_numpy()
        expected = float(np.mean(vals))
        if np.isnan(expected):
            assert pd.isna(row.oni_ventana)
        else:
            error = abs(expected-row.oni_ventana)
            assert error < 1e-9
            max_error = max(max_error,error)
    print(f'ONI comprobado independientemente en {len(windows):,} ventanas distintas',flush=True)
    # Round-trip compressed CSV and compare all numerical columns and NULL counts.
    numerical = ['pixel_id','latitud','longitud','temporada','dias_ventana','dias_validos','episodios',
                 'dias_afectados_equiv','episodios_100d','pct_dias_afectados','oni_ventana','conteo_original']
    totals = {c:0. for c in numerical}; nulls = {c:0 for c in numerical}; rows = 0
    for chunk in pd.read_csv(OUT/'matriz_frecuencias_ONI.csv.gz',chunksize=100000):
        rows += len(chunk)
        for c in numerical:
            totals[c] += float(chunk[c].sum()); nulls[c] += int(chunk[c].isna().sum())
    assert rows == 2359368
    for c in numerical:
        total, count = con.execute(f'SELECT sum({c}),count({c}) FROM matriz').fetchone()
        assert np.isclose(totals[c],total,rtol=1e-9,atol=1e-6), c
        assert nulls[c] == rows-count, c
    hashes = {str(p):sha(p) for p in sources}
    manifest = dict(filas=rows,pixeles=10923,temporadas=[1981,2016],fases=list(RUNS),
                    clave=['pixel_id','temporada','fase'],columnas=list(sample.columns),
                    fuentes_sha256=hashes,control_por_fase=stats,
                    comprobacion_oni=dict(ventanas_unicas=len(windows),error_maximo=max_error),
                    csv_sqlite_coinciden=True,sqlite_integridad='ok',
                    segundos=round(time.perf_counter()-started,2))
    pd.DataFrame([{'ruta':p,'sha256':h} for p,h in hashes.items()]).to_sql('fuentes',con,index=False)
    pd.DataFrame(stats).to_sql('control_calidad',con,index=False)
    con.commit(); con.close()
    pending.rename(OUT/'matriz_frecuencias_ONI.sqlite')
    (OUT/'completed.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'LEEME.txt').write_text(
        'Matriz completa: una fila por pixel, temporada y fase.\n'
        'SQLite: tabla matriz. CSV gzip: mismos datos; vacios = faltantes/no aplicable; ceros validos conservados.\n'
        'Clave: pixel_id, temporada, fase. 2.359.368 filas; no cabe en una hoja Excel.\n'
        'episodios = promedio espacial del conteo original; episodios_100d = episodios/dias_validos*100.\n'
        'MAT cuenta dias de lluvia: episodios y episodios_100d quedan vacios.\n'
        'dias_afectados_equiv = suma de fracciones diarias de area afectada; pct_dias_afectados = 100*dias_afectados_equiv/dias_validos.\n'
        'oni_ventana = ONI mensual centrado ponderado por dias de la ventana, incluidos inicio y fin.\n'
        'cat_oni: frio <= -0.5; neutral entre -0.5 y 0.5; calido >= 0.5.\n'
        'Ventanas incompletas: medidas de exposicion vacias; se conserva calidad y fechas.\n'
        'Filtro para comparar frecuencias con ONI: par_frecuencia_oni_valido = 1.\n'
        'Fuentes y hashes: completed.json y tabla fuentes. Comprobaciones: control_calidad.csv.\n'
        'El ejemplo de un pixel contiene 216 filas reales; no sustituye la matriz completa.\n'
        'No incluye rendimiento, MJO, contrastes ni intervalos. No recalcula clima ni consulta GEE.\n',encoding='utf-8')
    print(json.dumps(manifest['control_por_fase'],ensure_ascii=False,indent=2),flush=True)
    print(f'COMPLETO: {OUT}',flush=True)


if __name__ == '__main__':
    main()
