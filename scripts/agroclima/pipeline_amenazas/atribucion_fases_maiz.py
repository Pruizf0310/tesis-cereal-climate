"""Atribución exploratoria: qué amenaza en qué fase se asocia con el rendimiento anual de maíz.

Lee la SQLite del cruce anual (20 oct 2026) y corre, en orden:
  Paso 1  Relación entre fases: Spearman por píxel entre las 6 exposiciones (y con z de rendimiento).
  Paso 4  Atribución por región: panel con efecto fijo por píxel (exposición centrada por píxel),
          las 6 fases juntas, errores agrupados por temporada, y reparto del R² entre fases (LMG/Shapley).
  Paso 5  Compuestos: z de rendimiento en años con evento vs sin evento, por fase y por combinación,
          con IC por remuestreo de temporadas.
Exposición principal = pct_dias_afectados (la misma del Pearson principal). Respuesta = z_rendimiento.
Escenarios: 'todos' y 'plausibles' (clases OK + DUDOSO_RATIO_FAO de la auditoría de rendimiento).
Es exploratorio: asociación, no causalidad ni daño demostrado. No elige la mejor alineación.
Uso: .venv/Scripts/python.exe atribucion_fases_maiz.py
"""
import itertools, json, math, sqlite3, sys, time, traceback
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path('C:/Users/paola/Tesis')
SRC = ROOT / '03_Resultados/Agroclima/vigente/rendimiento/cruce_anual_ONI_MJO_20261020_183145/cruce_rendimiento.sqlite'
AUDIT = ROOT / 'Repositorio/tesis-cereal-climate/outputs/agroclima_vigente/auditoria_rendimiento/maize/auditoria_por_pixel.csv'
PHASES = ['EST', 'VEG', 'FLO', 'REP', 'FIL', 'MAT']
EXPO = 'pct_dias_afectados'
MIN_PARES = 20          # temporadas válidas mínimas por píxel para correlaciones por píxel
MIN_FILAS_REGION = 500  # filas mínimas para ajustar un panel regional
N_BOOT = 1000
RNG = np.random.default_rng(20261023)

STAMP = time.strftime('%Y%m%d_%H%M%S')
OUT = ROOT / f'03_Resultados/Agroclima/vigente/rendimiento/atribucion_fases_{STAMP}'
OUT.mkdir(parents=True, exist_ok=False)
LOG = open(OUT / 'registro.log', 'w', encoding='utf-8')
T0 = time.perf_counter()


def log(msg):
    line = f'[{time.perf_counter() - T0:7.0f} s] {msg}'
    print(line, flush=True); LOG.write(line + '\n'); LOG.flush()


def paso(nombre, fn):
    log(f'=== {nombre} ===')
    try:
        r = fn(); log(f'OK: {nombre}'); return r
    except Exception as e:
        log(f'ERROR en {nombre}: {e}\n{traceback.format_exc()}'); return None


# ---------------- Carga ----------------
def cargar():
    con = sqlite3.connect(f'file:{SRC.as_posix()}?mode=ro', uri=True)
    q = f"""select pixel_id, temporada, fase, alineacion, region, {EXPO} as expo, z_rendimiento as z
            from pares_anuales where par_amenaza_rendimiento_valido = 1"""
    partes = []
    for d in pd.read_sql_query(q, con, chunksize=500_000):
        d['expo'] = d.expo.astype('float32'); d['z'] = d.z.astype('float32')
        partes.append(d); log(f'  filas leídas: {sum(map(len, partes)):,}')
    con.close()
    d = pd.concat(partes, ignore_index=True)
    w = d.pivot_table(index=['alineacion', 'pixel_id', 'temporada'], columns='fase', values='expo', aggfunc='first')
    w = w.reindex(columns=PHASES)
    meta = d.drop_duplicates(['alineacion', 'pixel_id', 'temporada']).set_index(['alineacion', 'pixel_id', 'temporada'])[['region', 'z']]
    w = w.join(meta).reset_index()
    audit = pd.read_csv(AUDIT, usecols=['pixel_id', 'clase'])
    plaus = set(audit.loc[audit.clase.isin(['OK', 'DUDOSO_RATIO_FAO']), 'pixel_id'])
    log(f'  tabla ancha: {len(w):,} filas píxel-temporada-alineación | píxeles: {w.pixel_id.nunique():,} | plausibles: {len(plaus):,}')
    log(f'  regiones: {sorted(w.region.dropna().unique().tolist())}')
    return w, plaus


cargado = paso('Carga', cargar)
if cargado is None:
    log('Sin datos; se detiene.'); sys.exit(1)
