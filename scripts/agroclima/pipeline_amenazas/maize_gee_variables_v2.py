"""Variables nuevas de la tabla maestra v2 de maíz, calculadas en GEE por píxel GDHY, temporada y fase.

Por cada celda nativa de ERA5-Land (antes de promediar al píxel GDHY de 0,5°), dentro de la ventana de cada fase:
  p_mm         Σ precipitación diaria (mm)
  et0_mm       Σ ET0 de Hargreaves (FAO-56 ec. 52): 0,0023·0,408·Ra·(Tmedia+17,8)·√(Tmax−Tmin), Ra por latitud y día
  p_menos_et0  p_mm − et0_mm (sequía; el corte Q1 se aplica después, por píxel, sobre 1981–2016)
  edd29        Σ max(0, Tmax − 29 °C) (grados-día extremos; Anderson et al. 2020)
  Solo FLO y FIL, umbrales corregidos de la v2 (Li et al. 2025, EJA):
  rachas_v2    número de rachas ≥ 2 d con Tmax ≥ umbral (FLO 34,8 °C; FIL 32,9 °C)
  dias_racha_v2 días que pertenecen a esas rachas (para el % de días de la fase)
Luego se promedia en el píxel GDHY ponderando por cos(lat), solo con celdas de cobertura diaria completa.
Mismo calendario (maize-maize__rf.json, v4), mismos píxeles y mismo día UTC que el cálculo auditado del 8 oct.
Reanudable por lotes. Uso:
  .venv/Scripts/python.exe maize_gee_variables_v2.py --limit 30 --workers 8      (piloto)
  .venv/Scripts/python.exe maize_gee_variables_v2.py --workers 12               (completo)
"""
import argparse, csv, hashlib, json, math, time
import concurrent.futures as futures
from datetime import date, timedelta
from pathlib import Path

import pipeline as core
from maize_seis_fases import windows, STAGES
from maize_gee import read_pixels, count_arrays

UMBRAL_V2 = {'FLO': 34.8, 'FIL': 32.9}
EDD_TC = 29.0
CAMPOS = ['p_mm', 'et0_mm', 'p_menos_et0', 'edd29', 'rachas_v2', 'dias_racha_v2']


