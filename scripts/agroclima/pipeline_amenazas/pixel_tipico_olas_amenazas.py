"""Olas de cada amenaza en el píxel típico: calor por fase, racha seca, calor sobre 29 °C y lluvia en maduración.

Un evento del píxel es una OLA: días seguidos en que al menos la mitad de las celdas nativas de ERA5-Land (ponderadas por
cos(lat)) están dentro de una racha de esa amenaza. La ola no se corta en el borde de las fases: se evalúa la temporada
completa y se asigna a la fase donde tiene más días; si cruza un borde queda marcado.

Amenazas (validacion_umbrales_20261104.xlsx):
  calor     Tmax ≥ umbral del bloque (reglas v3: 34,1 / 34,6 / 33,7 / 32,9 °C), racha ≥ 2 d, grado por Li 2025b Tabla 2 (R02, R06)
  seco      P < 1 mm (ETCCDI, CDD), racha ≥ 2 d (R30; el mínimo de 2 d es adaptación para que la racha sea evento)
  calor29   Tmax > 29 °C (Schlenker y Roberts 2009), racha ≥ 2 d (R31; mismo mínimo)
  lluvia    P > 10 mm, solo en MAT, ≥ 1 d (Ortega Gómez et al. 2019: sin mínimo de racha publicado)
Salida: carpeta olas_amenazas_<fecha> con olas.csv (una fila por ola), fase_anio.csv (por amenaza, fase y año: número de
olas, días en ola, ola más larga y 0/1) y resumen.json.
Uso: .venv/Scripts/python.exe pixel_tipico_olas_amenazas.py [--pixel 191325] [--desde 1981 --hasta 2016]
"""
import argparse, json, math, sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

from pixel_tipico_tendencia import SQLITE, BASE
from pixel_tipico_reglas_v3 import CONFIG, BLOQUES_V3, UMBRAL_V3, ETAPA_BLOQUE, bloques_por_dia, grado, rachas

FASE_BLOQUE = {b: f for f, bs in BLOQUES_V3.items() for b in bs}
FASES = list(BLOQUES_V3)
AMENAZAS = {
    'calor': dict(bloques=[b for b in FASE_BLOQUE if b in UMBRAL_V3], min_dias=2,
                  hit=lambda r: r.tmax_c >= UMBRAL_V3[r.bloque], regla='Tmax ≥ umbral del bloque (v3)'),
    'seco': dict(bloques=list(FASE_BLOQUE), min_dias=2, hit=lambda r: r.p_mm < 1, regla='P < 1 mm (ETCCDI CDD)'),
    'calor29': dict(bloques=list(FASE_BLOQUE), min_dias=2, hit=lambda r: r.tmax_c > 29, regla='Tmax > 29 °C (Schlenker y Roberts 2009)'),
    'lluvia': dict(bloques=BLOQUES_V3['MAT'], min_dias=1, hit=lambda r: r.p_mm > 10, regla='P > 10 mm en MAT (Ortega Gómez et al. 2019)'),
}