W, PLAUS = cargado
ESCENARIOS = {'todos': W, 'plausibles': W[W.pixel_id.isin(PLAUS)]}
json.dump(dict(fuente=str(SRC), auditoria=str(AUDIT), exposicion=EXPO, respuesta='z_rendimiento',
               min_pares=MIN_PARES, n_boot=N_BOOT, semilla=20261023),
          open(OUT / 'procedencia.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


# ---------------- Paso 1: relación entre fases ----------------
def spearman_matrix_por_pixel(g, cols):
    x = g[cols].to_numpy(float)
    ok = np.isfinite(x).all(axis=1)
    x = x[ok]
    if len(x) < MIN_PARES: return None
    r = pd.DataFrame(x).rank().to_numpy()
    sd = r.std(axis=0)
    r = (r - r.mean(axis=0)) / np.where(sd > 0, sd, np.nan)
    return (r.T @ r) / len(r)


def paso1():
    cols = PHASES + ['z']
    filas = []
    for (esc, d) in ESCENARIOS.items():
        for (al, reg), dd in d.groupby(['alineacion', 'region']):
            mats = [m for _, g in dd.groupby('pixel_id') if (m := spearman_matrix_por_pixel(g, cols)) is not None]
            if not mats: continue
            M = np.stack(mats)                                   # píxeles × 7 × 7
            for i, j in itertools.combinations(range(len(cols)), 2):
                v = M[:, i, j]; v = v[np.isfinite(v)]
                if len(v) == 0: continue
                filas.append(dict(escenario=esc, alineacion=al, region=reg, var_1=cols[i], var_2=cols[j],
                                  pixeles=len(v), rho_mediana=np.median(v),
                                  pct_rho_mayor_05=100 * np.mean(np.abs(v) > 0.5)))
    t = pd.DataFrame(filas); t.to_csv(OUT / 'paso1_relacion_entre_fases.csv', index=False)
    s = t[t.escenario.eq('plausibles') & t.alineacion.eq('same-label')].assign(
        wr=lambda x: x.rho_mediana * x.pixeles)
    agg = s.groupby(['var_1', 'var_2'])[['wr', 'pixeles']].sum()
    glob = (agg.wr / agg.pixeles).unstack()
    glob.to_csv(OUT / 'paso1_matriz_global_same-label_plausibles.csv')
    log('  mediana de Spearman ponderada por píxeles (plausibles, same-label):\n' + glob.round(2).to_string())


paso('Paso 1 relación entre fases', paso1)


# ---------------- Paso 4: atribución por región ----------------
def ols(X, y):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ beta
    return beta, res


def r2(X, y):
    if X.shape[1] == 0: return 0.0
    _, res = ols(X, y)
    return 1 - (res @ res) / (y @ y)


def cluster_se(X, res, clusters):
    XtX_inv = np.linalg.pinv(X.T @ X)
    meat = np.zeros((X.shape[1], X.shape[1]))
    for c in np.unique(clusters):
        m = clusters == c
        s = X[m].T @ res[m]; meat += np.outer(s, s)
    G = len(np.unique(clusters)); n, k = X.shape
    adj = G / (G - 1) * (n - 1) / (n - k)
    return np.sqrt(np.diag(adj * XtX_inv @ meat @ XtX_inv))


def lmg(X, y, names):
    """Reparto de R² entre predictores promediando sobre todos los órdenes (Shapley)."""
    k = X.shape[1]; cache = {}
    def R(s):
        if s not in cache: cache[s] = r2(X[:, list(s)], y)
        return cache[s]
    contrib = np.zeros(k)
    for j in range(k):
        others = [i for i in range(k) if i != j]
        for size in range(k):
            w = math.factorial(size) * math.factorial(k - size - 1) / math.factorial(k)
            for s in itertools.combinations(others, size):
                contrib[j] += w * (R(tuple(sorted(s + (j,)))) - R(tuple(sorted(s))))
    return dict(zip(names, contrib)), R(tuple(range(k)))


def paso4():
    filas, partes_r2 = [], []
    for esc, d in ESCENARIOS.items():
        for (al, reg), dd in d.groupby(['alineacion', 'region']):
            dd = dd.dropna(subset=PHASES + ['z']).copy()
            if len(dd) < MIN_FILAS_REGION: continue
            # efecto fijo por píxel: centrar exposición y respuesta dentro de cada píxel
            cols = PHASES + ['z']
            cen = dd[cols] - dd.groupby('pixel_id')[cols].transform('mean')
            sd = cen[PHASES].std()
            usar = [p for p in PHASES if sd[p] > 1e-9]          # fases sin variación quedan fuera
            X = (cen[usar] / sd[usar]).to_numpy(float); y = cen.z.to_numpy(float)
            beta, res = ols(X, y)
            se = cluster_se(X, res, dd.temporada.to_numpy())
            for p, b, s in zip(usar, beta, se):
                filas.append(dict(escenario=esc, alineacion=al, region=reg, fase=p, filas=len(dd),
                                  pixeles=dd.pixel_id.nunique(), beta_por_1sd=b, se_cluster_temporada=s,
                                  t=b / s if s > 0 else np.nan,
                                  beta_por_1pct_dias=b / sd[p]))
            contrib, total = lmg(X, y, usar)
            for p in PHASES:
                partes_r2.append(dict(escenario=esc, alineacion=al, region=reg, fase=p,
                                      r2_atribuido=contrib.get(p, np.nan), r2_total=total,
                                      pct_del_r2=100 * contrib[p] / total if p in contrib and total > 0 else np.nan))
            log(f'  {esc} | {al} | {reg}: n={len(dd):,} R²(dentro de píxel)={total:.4f}')
    pd.DataFrame(filas).to_csv(OUT / 'paso4_coeficientes_panel_regional.csv', index=False)
    pd.DataFrame(partes_r2).to_csv(OUT / 'paso4_reparto_R2_LMG.csv', index=False)


paso('Paso 4 atribución por región (panel + LMG)', paso4)


# ---------------- Paso 5: compuestos ----------------
def diff_boot(dd, flag):
    """Diferencia de z medio (con evento − sin evento) e IC95 remuestreando temporadas."""
    yrs = dd.temporada.to_numpy(); ev = flag.to_numpy(); z = dd.z.to_numpy(float)
    uy, inv = np.unique(yrs, return_inverse=True)
    s1 = np.bincount(inv, z * ev, len(uy)); n1 = np.bincount(inv, ev, len(uy))
    s0 = np.bincount(inv, z * ~ev, len(uy)); n0 = np.bincount(inv, ~ev, len(uy))
    if n1.sum() == 0 or n0.sum() == 0: return np.nan, np.nan, np.nan, int(n1.sum()), int(n0.sum())
    obs = s1.sum() / n1.sum() - s0.sum() / n0.sum()
    idx = RNG.integers(0, len(uy), (N_BOOT, len(uy)))
    a1, b1, a0, b0 = s1[idx].sum(1), n1[idx].sum(1), s0[idx].sum(1), n0[idx].sum(1)
    with np.errstate(invalid='ignore', divide='ignore'):
        bt = a1 / b1 - a0 / b0
    lo, hi = np.nanpercentile(bt, [2.5, 97.5])
    return obs, lo, hi, int(n1.sum()), int(n0.sum())


def paso5():
    fil_f, fil_c = [], []
    for esc, d in ESCENARIOS.items():
        for (al, reg), dd in d.groupby(['alineacion', 'region']):
            dd = dd.dropna(subset=PHASES + ['z'])
            if len(dd) < MIN_FILAS_REGION: continue
            ev = dd[PHASES] > 0
            for p in PHASES:
                obs, lo, hi, n1, n0 = diff_boot(dd, ev[p])
                fil_f.append(dict(escenario=esc, alineacion=al, region=reg, fase=p, dif_z_con_menos_sin=obs,
                                  ic95_inf=lo, ic95_sup=hi, n_con_evento=n1, n_sin_evento=n0))
            code = (ev.to_numpy() * (1 << np.arange(len(PHASES)))).sum(axis=1)
            nombres = {c: '+'.join(p for i, p in enumerate(PHASES) if c >> i & 1) or 'ninguna' for c in np.unique(code)}
            combo = pd.Series(code, index=dd.index).map(nombres)
            g = dd.assign(combinacion=combo).groupby('combinacion').agg(n=('z', 'size'), z_medio=('z', 'mean'),
                                                                        pixeles=('pixel_id', 'nunique')).reset_index()
            g = g[g.n >= 30].assign(escenario=esc, alineacion=al, region=reg)
            fil_c.append(g)
    pd.DataFrame(fil_f).to_csv(OUT / 'paso5_compuestos_por_fase.csv', index=False)
    if fil_c: pd.concat(fil_c).sort_values(['escenario', 'alineacion', 'region', 'z_medio']).to_csv(
        OUT / 'paso5_compuestos_por_combinacion.csv', index=False)


paso('Paso 5 compuestos con evento vs sin evento', paso5)

(OUT / 'LEEME.md').write_text(f"""# Atribución exploratoria por fase — maíz — {STAMP}

Fuente: `{SRC}`. Exposición: `{EXPO}` por fase. Respuesta: `z_rendimiento` (rendimiento sin tendencia estandarizado por píxel).

1. `paso1_relacion_entre_fases.csv` / `paso1_matriz_global_same-label_plausibles.csv`: Spearman por píxel entre fases y con z.
   Si dos fases tienen |rho| alto, la regresión no puede separarlas bien: trátalas como un bloque.
2. `paso4_coeficientes_panel_regional.csv`: panel por región con efecto fijo por píxel; beta en z de rendimiento por 1 DE de
   exposición (y por 1 punto porcentual de días afectados); SE agrupados por temporada (36 grupos). |t|>2 ≈ señal.
   `paso4_reparto_R2_LMG.csv`: cuánto del R² dentro del píxel aporta cada fase (suma = R² total). Esto responde
   «qué fase aporta más», pero solo como asociación.
3. `paso5_compuestos_por_fase.csv`: z medio con evento − sin evento, IC95 remuestreando temporadas.
   `paso5_compuestos_por_combinacion.csv`: z medio por combinación de fases con evento (n≥30).

Cautelas: regiones provisionales; el detrend original usó todos los años; no hay corrección por multiplicidad entre regiones;
MJO y ONI no entran aún en el modelo; no se elige alineación por mejor ajuste.
""", encoding='utf-8')
log(f'TERMINÓ. Resultados en {OUT}')
