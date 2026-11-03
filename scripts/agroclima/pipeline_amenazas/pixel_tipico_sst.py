"""Correlación SST–rendimiento en un píxel: lo que está en el H5 frente a SST sin tendencia en 1981–2016.

El archivo SST_monthly_detrended_1981_2025_0p5deg35.nc (OISST v2.1 mensual, 0,5°) se detrendió con una recta sobre
1981–2025. Dentro de 1981–2016 puede quedar tendencia residual. Quitar una recta ajustada en 1981–2016 al archivo ya
detrendido da exactamente el mismo residuo que quitarla a la SST cruda (la recta es una proyección lineal).
Para el píxel:
  A) r(SST del archivo, rendimiento sin tendencia)   → debe reproducir el H5 (verificación)
  B) r(SST sin tendencia 1981–2016, rendimiento sin tendencia)
por mes calendario (mismo año de la etiqueta de rendimiento, como correlacion_masiva.py) y celda oceánica.
Salida: pixel_tipico/sst_<fecha>/ con resumen.xlsx, mapas_r.npz y resumen.json.
Uso: .venv/Scripts/python.exe pixel_tipico_sst.py [--pixel 191325] [--h5 D:/maize_correlacion_vectorizada.h5]
"""
import argparse, json
from datetime import datetime
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
import xarray as xr

SST = Path('C:/Users/paola/Tesis/02_Procesados/SST_monthly_detrended_1981_2025_0p5deg35.nc')
DET = Path('C:/Users/paola/Tesis/02_Procesados/GDHY_detrend/maize_yield_1981_2016_DETREND_clean.nc')
PIX = Path('C:/Users/paola/Tesis/02_Procesados/Pixeles_correlacion_vigentes/pixeles_maize.csv')
BASE = Path('C:/Users/paola/Tesis/03_Resultados/Agroclima/vigente/pixel_tipico')
CAJAS = {'Niño 3.4': (-5, 5, 190, 240), 'Niño 1+2': (-10, 0, 270, 280), 'Niño 4': (-5, 5, 160, 210),
         'Índico oeste': (-10, 10, 50, 70), 'Atlántico trop. norte': (5, 20, 300, 345), 'Pacífico norte': (30, 50, 180, 220)}
MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']


def corr_mapa(X, y):
    """X (años, celdas) e y (años,) → r por celda con años válidos comunes."""
    M = np.isfinite(X) & np.isfinite(y)[:, None]
    n = M.sum(0)
    Xm = np.where(M, X, np.nan); Ym = np.where(M, y[:, None], np.nan)
    xc = Xm - np.nanmean(Xm, 0); yc = Ym - np.nanmean(Ym, 0)
    with np.errstate(all='ignore'):
        r = np.nansum(xc * yc, 0) / np.sqrt(np.nansum(xc ** 2, 0) * np.nansum(yc ** 2, 0))
    r[n < 5] = np.nan
    return r


def quitar_recta(X, t):
    """Quita a cada columna su recta por mínimos cuadrados contra t (ignora NaN por columna)."""
    out = np.full_like(X, np.nan)
    filas = np.isfinite(X).any(1)  # años con dato (la SST empieza en sep. 1981)
    ok = np.isfinite(X[filas]).all(0)
    A = np.vstack([np.ones_like(t), t]).T[filas]
    coef, *_ = np.linalg.lstsq(A, X[filas][:, ok], rcond=None)
    sub = out[filas]; sub[:, ok] = X[filas][:, ok] - A @ coef; out[filas] = sub
    pend = np.full(X.shape[1], np.nan); pend[ok] = coef[1]
    return out, pend


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pixel', type=int, default=191325)
    ap.add_argument('--h5', default='D:/maize_correlacion_vectorizada.h5')
    a = ap.parse_args()
    px = pd.read_csv(PIX).set_index('pixel_id').loc[a.pixel]
    lat, lon, hi = float(px.latitude), float(px.longitude), int(px.h5_index)
    y = xr.open_dataset(DET)['var'].sel(lat=lat, lon=lon % 360, method='nearest')
    anios = np.arange(1981, 2017)
    y = pd.Series(y.values.astype(float), index=pd.DatetimeIndex(y.time.values).year).reindex(anios).values
    y = (y - np.nanmean(y)) / np.nanstd(y, ddof=1)  # como correlacion_masiva.py (no cambia r)
    sst = xr.open_dataset(SST)['sst_detrended'].sel(time=slice('1981', '2016')).transpose('time', 'lat', 'lon')
    with h5py.File(a.h5, 'r') as f:
        H = f['correlacion'][hi].reshape(12, 360, 720)
    latv, lonv = sst.lat.values, sst.lon.values
    A, B, P = np.full((12, 360, 720), np.nan), np.full((12, 360, 720), np.nan), np.full((12, 360, 720), np.nan)
    filas = []
    for m in range(12):
        sm = sst.sel(time=sst.time.dt.month == m + 1)
        sm = sm.assign_coords(time=sm.time.dt.year).reindex(time=anios)
        X = sm.values.reshape(36, -1).astype(float)
        Xd, pend = quitar_recta(X, anios.astype(float))
        A[m] = corr_mapa(X, y).reshape(360, 720); B[m] = corr_mapa(Xd, y).reshape(360, 720)
        P[m] = (pend * 10).reshape(360, 720)
        h, ra, rb = H[m].ravel(), A[m].ravel(), B[m].ravel()
        ok = np.isfinite(h) & np.isfinite(ra) & np.isfinite(rb)
        d = np.abs(rb[ok] - ra[ok])
        fila = dict(mes=MESES[m], celdas=int(ok.sum()), max_dif_H5_vs_A=float(np.abs(h[ok] - ra[ok]).max()),
                    mediana_abs_cambio_r=float(np.median(d)), p95_abs_cambio_r=float(np.percentile(d, 95)),
                    max_abs_cambio_r=float(d.max()), pct_celdas_r033_antes=100 * float(np.mean(np.abs(ra[ok]) >= .33)),
                    pct_celdas_r033_despues=100 * float(np.mean(np.abs(rb[ok]) >= .33)),
                    pct_cambia_signo=100 * float(np.mean(ra[ok] * rb[ok] < 0)),
                    mediana_tendencia_residual_C_dec=float(np.nanmedian(P[m])))
        for nombre, (la0, la1, lo0, lo1) in CAJAS.items():
            mk = (latv[:, None] >= la0) & (latv[:, None] <= la1) & (lonv[None, :] >= lo0) & (lonv[None, :] <= lo1)
            fila[f'r_{nombre}_antes'] = float(np.nanmean(A[m][mk])); fila[f'r_{nombre}_despues'] = float(np.nanmean(B[m][mk]))
        filas.append(fila)
    R = pd.DataFrame(filas)
    out = BASE / f'sst_{datetime.now():%Y%m%d_%H%M%S}'; out.mkdir(parents=True)
    with pd.ExcelWriter(out / 'resumen.xlsx') as w:
        R.to_excel(w, sheet_name='por_mes', index=False)
    np.savez_compressed(out / 'mapas_r.npz', antes=A.astype('float32'), despues=B.astype('float32'),
                        tendencia_residual=P.astype('float32'), lat=latv, lon=lonv)
    (out / 'resumen.json').write_text(json.dumps(dict(pixel=a.pixel, lat=lat, lon=lon, h5_index=hi, sst=str(SST),
                                                      rendimiento=str(DET), h5=a.h5), indent=1), encoding='utf-8')
    pd.set_option('display.width', 250)
    print(R.round(3).to_string()); print('listo', out)


if __name__ == '__main__':
    main()
