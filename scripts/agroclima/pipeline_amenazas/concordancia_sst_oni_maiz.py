"""Concordancia entre las correlaciones SST–rendimiento (campo completo) y la verificación ONI–rendimiento por píxel.

Entrada SST: HDF5 'correlacion' (n_pix, 12 meses, 259.200 celdas = 360 lat × 720 lon a 0,5°), con la fila
h5_index de cada píxel (pixeles_<cultivo>.csv). Según correlacion_masiva.py, cada mes es la SST mensual sin
tendencia del MISMO año calendario de la etiqueta de rendimiento (1981–2016) → comparable con 'same-label'.
Por píxel y mes calcula:
  - r medio en cajas oceánicas: Niño 3.4, Niño 1+2, Niño 4, Índico oeste/este (IOD), Atlántico tropical N/S.
  - celda de |r| máximo y la cuenca donde cae; % de océano con |r| ≥ 0,33 (≈ p<0,05 con n=36).
Concordancia: por píxel, r de la caja Niño 3.4 (meses ene–mar y promedio anual) frente al Spearman ONI–rendimiento
de verificar_oni_por_pixel_maiz.py: correlación entre píxeles y % de acuerdo de signo, global y por región.
Requiere el disco D: conectado (D:/maize_correlacion_vectorizada.h5). Solo lectura.
Uso: .venv/Scripts/python.exe concordancia_sst_oni_maiz.py [--h5 RUTA] [--bloque 16]
"""
import argparse, glob, sys, time, json, traceback
from pathlib import Path
import numpy as np
import pandas as pd
import h5py

ROOT = Path('C:/Users/paola/Tesis')
SST_GRID = ROOT / '02_Procesados/SST_monthly_detrended_1981_2025_0p5deg35.nc'
COORDS = ROOT / '02_Procesados/Pixeles_correlacion_vigentes/pixeles_maize.csv'
VERIF_GLOB = str(ROOT / '03_Resultados/Agroclima/vigente/rendimiento/verificacion_ONI_pixel_*/oni_rendimiento_por_pixel.csv')
R_SIG = 0.33
MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
# cajas: (lat_min, lat_max, lon_min, lon_max) en 0–360
CAJAS = {'nino34': (-5, 5, 190, 240), 'nino12': (-10, 0, 270, 280), 'nino4': (-5, 5, 160, 210),
         'iod_oeste': (-10, 10, 50, 70), 'iod_este': (-10, 0, 90, 110),
         'atl_trop_norte': (5, 20, 300, 330), 'atl_trop_sur': (-20, 0, 330, 370)}


