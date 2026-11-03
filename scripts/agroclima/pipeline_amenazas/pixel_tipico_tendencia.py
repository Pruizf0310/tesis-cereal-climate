"""Qué tendencia quitamos y qué cambia si también se la quitamos al clima.

1) Píxel típico (por defecto 191325, Nebraska): rendimiento GDHY crudo, su recta 1981–2016, el residuo (lo que usamos)
   y, por fase, la tendencia de cada variable climática y tres correlaciones:
     r_crudo     clima crudo  vs rendimiento crudo
     r_hasta_hoy clima crudo  vs rendimiento sin tendencia   (lo que se corrió en la primera ronda)
     r_ambos     clima sin tendencia vs rendimiento sin tendencia (= correlación parcial controlando el año)
   Identidad: r_hasta_hoy = r_ambos · √(1 − r(clima, año)²). Quitar la tendencia al clima solo cambia la magnitud,
   nunca el signo, y el cambio es grande solo si el año explica mucho de la variable climática.
2) Todos los píxeles (pares_v2, maturity-year): % de píxeles con tendencia climática p<0,05 y cuánto cambia r.
Salida: carpeta tendencia_<fecha> con tendencia.xlsx y resumen.json.
Uso: .venv/Scripts/python.exe pixel_tipico_tendencia.py [--pixel 191325]
"""
import argparse, json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import sqlite3
import xarray as xr
from scipy import stats

SQLITE = Path('C:/Users/paola/Tesis/03_Resultados/Agroclima/vigente/rendimiento/cruce_v2_20261024_184932/cruce_rendimiento_v2.sqlite')
RAW = Path('C:/Users/paola/Tesis/02_Procesados/GDHY_timeseries/maize_yield_1981_2016_RAW.nc')
BASE = Path('C:/Users/paola/Tesis/03_Resultados/Agroclima/vigente/pixel_tipico')
FASES = ['EST', 'VEG', 'FLO', 'REP', 'FIL', 'MAT']
VARS = {'conteo_original': 'Episodios de calor ≥2 d (MAT: días con P>10 mm)', 'edd29': 'EDD29 (°C·día)',
        'p_menos_et0': 'P − ETP Hargreaves (mm)'}
ANIOS = np.arange(1981, 2017)


def pixel(c, pid):
    d = pd.read_sql("select * from pares_v2 where pixel_id=? and alineacion='maturity-year'", c, params=(pid,))
    lat, lon = float(d.latitud.iloc[0]), float(d.longitud.iloc[0])
    y = xr.open_dataset(RAW)['var'].sel(lat=lat, lon=lon % 360).values.astype(float)
    lr = stats.linregress(ANIOS, y)
    serie = pd.DataFrame({'anio_cosecha': ANIOS, 'rendimiento_crudo_t_ha': y,
                          'tendencia_t_ha': lr.intercept + lr.slope * ANIOS})
    serie['rendimiento_sin_tendencia_t_ha'] = serie.rendimiento_crudo_t_ha - serie.tendencia_t_ha
    usado = d.drop_duplicates('anio_rendimiento').set_index('anio_rendimiento').rendimiento_sin_tendencia.loc[ANIOS]
    dif = float(np.abs(usado.values - serie.rendimiento_sin_tendencia_t_ha.values).max())
    if dif > 1e-4:
        raise ValueError(f'El residuo recalculado no coincide con el de la SQLite ({dif})')
    filas, cal = [], []
    for f in FASES:
        g = d[d.fase == f].set_index('anio_rendimiento').loc[ANIOS]
        cal.append(dict(fase=f, inicio_1981=g.inicio.iloc[0], fin_1981=g.fin.iloc[0], dias=int(g.dias_ventana.iloc[0]),
                        variable_regla=g.variable_climatica.iloc[0], operador=g.operador.iloc[0],
                        umbral=g.umbral.iloc[0], duracion_min_dias=g.duracion_min_dias.iloc[0]))
        for v, nombre in VARS.items():
            x = g[v].values.astype(float)
            serie[f'{f}_{v}'] = x
            if np.nanstd(x) == 0:
                filas.append(dict(fase=f, variable=v, descripcion=nombre, nota='constante (siempre 0)')); continue
            t = stats.linregress(ANIOS, x); xd = x - (t.intercept + t.slope * ANIOS)
            yr, yd = serie.rendimiento_crudo_t_ha.values, serie.rendimiento_sin_tendencia_t_ha.values
            filas.append(dict(fase=f, variable=v, descripcion=nombre, media=x.mean(), pendiente_por_decada=10 * t.slope,
                              p_tendencia=t.pvalue, r2_con_anio=t.rvalue ** 2,
                              r_crudo=stats.pearsonr(x, yr)[0], r_hasta_hoy=stats.pearsonr(x, yd)[0],
                              r_ambos=stats.pearsonr(xd, yd)[0], p_ambos=stats.pearsonr(xd, yd)[1]))
    info = dict(pixel_id=pid, lat=lat, lon=lon, region=d.region.iloc[0], pendiente_t_ha_anio=lr.slope,
                p_pendiente=lr.pvalue, r2_tendencia=lr.rvalue ** 2, tendencia_1981=lr.intercept + lr.slope * 1981,
                tendencia_2016=lr.intercept + lr.slope * 2016, media_cruda=float(y.mean()),
                verificacion_residuo_max_dif=dif)
    return serie, pd.DataFrame(filas), pd.DataFrame(cal), info