def feature(ee, pixel, phase, w):
    start = w['start']; end = (date.fromisoformat(w['end']) + timedelta(days=1)).isoformat()
    total = (date.fromisoformat(end) - date.fromisoformat(start)).days
    col = (ee.ImageCollection(core.DATASET).filterDate(start, end)
           .select(['temperature_2m_max', 'temperature_2m_min', 'total_precipitation_sum']).sort('system:time_start'))
    proj = ee.ImageCollection(core.DATASET).first().select('temperature_2m_max').projection()
    lat = ee.Image.pixelLonLat().select('latitude').multiply(math.pi / 180)

    def diaria(img):
        tmax = img.select('temperature_2m_max').subtract(273.15)
        tmin = img.select('temperature_2m_min').subtract(273.15)
        p = img.select('total_precipitation_sum').multiply(1000)
        j = ee.Date(img.get('system:time_start')).getRelative('day', 'year').add(1)
        ang = j.multiply(2 * math.pi / 365)
        dr = ee.Number(1).add(ang.cos().multiply(0.033))
        dec = ang.subtract(1.39).sin().multiply(0.409)
        ws = lat.tan().multiply(dec.tan()).multiply(-1).clamp(-1, 1).acos()
        ra = (ws.multiply(lat.sin()).multiply(dec.sin()).add(lat.cos().multiply(dec.cos()).multiply(ws.sin()))
              .multiply(24 * 60 / math.pi * 0.0820).multiply(dr))
        tmean = tmax.add(tmin).divide(2)
        et0 = (ra.multiply(0.408 * 0.0023).multiply(tmean.add(17.8))
               .multiply(tmax.subtract(tmin).max(0).sqrt())).max(0)
        edd = tmax.subtract(EDD_TC).max(0)
        return (p.rename('p_mm').addBands(et0.rename('et0_mm')).addBands(edd.rename('edd29'))
                .addBands(tmax.rename('tmax')).addBands(tmax.mask().rename('ok')))

    d = col.map(diaria)
    sums = d.select(['p_mm', 'et0_mm', 'edd29']).sum()
    valid = d.select('tmax').count().rename('valid_days')
    img = sums.addBands(sums.select('p_mm').subtract(sums.select('et0_mm')).rename('p_menos_et0'))
    if phase in UMBRAL_V2:
        hits = d.map(lambda i: i.select('tmax').gte(UMBRAL_V2[phase]).unmask(0).toByte()).toArray().arrayProject([0])
        runs, _ = count_arrays(ee, hits, hits, 2, 'episodes')
        n = hits.arrayLength(0)
        z = ee.Image.constant(ee.Array([0]))
        prev = z.arrayCat(hits, 0).arraySlice(0, 0, n)
        nxt = hits.arraySlice(0, 1).arrayCat(z, 0)
        inrun = hits.And(prev.Or(nxt)).arrayReduce(ee.Reducer.sum(), [0]).arrayGet([0])
        img = img.addBands(runs.rename('rachas_v2')).addBands(inrun.rename('dias_racha_v2'))
    complete = valid.eq(total)
    wgt = ee.Image.pixelLonLat().select('latitude').multiply(math.pi / 180).cos().multiply(complete)
    names = img.bandNames()
    m = img.multiply(wgt).addBands(wgt.rename('weight')).addBands(complete.rename('complete_cells')) \
        .addBands(ee.Image.constant(1).rename('native_cells'))
    region = ee.Geometry.Rectangle([pixel['lon'] - .25, pixel['lat'] - .25, pixel['lon'] + .25, pixel['lat'] + .25], geodesic=False)
    stats = m.reduceRegion(reducer=ee.Reducer.sum().unweighted(), geometry=region, crs=proj, maxPixels=1000, tileScale=2)
    return ee.Feature(None, stats).set(dict(pixel_id=pixel['pixel_id'], season_year=w['season_year'], phase=phase,
                                            start=start, end=w['end'], dias_ventana=total,
                                            umbral_v2=UMBRAL_V2.get(phase)))