def cuenca(lat, lon):
    """Clasificación gruesa (lon 0–360). Mar de China meridional cuenta como Pacífico; Caribe como Atlántico."""
    if abs(lat) > 60: return 'polar'
    if 20 <= lon < 120 and lat < 30 and not (lon >= 100 and lat > 0): return 'indico'
    if (100 <= lon < 290) and not (lat > 8 and lon >= 276): return 'pacifico'
    return 'atlantico'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--h5', default='D:/maize_correlacion_vectorizada.h5')
    ap.add_argument('--bloque', type=int, default=16, help='píxeles leídos a la vez (16 ≈ 200 MB)')
    args = ap.parse_args()
    stamp = time.strftime('%Y%m%d_%H%M%S')
    out = ROOT / f'03_Resultados/Agroclima/vigente/rendimiento/concordancia_SST_ONI_{stamp}'
    out.mkdir(parents=True, exist_ok=False)
    LOG = open(out / 'registro.log', 'w', encoding='utf-8'); t0 = time.perf_counter()
    def log(m):
        l = f'[{time.perf_counter() - t0:7.0f} s] {m}'; print(l, flush=True); LOG.write(l + '\n'); LOG.flush()

    if not Path(args.h5).exists():
        log(f'No existe {args.h5}. Conecta el disco D: o pasa --h5 con la ruta.'); sys.exit(1)
    with h5py.File(SST_GRID, 'r') as g:
        lat = g['lat'][:]; lon = g['lon'][:]
    LA, LO = np.meshgrid(lat, lon, indexing='ij'); LA = LA.ravel(); LO = LO.ravel()
    global NO_POLAR
    NO_POLAR = np.abs(LA) <= 60
    masks = {}
    for k, (a, b, c, d) in CAJAS.items():
        lo2 = np.where(LO < c - 1e-9, LO + 360, LO) if d > 360 else LO
        masks[k] = (LA >= a) & (LA <= b) & (lo2 >= c) & (lo2 <= d)
    coords = pd.read_csv(COORDS).sort_values('h5_index').reset_index(drop=True)

    f = h5py.File(args.h5, 'r'); C = f['correlacion']
    if C.shape[1:] != (12, lat.size * lon.size):
        log(f'Forma inesperada {C.shape}'); sys.exit(1)
    if C.shape[0] != len(coords):
        log(f'Píxeles HDF5 {C.shape[0]} ≠ CSV {len(coords)}'); sys.exit(1)
    if 'lat_idx' in f and not np.array_equal(f['lat_idx'][:], coords.lat_idx.to_numpy()):
        log('lat_idx del HDF5 no coincide con el CSV'); sys.exit(1)
    # chequeo de orientación: tierra (Sahara 20N, 10E) debe ser NaN y Pacífico (0N, 200E) finito
    v0 = C[0, 0, :]
    tierra = np.argmin((LA - 20.25) ** 2 + (LO - 10.25) ** 2); mar = np.argmin((LA - 0.25) ** 2 + (LO - 200.25) ** 2)
    log(f'chequeo orientación: tierra={v0[tierra]!r} (esperado nan), mar={v0[mar]!r} (esperado número)')
    if np.isfinite(v0[tierra]) or not np.isfinite(v0[mar]):
        log('La orientación de la grilla no es (lat, lon) ascendente; se detiene para no leer mal.'); sys.exit(1)

    filas = []
    n = C.shape[0]
    for i0 in range(0, n, args.bloque):
        blk = C[i0:i0 + args.bloque].astype(np.float32)          # bloque × 12 × 259200
        for j in range(blk.shape[0]):
            pid = int(coords.pixel_id[i0 + j])
            for m in range(12):
                v = blk[j, m]; ok = np.isfinite(v) & NO_POLAR   # celdas polares (hielo) dan |r| espurios
                if not ok.any(): continue
                av = np.where(ok, np.abs(v), -1); k = int(np.argmax(av))
                fila = dict(pixel_id=pid, mes=m + 1, r_max_abs=float(v[k]), lat_max=float(LA[k]), lon_max=float(LO[k]),
                            cuenca_max=cuenca(LA[k], LO[k]), pct_oceano_sig=100 * float(np.mean(np.abs(v[ok]) >= R_SIG)))
                for c, mk in masks.items():
                    w = v[mk]; w = w[np.isfinite(w)]
                    fila[f'r_{c}'] = float(w.mean()) if w.size else np.nan
                filas.append(fila)
        if (i0 // args.bloque) % 25 == 0:
            log(f'  píxeles {min(i0 + args.bloque, n):,}/{n:,}')
    f.close()
    T = pd.DataFrame(filas); T.to_csv(out / 'sst_por_pixel_mes.csv.gz', index=False)

    # concordancia con la verificación ONI (la más reciente)
    vfiles = sorted(glob.glob(VERIF_GLOB))
    if not vfiles:
        log('No hay verificación ONI por píxel; solo se guardan los resúmenes SST.')
    else:
        V = pd.read_csv(vfiles[-1]); V = V[V.predictor.eq('ONI_temporada')]
        nino = T.pivot(index='pixel_id', columns='mes', values='r_nino34')
        S = pd.DataFrame({'r_nino34_EFM': nino[[1, 2, 3]].mean(1), 'r_nino34_anual': nino.mean(1)})
        res = []
        for al, v in V.groupby('alineacion'):
            M = v.set_index('pixel_id')[['spearman', 'region', 'plausible']].join(S, how='inner')
            M = M[M.plausible]
            for zona, g in [('mundo', M)] + list(M.groupby('region')):
                for col in ['r_nino34_EFM', 'r_nino34_anual']:
                    gg = g[['spearman', col]].dropna()
                    if len(gg) < 30: continue
                    res.append(dict(alineacion=al, zona=zona, sst=col, pixeles=len(gg),
                                    corr_entre_pixeles=gg.spearman.rank().corr(gg[col].rank()),
                                    pct_mismo_signo=100 * float(np.mean(np.sign(gg.spearman) == np.sign(gg[col]))),
                                    mediana_oni=gg.spearman.median(), mediana_sst=gg[col].median()))
        R = pd.DataFrame(res); R.to_csv(out / 'concordancia_ONI_vs_SST_nino34.csv', index=False)
        log('  concordancia (mundo y regiones):\n' + R.round(2).to_string(index=False))
        json.dump(dict(verificacion_usada=vfiles[-1]), open(out / 'procedencia.json', 'w'), indent=1)

    dom =T.groupby(['pixel_id', 'mes']).cuenca_max.first().groupby('pixel_id').agg(lambda s: s.value_counts().index[0])
    dom.rename('cuenca_dominante').to_csv(out / 'cuenca_dominante_por_pixel.csv')
    (out / 'LEEME.md').write_text(__doc__ + """
Archivos: `sst_por_pixel_mes.csv.gz` (detalle), `cuenca_dominante_por_pixel.csv` (cuenca donde más meses cae el |r| máximo),
`concordancia_ONI_vs_SST_nino34.csv`. Si la verificación ONI y la caja Niño 3.4 de tus correlaciones SST concuerdan
(correlación entre píxeles alta y mismo signo), las dos lecturas son coherentes. Compara sobre todo 'same-label'.
Cautela: |r| ≥ 0,33 es un umbral por celda; el máximo sobre 259.200 celdas siempre será alto por azar.
""", encoding='utf-8')
    log(f'TERMINÓ. Resultados en {out}')


try:
    main()
except SystemExit:
    raise
except Exception as ex:
    print(f'ERROR: {ex}\n{traceback.format_exc()}'); sys.exit(1)
