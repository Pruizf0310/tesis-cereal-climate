"""Serie diaria ERA5-Land de UN píxel GDHY (0,5°) para el análisis pedagógico del píxel típico.

Baja Tmax, Tmin (°C) y precipitación (mm/día) de cada celda nativa de ERA5-Land (~0,1°) cuyo centro cae dentro
del píxel GDHY, con la misma colección, proyección y recorte que maize_gee_variables_v2.py. Uno por año
(1981–2016 por defecto; --desde 1950 --hasta 2024 para el tramo ONI → amenaza, que no necesita rendimiento), meses marzo–noviembre (la ventana del maíz de secano en el hemisferio norte cabe holgada).
Uso:
  .venv/Scripts/python.exe pixel_tipico_descarga.py --pixel 191325
"""
import argparse, json
from pathlib import Path

import pandas as pd

import pipeline as core

BASE = Path('C:/Users/paola/Tesis/03_Resultados/Agroclima/vigente/pixel_tipico')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pixel', type=int, default=191325)
    ap.add_argument('--config', default=str(Path(__file__).with_name('config_maize_seis_fases_gee.json')))
    ap.add_argument('--meses', default='3-11', help='rango de meses inclusivo, p. ej. 3-11')
    ap.add_argument('--desde', type=int, default=1981)
    ap.add_argument('--hasta', type=int, default=2016)
    a = ap.parse_args()
    c = json.loads(Path(a.config).read_text(encoding='utf-8'))
    from maize_gee import read_pixels
    pixels, _ = read_pixels(c)
    p = next(x for x in pixels if int(x['pixel_id']) == a.pixel)
    m0, m1 = (int(v) for v in a.meses.split('-'))
    out = BASE / f'pixel_{a.pixel}'; out.mkdir(parents=True, exist_ok=True)
    ee = core.initialize(c)
    proj = ee.ImageCollection(core.DATASET).first().select('temperature_2m_max').projection()
    info = proj.getInfo()
    region = ee.Geometry.Rectangle([p['lon'] - .25, p['lat'] - .25, p['lon'] + .25, p['lat'] + .25], geodesic=False)
    partes = []
    for y in range(a.desde, a.hasta + 1):
        f = out / f'diario_{y}.csv'
        if f.exists():
            partes.append(pd.read_csv(f)); continue
        end = f'{y + 1}-01-01' if m1 == 12 else f'{y}-{m1 + 1:02d}-01'
        col = (ee.ImageCollection(core.DATASET).filterDate(f'{y}-{m0:02d}-01', end)
               .select(['temperature_2m_max', 'temperature_2m_min', 'total_precipitation_sum']))
        rows = col.getRegion(region, crs=info['crs'], crsTransform=info['transform']).getInfo()
        d = pd.DataFrame(rows[1:], columns=rows[0])
        d['fecha'] = pd.to_datetime(d['time'], unit='ms').dt.strftime('%Y-%m-%d')
        d = pd.DataFrame(dict(fecha=d.fecha, lon=d.longitude.round(4), lat=d.latitude.round(4),
                              tmax_c=d.temperature_2m_max - 273.15, tmin_c=d.temperature_2m_min - 273.15,
                              p_mm=d.total_precipitation_sum * 1000))
        d.to_csv(f, index=False); partes.append(d)
        print(y, len(d), 'filas', d[['lon', 'lat']].drop_duplicates().shape[0], 'celdas', flush=True)
    todo = pd.concat(partes, ignore_index=True)
    todo.to_csv(out / f'diario_celdas_nativas_{a.desde}_{a.hasta}.csv.gz', index=False)
    (out / 'procedencia.json').write_text(json.dumps(dict(
        pixel_id=a.pixel, lat=p['lat'], lon=p['lon'], dataset=core.DATASET, proyeccion=info,
        caja=[p['lon'] - .25, p['lat'] - .25, p['lon'] + .25, p['lat'] + .25], meses=[m0, m1], anios=[a.desde, a.hasta],
        celdas=int(todo[['lon', 'lat']].drop_duplicates().shape[0]), filas=len(todo),
        nota='Celdas nativas con centro dentro del píxel GDHY; misma colección y proyección que maize_gee_variables_v2.py'),
        indent=1, ensure_ascii=False), encoding='utf-8')
    print('listo', out)


if __name__ == '__main__':
    main()