def batch(ee, items, data, folder, fp):
    key = hashlib.sha256(json.dumps(items, sort_keys=True).encode()).hexdigest()[:20]
    path = folder / f'batch_{key}.csv'; marker = path.with_suffix('.json')
    if path.exists() and marker.exists():
        meta = json.loads(marker.read_text())
        if meta['fingerprint'] != fp or meta['sha256'] != hashlib.sha256(path.read_bytes()).hexdigest():
            raise ValueError(f'Lote incompatible o alterado: {path}')
        return path, True
    feats = [feature(ee, p, ph, windows(data, p, ph, y, y)[0]) for p, y in items for ph in STAGES]
    rows = core.fetch_pages(ee, ee.FeatureCollection(feats))
    expected = {(p['pixel_id'], y, ph) for p, y in items for ph in STAGES}
    if {(int(r['pixel_id']), int(r['season_year']), r['phase']) for r in rows} != expected or len(rows) != len(expected):
        raise ValueError('GEE devolvió filas incompletas o duplicadas; no se guarda el lote')
    for r in rows:
        w = float(r.get('weight') or 0); cells = int(r.get('native_cells') or 0); comp = int(r.get('complete_cells') or 0)
        r['quality'] = 'OK' if cells > 0 and comp == cells else 'INCOMPLETE'
        r['coverage_fraction'] = comp / cells if cells else 0
        for c in CAMPOS:
            v = r.get(c)
            r[c] = (float(v) / w) if (v is not None and w) else None
        if r.get('dias_racha_v2') is not None:
            r['pct_dias_racha_v2'] = 100 * r['dias_racha_v2'] / int(r['dias_ventana'])
    fields = sorted({k for r in rows for k in r})
    tmp = path.with_suffix('.tmp'); core.save_csv(tmp, rows, fields=fields); tmp.replace(path)
    marker.write_text(json.dumps(dict(fingerprint=fp, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), rows=len(rows))))
    return path, False


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config', default=str(Path(__file__).with_name('config_maize_seis_fases_gee.json')))
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--workers', type=int, default=12)
    ap.add_argument('--batch-size', type=int, default=4)
    ap.add_argument('--salida', default='C:/Users/paola/Tesis/03_Resultados/Agroclima/vigente/ejecuciones/maize_variables_v2_GEE_1981_2016')
    a = ap.parse_args()
    c = json.loads(Path(a.config).read_text(encoding='utf-8'))
    pixels, origin = read_pixels(c)
    if a.limit: pixels = pixels[:a.limit]
    cal = Path(c['calendar_dir']) / 'maize-maize__rf.json'; data = json.loads(cal.read_text(encoding='utf-8'))
    sci = dict(umbral_v2=UMBRAL_V2, edd_tc=EDD_TC, et0='Hargreaves FAO-56 ec.52', stages=STAGES,
               calendar_sha256=hashlib.sha256(cal.read_bytes()).hexdigest(),
               code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    fp = hashlib.sha256(json.dumps(sci, sort_keys=True).encode()).hexdigest()
    root = Path(a.salida + (f'_piloto{a.limit}' if a.limit else '')); folder = root / 'lotes'; folder.mkdir(parents=True, exist_ok=True)
    (root / 'plan_ejecucion.json').write_text(json.dumps(sci | dict(pixeles=len(pixels), origen=origin, workers=a.workers),
                                                         ensure_ascii=False, indent=2), encoding='utf-8')
    import ee
    core.authenticate_gee(); core.initialize(c)
    items = [(p, y) for p in pixels for y in range(c['start_year'], c['end_year'] + 1)]
    batches = [items[i:i + a.batch_size] for i in range(0, len(items), a.batch_size)]
    print(f'GEE v2: {len(pixels)} píxeles × {c["end_year"] - c["start_year"] + 1} años × 6 fases; {len(batches)} lotes', flush=True)
    t0 = time.monotonic(); done = new = 0; paths = []
    it = iter(batches); pool = futures.ThreadPoolExecutor(max_workers=a.workers)
    pend = {pool.submit(batch, ee, b, data, folder, fp) for b in [next(it, None) for _ in range(a.workers)] if b}
    status = 'RUNNING'
    try:
        while pend:
            ready, pend = futures.wait(pend, timeout=30, return_when=futures.FIRST_COMPLETED)
            for j in ready:
                path, cached = j.result(); paths.append(path); done += 1; new += not cached
                el = time.monotonic() - t0; eta = el / new * (len(batches) - done) if new else 0
                if done % 200 == 0 or done == len(batches):
                    print(f'Lotes {done}/{len(batches)} | {el / 60:.1f} min | restante aprox. {eta / 3600:.2f} h', flush=True)
                    (root / 'progreso.json').write_text(json.dumps(dict(done=done, total=len(batches), elapsed_s=el, eta_s=eta)))
                b = next(it, None)
                if b: pend.add(pool.submit(batch, ee, b, data, folder, fp))
        status = 'COMPLETED'
    except Exception as e:
        status = 'FAILED'; print(f'Lote fallido: {e}. Repite el comando para retomar (los lotes completos se conservan).', flush=True); raise
    finally:
        for j in pend: j.cancel()
        pool.shutdown(wait=True, cancel_futures=True)
        (root / 'estado.json').write_text(json.dumps(dict(status=status, done=done, total=len(batches))))
    # consolidar
    out = root / 'variables_v2_por_fase.csv'; header = None
    with out.open('w', encoding='utf-8', newline='') as fh:
        wr = None
        for p in sorted(paths):
            with p.open(encoding='utf-8-sig', newline='') as s:
                rd = csv.DictReader(s)
                for row in rd:
                    if wr is None:
                        header = ['pixel_id', 'season_year', 'phase', 'start', 'end', 'dias_ventana', 'quality',
                                  'coverage_fraction', 'umbral_v2'] + CAMPOS + ['pct_dias_racha_v2']
                        wr = csv.DictWriter(fh, fieldnames=header, extrasaction='ignore'); wr.writeheader()
                    wr.writerow(row)
    print('TERMINÓ GEE v2:', out, flush=True)


if __name__ == '__main__':
    main()