def fraccion(diario, mapa, am):
    """Fracción ponderada de celdas en racha, por día de la ventana de la amenaza."""
    dias = sorted(d for d, b in mapa.items() if b in am['bloques'])
    w = diario[(diario.f >= dias[0]) & (diario.f <= dias[-1])].copy()
    w['bloque'] = w.f.map(mapa)
    en_racha, pesos = pd.Series(0.0, index=dias), 0.0
    for (clon, clat), g in w.groupby(['lon', 'lat']):
        g = g.sort_values('f')
        if len(g) != len(dias) or g[['tmax_c', 'p_mm']].isna().any().any():
            continue  # celda sin todos los días: fuera, como en GEE
        peso = math.cos(clat * math.pi / 180)
        marca = [0] * len(dias)
        for i, largo in rachas([bool(am['hit'](r)) for r in g.itertuples()], min_dias=am['min_dias']):
            for k in range(i, i + largo): marca[k] = 1
        en_racha += peso * pd.Series(marca, index=dias)
        pesos += peso
    return pd.DataFrame(dict(fecha=dias, bloque=[mapa[d] for d in dias], frac=(en_racha / pesos).values))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pixel', type=int, default=191325)
    ap.add_argument('--desde', type=int, default=1981)
    ap.add_argument('--hasta', type=int, default=2016)
    a = ap.parse_args()
    c = json.loads(CONFIG.read_text(encoding='utf-8'))
    data = json.loads((Path(c['calendar_dir']) / 'maize-maize__rf.json').read_text(encoding='utf-8'))
    con = sqlite3.connect(SQLITE)
    ref = pd.read_sql("select latitud, longitud from pares_v2 where pixel_id=? limit 1", con, params=(a.pixel,))
    lat, lon = float(ref.latitud.iloc[0]), float(ref.longitud.iloc[0])
    cal = dict(templates=data['templates'], pixel=data['pixels'][f'{lat:.2f},{lon:.2f}'])

    carpeta = BASE / f'pixel_{a.pixel}'
    archivo = carpeta / 'diario_celdas_nativas_1950_2024.csv.gz'
    if not archivo.exists():
        archivo = carpeta / 'diario_celdas_nativas_1981_2016.csv.gz'
    diario = pd.read_csv(archivo)
    diario['f'] = pd.to_datetime(diario.fecha).dt.date

    olas, resumen = [], []
    for anio in range(a.desde, a.hasta + 1):
        mapa = bloques_por_dia(cal, anio)
        for nombre, am in AMENAZAS.items():
            g = fraccion(diario, mapa, am)
            for i, largo in rachas(list(g.frac >= 0.5), min_dias=am['min_dias']):
                t = g.iloc[i:i + largo]
                fases = [FASE_BLOQUE[b] for b in t.bloque]
                orden = list(dict.fromkeys(fases))
                fase = max(orden, key=fases.count)  # la fase con más días; empate: la primera
                b = t.bloque.value_counts().index[0]
                olas.append(dict(amenaza=nombre, anio=anio, inicio=t.fecha.iloc[0].isoformat(), fin=t.fecha.iloc[-1].isoformat(),
                                 dias=largo, fase=fase, fases=' → '.join(orden),
                                 dias_por_fase=' + '.join(str(fases.count(f)) for f in orden), cruza_borde=len(orden) > 1,
                                 grado=grado(largo, ETAPA_BLOQUE[b]) if nombre == 'calor' else ''))
    ol = pd.DataFrame(olas)

    for nombre, am in AMENAZAS.items():
        fases_am = list(dict.fromkeys(FASE_BLOQUE[b] for b in am['bloques']))
        for anio in range(a.desde, a.hasta + 1):
            for f in fases_am:
                s = ol[(ol.amenaza == nombre) & (ol.anio == anio) & (ol.fase == f)] if len(ol) else ol
                resumen.append(dict(amenaza=nombre, anio=anio, fase=f, olas=len(s), hubo_ola=int(len(s) > 0),
                                    dias_en_ola=int(s.dias.sum()) if len(s) else 0, ola_max=int(s.dias.max()) if len(s) else 0,
                                    moderada_o_mas=int(s.grado.isin(['moderado', 'severo']).any()) if nombre == 'calor' and len(s) else ''))
    fa = pd.DataFrame(resumen)

    out = BASE / f'olas_amenazas_{datetime.now():%Y%m%d_%H%M%S}'
    out.mkdir()
    ol.to_csv(out / 'olas.csv', index=False)
    fa.to_csv(out / 'fase_anio.csv', index=False)
    (out / 'resumen.json').write_text(json.dumps(dict(
        pixel=a.pixel, anios=[a.desde, a.hasta], diario=str(archivo),
        criterio_ola='días seguidos con ≥ 50 % de las celdas (ponderadas por cos(lat)) en racha de la amenaza; la ola se asigna a la fase con más días',
        reglas={k: dict(regla=v['regla'], min_dias=v['min_dias']) for k, v in AMENAZAS.items()},
        olas_por_amenaza=ol.amenaza.value_counts().to_dict(),
        cruzan_borde=ol.groupby('amenaza').cruza_borde.sum().astype(int).to_dict()), ensure_ascii=False, indent=1), encoding='utf-8')
    print(out)
    print(fa.pivot_table(index=['amenaza', 'fase'], values=['olas', 'hubo_ola', 'dias_en_ola', 'ola_max'],
                         aggfunc={'olas': 'sum', 'hubo_ola': 'sum', 'dias_en_ola': 'mean', 'ola_max': 'max'}).round(1).to_string())


if __name__ == '__main__':
    main()
