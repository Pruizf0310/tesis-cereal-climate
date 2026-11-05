"""Reglas v3 de maíz en el píxel típico, recalculadas en local desde el diario ERA5-Land de sus celdas nativas.

Decisiones del 3 nov 2026:
  VEG completo: las tres variables (rachas, EDD29, P − ETP) en V1–VT, 64 días en Nebraska. El calor usa el umbral de
      cada subfase de Li et al. (2025a, EJA 127729, p. 8): ≥ 34,1 °C en VE–V6 (bloque V1_V6) y ≥ 34,6 °C en V6–VT (V7_VT).
      La racha se evalúa sobre los 64 días seguidos: un día cuenta si supera el umbral de su subfase.
  FLO: 33,7 °C (R1–R3 en Li et al. 2025a); 34,8 °C (VT–R1) queda como sensibilidad.
  FIL: 32,9 °C (R3–R6, Youden en Li et al. 2025a) en lugar de 32,7 °C (Li et al. 2025b, que cita otros trabajos).
  Severidad de cada evento por su duración en días seguidos, Tabla 2 de Li et al. (2025b, Agronomy 15:1545, p. 7):
      por debajo del límite inferior de «leve» el evento cuenta, pero queda «bajo leve» (la fuente incluye eventos ≥ 2 d).
      Las rachas se cortan en el borde de la fase, igual que el conteo de v1.

Mismo método que maize_seis_fases.py y maize_gee_variables_v2.py: umbral y rachas en cada celda nativa (~0,1°), luego
media ponderada por cos(lat) de las celdas con todos los días válidos. Antes de aplicar las decisiones, el script
reproduce v1 (VEG = V7_VT, FIL 32,7 °C) y lo compara con pares_v2 del SQLite: si no coincide, se detiene.
Entrada: pixel_<id>/diario_celdas_nativas_1981_2016.csv.gz (pixel_tipico_descarga.py).
Salida: carpeta reglas_v3_<fecha> con fases.csv (formato de pares_v2 para pixel_tipico_correlaciones.py --fases),
eventos.csv, severidad.csv, validacion_v1.csv y resumen.json.
Uso: .venv/Scripts/python.exe pixel_tipico_reglas_v3.py [--pixel 191325]
"""
import argparse, json, math, sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

import pipeline as core
from pixel_tipico_tendencia import SQLITE, BASE, ANIOS

CONFIG = Path(__file__).with_name('config_maize_seis_fases_gee.json')
EDD_TC = 29.0
# Bloques del calendario que forman cada fase en v1 y en v3
BLOQUES_V1 = {'EST': ['VE'], 'VEG': ['V7_VT'], 'FLO': ['R1'], 'REP': ['R2'], 'FIL': ['R3', 'R4_R5'], 'MAT': ['R6']}
BLOQUES_V3 = BLOQUES_V1 | {'VEG': ['V1_V6', 'V7_VT']}
# Umbral de calor por bloque (Tmax ≥, °C)
UMBRAL_V1 = {'VE': 34.0, 'V7_VT': 34.6, 'R1': 33.7, 'R2': 33.7, 'R3': 32.7, 'R4_R5': 32.7}
UMBRAL_V3 = UMBRAL_V1 | {'V1_V6': 34.1, 'R3': 32.9, 'R4_R5': 32.9}
# Tabla 2 de Li et al. (2025b): límites leve / moderado / severo (días) por etapa de la fuente
SEVERIDAD = {'V0–VE': (2.5, 4.7, 7.7), 'VE–V6': (3.7, 5.9, 8.6), 'V6–VT': (3.5, 5.4, 7.5),
             'VT–R1': (2.3, 4.5, 7.9), 'R1–R3': (2.8, 4.7, 8.3), 'R3–R6': (3.2, 5.3, 8.1)}
ETAPA_BLOQUE = {'VE': 'V0–VE', 'V1_V6': 'VE–V6', 'V7_VT': 'V6–VT', 'R1': 'R1–R3', 'R2': 'R1–R3',
                'R3': 'R3–R6', 'R4_R5': 'R3–R6'}
GRADOS = ['bajo_leve', 'leve', 'moderado', 'severo']


def grado(dias, etapa):
    leve, mod, sev = SEVERIDAD[etapa]
    return 'bajo_leve' if dias < leve else 'leve' if dias < mod else 'moderado' if dias < sev else 'severo'


