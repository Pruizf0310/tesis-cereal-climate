"""¿Explica el ONI algo del rendimiento de maíz además de las amenazas por fase? Panel regional.

Misma base que atribucion_fases_maiz.py (SQLite del cruce anual, 20 oct 2026), mismo efecto fijo por píxel.
ONI de la temporada = promedio de oni_ventana de las 6 fases ponderado por dias_ventana.
Modelos por región, escenario y alineación (respuesta z_rendimiento, todo centrado dentro del píxel):
  A  6 fases                           (línea base, igual al paso 4 anterior)
  B  6 fases + ONI continuo            → ΔR² = R²B − R²A = lo que el ONI agrega
  C  solo ONI                          → efecto total del ONI
  D  6 fases + El Niño + La Niña       (dummies, umbral ±0,5 sobre ONI de temporada; base neutral)
Si beta_ONI baja de C a B, parte del efecto del ONI pasa por las amenazas por fase (lectura exploratoria).
El ONI es casi común a todos los píxeles de un año: los SE se agrupan por temporada (36 grupos).
Para decidir si el ONI aporta usa el t del ONI en el modelo B, NO el IC de ΔR²: agregar una variable nunca baja
el R² dentro de la muestra, así que ese IC tiene límite inferior ≥ 0 por construcción (se conserva solo como magnitud).
Exploratorio: sin corrección por multiplicidad entre regiones.
Uso: .venv/Scripts/python.exe atribucion_oni_maiz.py
"""
import sqlite3, sys, time, json, traceback
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path('C:/Users/paola/Tesis')
SRC = ROOT / '03_Resultados/Agroclima/vigente/rendimiento/cruce_anual_ONI_MJO_20261020_183145/cruce_rendimiento.sqlite'
AUDIT = ROOT / 'Repositorio/tesis-cereal-climate/outputs/agroclima_vigente/auditoria_rendimiento/maize/auditoria_por_pixel.csv'
PHASES = ['EST', 'VEG', 'FLO', 'REP', 'FIL', 'MAT']
EXPO = 'pct_dias_afectados'
MIN_FILAS_REGION = 500
N_BOOT = 300
UMBRAL_ENSO = 0.5
RNG = np.random.default_rng(20261023)

STAMP = time.strftime('%Y%m%d_%H%M%S')
OUT = ROOT / f'03_Resultados/Agroclima/vigente/rendimiento/atribucion_oni_{STAMP}'
OUT.mkdir(parents=True, exist_ok=False)
LOG = open(OUT / 'registro.log', 'w', encoding='utf-8')
T0 = time.perf_counter()


def log(msg):
    line = f'[{time.perf_counter() - T0:7.0f} s] {msg}'
    print(line, flush=True); LOG.write(line + '\n'); LOG.flush()


def cargar():
    con = sqlite3.connect(f'file:{SRC.as_posix()}?mode=ro', uri=True)
    q = f"""select pixel_id, temporada, fase, alineacion, region, {EXPO} as expo, z_rendimiento as z,
                   oni_ventana, dias_ventana
            from pares_anuales where par_amenaza_rendimiento_valido = 1"""
    partes = []
    for d in pd.read_sql_query(q, con, chunksize=500_000):
        partes.append(d); log(f'  filas leídas: {sum(map(len, partes)):,}')
    con.close()
    d = pd.concat(partes, ignore_index=True)
    keys = ['alineacion', 'pixel_id', 'temporada']
    w = d.pivot_table(index=keys, columns='fase', values='expo', aggfunc='first').reindex(columns=PHASES)
    d['oni_x_dias'] = d.oni_ventana * d.dias_ventana
    o = d.dropna(subset=['oni_ventana']).groupby(keys)[['oni_x_dias', 'dias_ventana']].sum()
    w['ONI'] = o.oni_x_dias / o.dias_ventana
    meta = d.drop_duplicates(keys).set_index(keys)[['region', 'z']]
    w = w.join(meta).reset_index()
    w['NINO'] = (w.ONI >= UMBRAL_ENSO).astype(float)
    w['NINA'] = (w.ONI <= -UMBRAL_ENSO).astype(float)
    audit = pd.read_csv(AUDIT, usecols=['pixel_id', 'clase'])
    plaus = set(audit.loc[audit.clase.isin(['OK', 'DUDOSO_RATIO_FAO']), 'pixel_id'])
    log(f'  tabla: {len(w):,} filas | ONI de temporada sin dato: {w.ONI.isna().sum():,}')
    return w, plaus


def ols(X, y):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta, y - X @ beta


def r2(X, y):
    _, res = ols(X, y); return 1 - (res @ res) / (y @ y)


def cluster_se(X, res, cl):
    inv = np.linalg.pinv(X.T @ X); meat = np.zeros((X.shape[1],) * 2)
    for c in np.unique(cl):
        m = cl == c; s = X[m].T @ res[m]; meat += np.outer(s, s)
    G = len(np.unique(cl)); n, k = X.shape
    return np.sqrt(np.diag(G / (G - 1) * (n - 1) / (n - k) * inv @ meat @ inv))


