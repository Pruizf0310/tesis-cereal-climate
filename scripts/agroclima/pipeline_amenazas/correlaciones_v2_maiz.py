"""Correlaciones con la tabla maestra v2 de maíz: sequía (P − ETP), grados-día (EDD29) y calor con umbrales v2.

Lee la vista pares_v2 de cruce_rendimiento_v2.sqlite (integrar_variables_v2_sqlite.py). Respuesta: z_rendimiento.
Escenarios: 'plausibles' (clases OK + DUDOSO_RATIO_FAO) y 'todos'. Alineaciones: same-label y maturity-year (no se elige).
Parte 1 — por píxel (Pearson principal, acordado con el director de tesis; Spearman como sensibilidad):
  cada variable × fase vs z; p por aproximación de Fisher → FDR (BH) global y por región;
  significancia de campo por permutación de temporadas (misma permutación para todos los píxeles), global y por región.
Parte 2 — panel regional con efecto fijo por píxel y SE agrupados por temporada:
  M_calor_v1 (6 fases, % días afectados, reglas v1) · M_sequia (P−ETP z en EST, VEG, FLO, FIL) ·
  M_edd (EDD29 en FLO, REP, FIL) · M_completo (sequía 4 fases + EDD 3 fases), con reparto del R² (LMG).
Uso: .venv/Scripts/python.exe correlaciones_v2_maiz.py --sqlite RUTA [--perm 1000] [--min-filas 500]
"""
import argparse, itertools, json, math, sqlite3, sys, time, traceback
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path('C:/Users/paola/Tesis')
AUDIT = ROOT / 'Repositorio/tesis-cereal-climate/outputs/agroclima_vigente/auditoria_rendimiento/maize/auditoria_por_pixel.csv'
PHASES = ['EST', 'VEG', 'FLO', 'REP', 'FIL', 'MAT']
VARS = {'sequia_z': ('p_menos_et0_z', ['EST', 'VEG', 'FLO', 'FIL']),
        'edd29': ('edd29', PHASES),
        'calor_v2_pct': ('pct_dias_racha_v2', ['FLO', 'FIL']),
        'calor_v1_pct': ('pct_dias_afectados', PHASES)}
MODELOS = {'M_calor_v1': [('calor_v1_pct', p) for p in PHASES],
           'M_sequia': [('sequia_z', p) for p in ['EST', 'VEG', 'FLO', 'FIL']],
           'M_edd': [('edd29', p) for p in ['FLO', 'REP', 'FIL']],
           'M_completo': [('sequia_z', p) for p in ['EST', 'VEG', 'FLO', 'FIL']] + [('edd29', p) for p in ['FLO', 'REP', 'FIL']]}
MIN_PARES = 20
ALFA = 0.05


def fdr(p):
    p = np.asarray(p, float); q = np.full_like(p, np.nan); ok = np.isfinite(p); m = ok.sum()
    if m == 0: return q
    i = np.argsort(p[ok]); r = p[ok][i] * m / np.arange(1, m + 1)
    r = np.minimum.accumulate(r[::-1])[::-1].clip(max=1); t = np.empty(m); t[i] = r; q[ok] = t
    return q


def corr_rows(x, y):
    m = np.isfinite(x) & np.isfinite(y); n = m.sum(1)
    x = np.where(m, x, np.nan); y = np.where(m, y, np.nan)
    xc = x - np.nanmean(x, 1, keepdims=True); yc = y - np.nanmean(y, 1, keepdims=True)
    with np.errstate(invalid='ignore', divide='ignore'):
        r = np.nansum(xc * yc, 1) / np.sqrt(np.nansum(xc ** 2, 1) * np.nansum(yc ** 2, 1))
    r[n < MIN_PARES] = np.nan
    return r, n


def p_fisher(r, n):
    z = np.arctanh(np.clip(r, -.999999, .999999)) * np.sqrt(np.clip(n - 3, 1, None))
    return np.array([math.erfc(abs(v) / math.sqrt(2)) if np.isfinite(v) else np.nan for v in z])


def ols(X, y):
    b, *_ = np.linalg.lstsq(X, y, rcond=None); return b, y - X @ b


def r2(X, y):
    _, e = ols(X, y); return 1 - (e @ e) / (y @ y)


def cl_se(X, e, cl):
    inv = np.linalg.pinv(X.T @ X); meat = np.zeros((X.shape[1],) * 2)
    for c in np.unique(cl):
        m = cl == c; s = X[m].T @ e[m]; meat += np.outer(s, s)
    G = len(np.unique(cl)); n, k = X.shape
    return np.sqrt(np.diag(G / (G - 1) * (n - 1) / (n - k) * inv @ meat @ inv))