def bloques_por_dia(cal, anio):
    """Fecha → bloque del calendario para la temporada que empieza en `anio`."""
    v = cal['pixel']; codigos = [t['code'] for t in cal['templates']]
    out = {}
    for i, cod in enumerate(codigos):
        ini = core.absolute_reference_date(anio, v[0] - 1 + v[3 + i])
        fin = core.absolute_reference_date(anio, v[0] - 1 + v[4 + i])
        d = ini
        while d < fin:
            out[d] = cod; d += timedelta(days=1)
    return out


def et0_hargreaves(fecha, lat, tmax, tmin):
    """Igual que maize_gee_variables_v2.py: FAO-56 ec. 52, Ra por latitud y día del año."""
    j = fecha.timetuple().tm_yday
    ang = j * 2 * math.pi / 365
    dr = 1 + 0.033 * math.cos(ang)
    dec = 0.409 * math.sin(ang - 1.39)
    phi = lat * math.pi / 180
    ws = math.acos(max(-1, min(1, -math.tan(phi) * math.tan(dec))))
    ra = 24 * 60 / math.pi * 0.0820 * dr * (ws * math.sin(phi) * math.sin(dec) + math.cos(phi) * math.cos(dec) * math.sin(ws))
    return max(0.0, 0.0023 * 0.408 * ra * ((tmax + tmin) / 2 + 17.8) * math.sqrt(max(0.0, tmax - tmin)))


def rachas(hits, min_dias=2):
    """Lista de (inicio, largo) de cada racha de días True con largo ≥ min_dias."""
    out, i, n = [], 0, len(hits)
    while i < n:
        if hits[i]:
            j = i
            while j < n and hits[j]: j += 1
            if j - i >= min_dias: out.append((i, j - i))
            i = j
        else:
            i += 1
    return out


def fase_celda(g, bloques, umbral, fase):
    """Variables de una fase en una celda: g tiene las filas diarias de la ventana, en orden, con su bloque."""
    edd = float(np.maximum(0, g.tmax_c.values - EDD_TC).sum())
    pme = float((g.p_mm - g.et0).sum())
    if fase == 'MAT':
        return dict(conteo=float((g.p_mm > 10).sum()), edd29=edd, p_menos_et0=pme), []
    hits = [t >= umbral[b] for t, b in zip(g.tmax_c, g.bloque)]
    ev = []
    for i, largo in rachas(hits):
        # etapa de la fuente: la del bloque con más días dentro de la racha
        b = pd.Series(g.bloque.values[i:i + largo]).value_counts().index[0]
        etapa = ETAPA_BLOQUE[b]
        ev.append(dict(inicio=g.fecha.values[i], dias=largo, bloque=b, etapa=etapa, grado=grado(largo, etapa)))
    return dict(conteo=float(len(ev)), edd29=edd, p_menos_et0=pme), ev