def main():
    W, PLAUS = cargar()
    esc = {'todos': W, 'plausibles': W[W.pixel_id.isin(PLAUS)]}
    filas_mod, filas_coef = [], []
    for e, d in esc.items():
        for (al, reg), dd in d.groupby(['alineacion', 'region']):
            dd = dd.dropna(subset=PHASES + ['z', 'ONI'])
            if len(dd) < MIN_FILAS_REGION: continue
            cols = PHASES + ['ONI', 'NINO', 'NINA', 'z']
            cen = dd[cols] - dd.groupby('pixel_id')[cols].transform('mean')
            sd = cen.std()
            fases = [p for p in PHASES if sd[p] > 1e-9]
            Z = {c: (cen[c] / sd[c]).to_numpy(float) if sd[c] > 1e-9 else None for c in cols[:-1]}
            y = cen.z.to_numpy(float); yr = dd.temporada.to_numpy()
            mods = {'A_fases': fases, 'B_fases_ONI': fases + ['ONI'], 'C_solo_ONI': ['ONI'],
                    'D_fases_Nino_Nina': fases + [c for c in ['NINO', 'NINA'] if Z[c] is not None]}
            R = {}
            for m, vs in mods.items():
                if any(Z[v] is None for v in vs): continue
                X = np.column_stack([Z[v] for v in vs])
                b, res = ols(X, y); se = cluster_se(X, res, yr); R[m] = 1 - (res @ res) / (y @ y)
                for v, bb, ss in zip(vs, b, se):
                    filas_coef.append(dict(escenario=e, alineacion=al, region=reg, modelo=m, variable=v,
                                           beta_por_1sd=bb, se_cluster=ss, t=bb / ss if ss > 0 else np.nan))
            # IC de ΔR² (B − A) remuestreando temporadas
            lo = hi = np.nan
            if 'A_fases' in R and 'B_fases_ONI' in R:
                XA = np.column_stack([Z[v] for v in mods['A_fases']]); XB = np.column_stack([XA, Z['ONI']])
                uy, inv = np.unique(yr, return_inverse=True); pos = [np.flatnonzero(inv == i) for i in range(len(uy))]
                dl = []
                for _ in range(N_BOOT):
                    idx = np.concatenate([pos[i] for i in RNG.integers(0, len(uy), len(uy))])
                    dl.append(r2(XB[idx], y[idx]) - r2(XA[idx], y[idx]))
                lo, hi = np.percentile(dl, [2.5, 97.5])
            bC = next((f['beta_por_1sd'] for f in filas_coef[::-1] if f['modelo'] == 'C_solo_ONI' and f['region'] == reg
                       and f['escenario'] == e and f['alineacion'] == al), np.nan)
            bB = next((f['beta_por_1sd'] for f in filas_coef[::-1] if f['modelo'] == 'B_fases_ONI' and f['variable'] == 'ONI'
                       and f['region'] == reg and f['escenario'] == e and f['alineacion'] == al), np.nan)
            filas_mod.append(dict(escenario=e, alineacion=al, region=reg, filas=len(dd), pixeles=dd.pixel_id.nunique(),
                                  temporadas_nino=int(dd.groupby('temporada').NINO.first().sum()),
                                  temporadas_nina=int(dd.groupby('temporada').NINA.first().sum()),
                                  R2_A_fases=R.get('A_fases'), R2_B_fases_ONI=R.get('B_fases_ONI'),
                                  R2_C_solo_ONI=R.get('C_solo_ONI'), R2_D_fases_Nino_Nina=R.get('D_fases_Nino_Nina'),
                                  dR2_ONI_sobre_fases=(R.get('B_fases_ONI', np.nan) - R.get('A_fases', np.nan)),
                                  dR2_ic95_inf=lo, dR2_ic95_sup=hi,
                                  beta_ONI_solo=bC, beta_ONI_con_fases=bB,
                                  pct_efecto_ONI_que_pasa_por_fases=100 * (1 - bB / bC) if bC and np.isfinite(bC) and abs(bC) > 1e-9 else np.nan))
            log(f'  {e} | {al} | {reg}: R²A={R.get("A_fases", np.nan):.4f} R²B={R.get("B_fases_ONI", np.nan):.4f} '
                f'dR²={filas_mod[-1]["dR2_ONI_sobre_fases"]:.4f} [{lo:.4f}, {hi:.4f}]')
    pd.DataFrame(filas_mod).to_csv(OUT / 'comparacion_modelos_ONI.csv', index=False)
    pd.DataFrame(filas_coef).to_csv(OUT / 'coeficientes_modelos_ONI.csv', index=False)
    json.dump(dict(fuente=str(SRC), exposicion=EXPO, umbral_enso=UMBRAL_ENSO, n_boot=N_BOOT, semilla=20261023),
              open(OUT / 'procedencia.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    (OUT / 'LEEME.md').write_text(__doc__ + """
Archivos: `comparacion_modelos_ONI.csv` (R² de cada modelo, ΔR² con IC95, beta del ONI solo y con fases),
`coeficientes_modelos_ONI.csv` (beta por 1 DE, SE agrupado por temporada y t de cada variable en cada modelo).
Lectura: si el IC95 de ΔR² no incluye 0, el ONI agrega información a las amenazas por fase en esa región.
Ojo: con pocas temporadas Niño/Niña (columnas temporadas_nino/nina) los efectos son inestables.
""", encoding='utf-8')
    log(f'TERMINÓ. Resultados en {OUT}')


try:
    main()
except Exception as ex:
    log(f'ERROR: {ex}\n{traceback.format_exc()}'); sys.exit(1)