def lmg(X, y, names):
    k = X.shape[1]; cache = {}
    def R(s):
        if s not in cache: cache[s] = r2(X[:, list(s)], y) if s else 0.0
        return cache[s]
    out = np.zeros(k)
    for j in range(k):
        oth = [i for i in range(k) if i != j]
        for size in range(k):
            w = math.factorial(size) * math.factorial(k - size - 1) / math.factorial(k)
            for s in itertools.combinations(oth, size):
                out[j] += w * (R(tuple(sorted(s + (j,)))) - R(tuple(sorted(s))))
    return dict(zip(names, out)), R(tuple(range(k)))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sqlite', required=True)
    ap.add_argument('--perm', type=int, default=1000)
    ap.add_argument('--min-filas', type=int, default=500)
    a = ap.parse_args()
    stamp = time.strftime('%Y%m%d_%H%M%S')
    out = Path(a.sqlite).parent / f'correlaciones_v2_{stamp}'; out.mkdir(parents=True, exist_ok=False)
    LOG = open(out / 'registro.log', 'w', encoding='utf-8'); t0 = time.perf_counter()
    def log(m):
        l = f'[{time.perf_counter() - t0:7.0f} s] {m}'; print(l, flush=True); LOG.write(l + '\n'); LOG.flush()

    con = sqlite3.connect(f'file:{Path(a.sqlite).as_posix()}?mode=ro', uri=True)
    q = """select pixel_id, temporada, fase, alineacion, region, z_rendimiento as z, pct_dias_afectados,
                  p_menos_et0_z, edd29, pct_dias_racha_v2
           from pares_v2 where par_amenaza_rendimiento_valido = 1"""
    d = pd.concat(pd.read_sql_query(q, con, chunksize=500_000), ignore_index=True); con.close()
    log(f'filas: {len(d):,}')
    audit = pd.read_csv(AUDIT, usecols=['pixel_id', 'clase'])
    plaus = set(audit.loc[audit.clase.isin(['OK', 'DUDOSO_RATIO_FAO']), 'pixel_id'])
    keys = ['alineacion', 'pixel_id', 'temporada']
    cols = []
    for nombre, (col, fases) in VARS.items():
        piv = d[d.fase.isin(fases)].pivot_table(index=keys, columns='fase', values=col, aggfunc='first')
        piv.columns = [f'{nombre}|{f}' for f in piv.columns]; cols.append(piv)
    W = pd.concat(cols, axis=1).join(d.drop_duplicates(keys).set_index(keys)[['region', 'z']]).reset_index()
    W['plausible'] = W.pixel_id.isin(plaus)
    rng = np.random.default_rng(20261024); years = np.arange(1981, 2017)
    perms = np.stack([rng.permutation(len(years)) for _ in range(a.perm)])

    # ---------- Parte 1: por píxel ----------
    filas, campo = [], []
    for al, dd in W.groupby('alineacion'):
        info = dd.drop_duplicates('pixel_id').set_index('pixel_id')[['region', 'plausible']]
        Y = dd.pivot(index='pixel_id', columns='temporada', values='z').reindex(columns=years)
        pix = Y.index.to_numpy(); Yv = Y.to_numpy(float)
        regs = info.reindex(pix).region.to_numpy(); pl = info.reindex(pix).plausible.to_numpy()
        for var in [c for c in W.columns if '|' in c]:
            X = dd.pivot(index='pixel_id', columns='temporada', values=var).reindex(index=pix, columns=years).to_numpy(float)
            r, n = corr_rows(X, Yv)
            rs, _ = corr_rows(pd.DataFrame(X).rank(axis=1).to_numpy(), pd.DataFrame(Yv).rank(axis=1).to_numpy())
            p = p_fisher(r, n)
            R = np.abs(np.stack([corr_rows(X, Yv[:, pm])[0] for pm in perms]))
            crit = np.nanpercentile(R, 95, axis=0)
            for esc, base in [('plausibles', pl), ('todos', np.ones(len(pix), bool))]:
                for zona in ['mundo'] + sorted(pd.unique(regs[base]).tolist()):
                    m = np.isfinite(r) & base & ((regs == zona) if zona != 'mundo' else True)
                    if m.sum() < 30: continue
                    obs = 100 * np.mean(np.abs(r[m]) >= crit[m]); nula = 100 * np.mean(R[:, m] >= crit[m], axis=1)
                    campo.append(dict(alineacion=al, variable=var, escenario=esc, zona=zona, pixeles=int(m.sum()),
                                      pearson_mediana=float(np.median(r[m])), pct_sig_obs=obs,
                                      pct_nulo_p95=float(np.percentile(nula, 95)),
                                      significancia_campo=bool(obs > np.percentile(nula, 95)),
                                      p_campo=float((np.sum(nula >= obs) + 1) / (a.perm + 1))))
            t = pd.DataFrame(dict(alineacion=al, variable=var, pixel_id=pix, region=regs, plausible=pl, n=n,
                                  pearson=r, spearman=rs, p=p))
            t['q_fdr'] = fdr(t.p); t['q_fdr_region'] = np.nan
            for _, idx in t.groupby('region').groups.items(): t.loc[idx, 'q_fdr_region'] = fdr(t.loc[idx, 'p'])
            filas.append(t)
            log(f'  {al} | {var}: {np.isfinite(r).sum():,} píxeles; mediana r = {np.nanmedian(r):.3f}')
    pd.concat(filas).to_csv(out / 'pearson_por_pixel_v2.csv.gz', index=False)
    C = pd.DataFrame(campo); C.to_csv(out / 'significancia_de_campo_v2.csv', index=False)
    log('  con significancia de campo (plausibles):\n' +
        C[C.significancia_campo & C.escenario.eq('plausibles')].round(3).to_string(index=False))

    # ---------- Parte 2: panel regional ----------
    mod_rows, coef_rows, lmg_rows = [], [], []
    for esc, Wx in [('plausibles', W[W.plausible]), ('todos', W)]:
        for (al, reg), dd in Wx.groupby(['alineacion', 'region']):
            for mod, vs in MODELOS.items():
                names = [f'{v}|{f}' for v, f in vs if f'{v}|{f}' in dd.columns]
                sub = dd.dropna(subset=names + ['z'])
                if len(sub) < a.min_filas or not names: continue
                cen = sub[names + ['z']] - sub.groupby('pixel_id')[names + ['z']].transform('mean')
                sd = cen[names].std(); use = [c for c in names if sd[c] > 1e-9]
                if not use: continue
                X = (cen[use] / sd[use]).to_numpy(float); y = cen.z.to_numpy(float)
                b, e = ols(X, y); se = cl_se(X, e, sub.temporada.to_numpy()); R2 = 1 - (e @ e) / (y @ y)
                mod_rows.append(dict(escenario=esc, alineacion=al, region=reg, modelo=mod, filas=len(sub),
                                     pixeles=sub.pixel_id.nunique(), R2_dentro_pixel=R2))
                for c, bb, ss in zip(use, b, se):
                    coef_rows.append(dict(escenario=esc, alineacion=al, region=reg, modelo=mod, variable=c,
                                          beta_por_1sd=bb, se_cluster=ss, t=bb / ss if ss > 0 else np.nan))
                if mod == 'M_completo':
                    con_, tot = lmg(X, y, use)
                    for c, v in con_.items():
                        lmg_rows.append(dict(escenario=esc, alineacion=al, region=reg, variable=c, r2_atribuido=v,
                                             r2_total=tot, pct_del_r2=100 * v / tot if tot > 0 else np.nan))
            log(f'  panel {esc} | {al} | {reg}')
    M = pd.DataFrame(mod_rows); M.to_csv(out / 'panel_R2_modelos.csv', index=False)
    pd.DataFrame(coef_rows).to_csv(out / 'panel_coeficientes.csv', index=False)
    pd.DataFrame(lmg_rows).to_csv(out / 'panel_LMG_M_completo.csv', index=False)
    if len(M):
        log('  R² dentro del píxel (plausibles):\n' + M[M.escenario.eq('plausibles')]
            .pivot_table(index=['alineacion', 'region'], columns='modelo', values='R2_dentro_pixel').round(3).to_string())
    (out / 'LEEME.md').write_text(__doc__ + """
Cómo leer:
1. `significancia_de_campo_v2.csv`: primero esto. Una variable "funciona" en una zona solo si significancia_campo = True.
2. `panel_R2_modelos.csv`: compara M_calor_v1 (reglas antiguas) con M_sequia, M_edd y M_completo, por región.
   Si M_completo supera claramente a M_calor_v1, la tabla v2 aporta.
3. `panel_LMG_M_completo.csv`: qué variable y fase aporta más al R² (solo asociación).
4. `pearson_por_pixel_v2.csv.gz`: detalle por píxel (Pearson principal, Spearman sensibilidad, FDR).
Cautelas: Q1 por píxel; ETP Hargreaves; regiones provisionales; sin corrección de multiplicidad entre regiones en el panel;
no elegir la alineación por el mejor resultado.
""", encoding='utf-8')
    log(f'TERMINÓ. Resultados en {out}')


try:
    main()
except Exception as ex:
    print(f'ERROR: {ex}\n{traceback.format_exc()}', flush=True); sys.exit(1)