def calcular(diario, cal, bloques_fase, umbral):
    filas, eventos = [], []
    for anio in ANIOS:
        mapa = bloques_por_dia(cal, int(anio))
        for fase, bloques in bloques_fase.items():
            dias = sorted(d for d, b in mapa.items() if b in bloques)
            ini, fin = dias[0], dias[-1]
            assert len(dias) == (fin - ini).days + 1, 'ventana con huecos'
            w = diario[(diario.f >= ini) & (diario.f <= fin)].copy()
            w['bloque'] = w.f.map(mapa)
            acum, pesos = {}, 0.0
            for (lon, lat), g in w.groupby(['lon', 'lat']):
                g = g.sort_values('f')
                if len(g) != len(dias) or g[['tmax_c', 'tmin_c', 'p_mm']].isna().any().any():
                    continue  # celda sin todos los días: fuera, como en GEE
                peso = math.cos(lat * math.pi / 180)
                v, ev = fase_celda(g, bloques, umbral, fase)
                for k, x in v.items(): acum[k] = acum.get(k, 0) + peso * x
                for e in ev:
                    eventos.append(dict(anio=int(anio), fase=fase, lon=lon, lat=lat, peso=peso) | e)
                pesos += peso
            fila = dict(anio_rendimiento=int(anio), fase=fase, inicio=ini.isoformat(), fin=fin.isoformat(),
                        dias_ventana=len(dias), celdas=int(w[['lon', 'lat']].drop_duplicates().shape[0]))
            fila |= {('conteo_original' if k == 'conteo' else k): x / pesos for k, x in acum.items()}
            fila['peso_total'] = pesos
            filas.append(fila)
    return pd.DataFrame(filas), pd.DataFrame(eventos)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pixel', type=int, default=191325)
    a = ap.parse_args()
    c = json.loads(CONFIG.read_text(encoding='utf-8'))
    data = json.loads((Path(c['calendar_dir']) / 'maize-maize__rf.json').read_text(encoding='utf-8'))
    con = sqlite3.connect(SQLITE)
    ref = pd.read_sql("select * from pares_v2 where pixel_id=? and alineacion='maturity-year'", con, params=(a.pixel,))
    lat, lon = float(ref.latitud.iloc[0]), float(ref.longitud.iloc[0])
    cal = dict(templates=data['templates'], pixel=data['pixels'][f'{lat:.2f},{lon:.2f}'])

    diario = pd.read_csv(BASE / f'pixel_{a.pixel}' / 'diario_celdas_nativas_1981_2016.csv.gz')
    diario['f'] = pd.to_datetime(diario.fecha).dt.date
    diario['et0'] = [et0_hargreaves(f, la, tx, tn) for f, la, tx, tn in zip(diario.f, diario.lat, diario.tmax_c, diario.tmin_c)]

    # 1) Reproducir v1 y comparar con lo que ya está en pares_v2
    v1, _ = calcular(diario, cal, BLOQUES_V1, UMBRAL_V1)
    m = v1.merge(ref[['anio_rendimiento', 'fase', 'inicio', 'fin', 'conteo_original', 'edd29', 'p_menos_et0']],
                 on=['anio_rendimiento', 'fase'], suffixes=('_local', '_gee'))
    for v in ('conteo_original', 'edd29', 'p_menos_et0'):
        m[f'dif_{v}'] = (m[f'{v}_local'] - m[f'{v}_gee']).abs()
    fechas_ok = bool((m.inicio_local == m.inicio_gee).all() and (m.fin_local == m.fin_gee).all())
    dif = {v: float(m[f'dif_{v}'].max()) for v in ('conteo_original', 'edd29', 'p_menos_et0')}

    out = BASE / f'reglas_v3_{datetime.now():%Y%m%d_%H%M%S}'; out.mkdir(parents=True)
    m.to_csv(out / 'validacion_v1.csv', index=False)
    tol = dict(conteo_original=0.01, edd29=0.05, p_menos_et0=0.5)
    if not fechas_ok or any(dif[k] > tol[k] for k in tol):
        print('NO reproduce v1:', fechas_ok, dif, 'ver', out / 'validacion_v1.csv'); raise SystemExit(1)

    # 2) v3 con las decisiones del 3 nov
    v3, ev = calcular(diario, cal, BLOQUES_V3, UMBRAL_V3)
    v3.to_csv(out / 'fases.csv', index=False)
    ev.to_csv(out / 'eventos.csv', index=False)

    # 3) Severidad: eventos por año y fase, media ponderada de las celdas (como el conteo)
    pesos = v3.set_index(['anio_rendimiento', 'fase']).peso_total
    sev = (ev.pivot_table(index=['anio', 'fase'], columns='grado', values='peso', aggfunc='sum', fill_value=0)
           .reindex(columns=GRADOS, fill_value=0))
    sev = sev.div(pesos.rename_axis(['anio', 'fase']).reindex(sev.index), axis=0)
    todo = pd.MultiIndex.from_product([ANIOS, list(BLOQUES_V3)], names=['anio', 'fase'])
    sev = sev.reindex(todo, fill_value=0).reset_index()
    sev.to_csv(out / 'severidad.csv', index=False)
    tabla = sev.groupby('fase')[GRADOS].sum().reindex(list(BLOQUES_V3))
    anios_con = sev.assign(algun=sev[GRADOS[1:]].sum(axis=1) >= 0.5).groupby('fase').algun.sum().reindex(list(BLOQUES_V3))

    (out / 'resumen.json').write_text(json.dumps(dict(
        pixel=a.pixel, lat=lat, lon=lon, celdas=int(diario[['lon', 'lat']].drop_duplicates().shape[0]),
        validacion_v1=dict(fechas_iguales=fechas_ok, dif_max=dif, tolerancia=tol),
        bloques=BLOQUES_V3, umbral=UMBRAL_V3, severidad_li2025b=SEVERIDAD, etapa_por_bloque=ETAPA_BLOQUE,
        eventos_1981_2016_por_fase=tabla.round(2).to_dict(orient='index'),
        anios_con_evento_leve_o_mas=anios_con.astype(int).to_dict(),
        nota='Conteos = media ponderada por cos(lat) de las celdas nativas; por eso pueden ser fraccionarios.'),
        ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    print('v1 reproducido, dif máx', dif)
    print(tabla.round(2).to_string())
    print('listo', out)


if __name__ == '__main__':
    main()