def global_(c):
    d = pd.read_sql("select pixel_id, fase, anio_rendimiento a, conteo_original, edd29, p_menos_et0, "
                    "rendimiento_sin_tendencia y from pares_v2 where alineacion='maturity-year' "
                    "and par_amenaza_rendimiento_valido=1", c)
    filas = []
    for v in VARS:
        for f, g in d.groupby('fase'):
            X = g.pivot(index='pixel_id', columns='a', values=v)
            Y = g.pivot(index='pixel_id', columns='a', values='y').loc[X.index, X.columns]
            X, Y = X.values.astype(float), Y.values.astype(float)
            T = np.broadcast_to(np.arange(X.shape[1], dtype=float), X.shape)
            M = np.isfinite(X) & np.isfinite(Y); n = M.sum(1)
            with np.errstate(all='ignore'):
                dm = lambda A: np.where(M, A, np.nan) - np.nanmean(np.where(M, A, np.nan), 1, keepdims=True)
                xc, yc, tc = dm(X), dm(Y), dm(T)
                sxt, stt, sxx, syy = (np.nansum(a * b, 1) for a, b in [(xc, tc), (tc, tc), (xc, xc), (yc, yc)])
                b = sxt / stt; xd = xc - b[:, None] * tc; sdd = np.nansum(xd * xd, 1)
                rxt = sxt / np.sqrt(sxx * stt)
                p = 2 * stats.t.sf(np.abs(rxt * np.sqrt((n - 2) / (1 - rxt ** 2))), n - 2)
                r1 = np.nansum(xc * yc, 1) / np.sqrt(sxx * syy); r2 = np.nansum(xd * yc, 1) / np.sqrt(sdd * syy)
            ok = (n >= 20) & (sxx > 0) & (sdd > 1e-12) & np.isfinite(r1) & np.isfinite(r2)
            dr = np.abs(r2 - r1)[ok]
            filas.append(dict(variable=v, fase=f, pixeles=int(ok.sum()), pct_pixeles_tendencia_p05=100 * np.mean(p[ok] < .05),
                              mediana_pendiente_por_decada=10 * np.nanmedian(b[ok]), mediana_abs_cambio_r=np.median(dr),
                              p95_abs_cambio_r=np.percentile(dr, 95), max_abs_cambio_r=dr.max(),
                              pct_cambio_r_mayor_0_1=100 * np.mean(dr > .1),
                              pct_cambia_signo=100 * np.mean((r1 * r2 < 0)[ok])))
    return pd.DataFrame(filas)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pixel', type=int, default=191325)
    a = ap.parse_args()
    c = sqlite3.connect(SQLITE)
    serie, corr, cal, info = pixel(c, a.pixel)
    glob = global_(c)
    out = BASE / f'tendencia_{datetime.now():%Y%m%d_%H%M%S}'; out.mkdir(parents=True)
    with pd.ExcelWriter(out / 'tendencia.xlsx') as w:
        serie.to_excel(w, sheet_name='serie_pixel', index=False); corr.to_excel(w, sheet_name='correlaciones_pixel', index=False)
        cal.to_excel(w, sheet_name='calendario_pixel', index=False); glob.to_excel(w, sheet_name='efecto_global', index=False)
    (out / 'resumen.json').write_text(json.dumps(dict(pixel=info, sqlite=str(SQLITE), rendimiento_crudo=str(RAW)),
                                                 indent=1, ensure_ascii=False, default=float), encoding='utf-8')
    print(json.dumps(info, indent=1, default=float)); print(corr.round(3).to_string()); print(glob.round(3).to_string())
    print('listo', out)


if __name__ == '__main__':
    main()
