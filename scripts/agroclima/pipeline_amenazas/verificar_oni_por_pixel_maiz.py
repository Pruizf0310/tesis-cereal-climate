"""Verificación píxel por píxel: ¿el ONI se correlaciona con el rendimiento de maíz?

Base: SQLite del cruce anual (20 oct 2026). Respuesta: z_rendimiento (sin tendencia, estandarizado por píxel).
Predictores ONI, uno a la vez:
  ONI_temporada  promedio de oni_ventana de las 6 fases ponderado por días
  ONI_<fase>     ONI de la ventana de cada fase (EST, VEG, FLO, REP, FIL, MAT)
Por píxel, alineación (same-label / maturity-year) y escenario (todos / plausibles):
  - Pearson y Spearman, n de pares (mínimo 20).
  - p-valor por permutación de temporadas (1.000) — la MISMA permutación para todos los píxeles,
    así se conserva la correlación espacial.
  - FDR de Benjamini-Hochberg global y por región.
  - Significancia de campo (Livezey y Chen 1983): % de píxeles con p<0,05 observado frente a su
    distribución nula por permutación. Si el % observado no supera el percentil 95 nulo, el mapa
    no es distinguible del azar aunque tenga píxeles "significativos".
Salidas en 03_Resultados/Agroclima/vigente/rendimiento/verificacion_ONI_pixel_<fecha>/ con mapas PNG.
Uso: .venv/Scripts/python.exe verificar_oni_por_pixel_maiz.py
"""
import math, sqlite3, sys, time, json, traceback
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path('C:/Users/paola/Tesis')
SRC = ROOT / '03_Resultados/Agroclima/vigente/rendimiento/cruce_anual_ONI_MJO_20261020_183145/cruce_rendimiento.sqlite'
AUDIT = ROOT / 'Repositorio/tesis-cereal-climate/outputs/agroclima_vigente/auditoria_rendimiento/maize/auditoria_por_pixel.csv'
PHASES = ['EST', 'VEG', 'FLO', 'REP', 'FIL', 'MAT']
MIN_PARES = 20
N_PERM = 1000
ALFA = 0.05
RNG = np.random.default_rng(20261023)

STAMP = time.strftime('%Y%m%d_%H%M%S')
OUT = ROOT / f'03_Resultados/Agroclima/vigente/rendimiento/verificacion_ONI_pixel_{STAMP}'
OUT.mkdir(parents=True, exist_ok=False)
LOG = open(OUT / 'registro.log', 'w', encoding='utf-8')
T0 = time.perf_counter()


def log(msg):
    line = f'[{time.perf_counter() - T0:7.0f} s] {msg}'
    print(line, flush=True); LOG.write(line + '\n'); LOG.flush()


def cargar():
    con = sqlite3.connect(f'file:{SRC.as_posix()}?mode=ro', uri=True)
    q = """select pixel_id, latitud, longitud, temporada, fase, alineacion, region, oni_ventana, dias_ventana,
                  z_rendimiento as z
           from pares_anuales where par_amenaza_rendimiento_valido = 1"""
    d = pd.concat(pd.read_sql_query(q, con, chunksize=500_000), ignore_index=True); con.close()
    log(f'  filas: {len(d):,}')
    keys = ['alineacion', 'pixel_id', 'temporada']
    w = d.pivot_table(index=keys, columns='fase', values='oni_ventana', aggfunc='first').reindex(columns=PHASES)
    w.columns = [f'ONI_{p}' for p in PHASES]
    d['ox'] = d.oni_ventana * d.dias_ventana
    o = d.dropna(subset=['oni_ventana']).groupby(keys)[['ox', 'dias_ventana']].sum()
    w['ONI_temporada'] = o.ox / o.dias_ventana
    meta = d.drop_duplicates(keys).set_index(keys)[['region', 'latitud', 'longitud', 'z']]
    return w.join(meta).reset_index()


def rank_rows(a):
    """Rangos por fila ignorando NaN (para Spearman)."""
    return pd.DataFrame(a).rank(axis=1).to_numpy()


def corr_rows(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    n = m.sum(1)
    x = np.where(m, x, np.nan); y = np.where(m, y, np.nan)
    xc = x - np.nanmean(x, 1, keepdims=True); yc = y - np.nanmean(y, 1, keepdims=True)
    num = np.nansum(xc * yc, 1); den = np.sqrt(np.nansum(xc ** 2, 1) * np.nansum(yc ** 2, 1))
    with np.errstate(invalid='ignore', divide='ignore'):
        r = num / den
    r[n < MIN_PARES] = np.nan
    return r, n


def fdr_bh(p):
    p = np.asarray(p, float); q = np.full_like(p, np.nan); ok = np.isfinite(p); m = ok.sum()
    if m == 0: return q
    i = np.argsort(p[ok]); r = p[ok][i] * m / np.arange(1, m + 1)
    r = np.minimum.accumulate(r[::-1])[::-1].clip(max=1); t = np.empty(m); t[i] = r; q[ok] = t
    return q


def mapa(df, col, titulo, ruta):
    try:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(14, 6.5), layout='constrained')
        base = df[df[col].notna()]
        sc = ax.scatter(base.longitud, base.latitud, c=base[col], cmap='RdBu', vmin=-.6, vmax=.6, s=4, lw=0)
        sig = base[base.q_fdr < ALFA]
        ax.scatter(sig.longitud, sig.latitud, facecolors='none', edgecolors='k', s=6, lw=.3)
        fig.colorbar(sc, ax=ax, shrink=.7, label='Spearman ONI vs rendimiento (contorno negro: FDR < 0,05)')
        ax.set_title(titulo); ax.set_xlim(-180, 180); ax.set_ylim(-60, 75); ax.set_aspect('equal')
        fig.savefig(ruta, dpi=130); plt.close(fig)
    except Exception as e:
        log(f'  (sin mapa {ruta.name}: {e})')


def main():
    W = cargar()
    audit = pd.read_csv(AUDIT, usecols=['pixel_id', 'clase'])
    plaus = set(audit.loc[audit.clase.isin(['OK', 'DUDOSO_RATIO_FAO']), 'pixel_id'])
    years = np.arange(1981, 2017)
    predictores = ['ONI_temporada'] + [f'ONI_{p}' for p in PHASES]
    filas, campo, campo_reg = [], [], []
    perms = np.stack([RNG.permutation(len(years)) for _ in range(N_PERM)])   # misma permutación para todos
    for al, d in W.groupby('alineacion'):
        info = d.drop_duplicates('pixel_id').set_index('pixel_id')[['region', 'latitud', 'longitud']]
        Y = d.pivot(index='pixel_id', columns='temporada', values='z').reindex(columns=years)
        pix = Y.index.to_numpy(); Yv = Y.to_numpy(float); Yr = rank_rows(Yv)
        for pred in predictores:
            X = d.pivot(index='pixel_id', columns='temporada', values=pred).reindex(index=pix, columns=years).to_numpy(float)
            Xr = rank_rows(X)
            r_p, n = corr_rows(X, Yv); r_s, _ = corr_rows(Xr, Yr)
            # nula por permutación de temporadas (Spearman)
            exceed = np.zeros(len(pix)); null_frac = {'todos': [], 'plausibles': []}
            mask_pl = np.isin(pix, list(plaus))
            for k, pm in enumerate(perms):
                rp, _ = corr_rows(Xr, Yr[:, pm])
                exceed += np.abs(rp) >= np.abs(r_s) - 1e-12
                null_frac['todos'].append(rp)
                if k % 200 == 0: log(f'  {al} | {pred}: permutación {k}/{N_PERM}')
            p_perm = (exceed + 1) / (N_PERM + 1)
            p_perm[~np.isfinite(r_s)] = np.nan
            # p paramétrico (Fisher) para el FDR: con 1.000 permutaciones el p mínimo es 0,001 y el FDR
            # sobre ~10.000 píxeles casi nunca puede rechazar (resolución insuficiente).
            z = np.arctanh(np.clip(r_s, -.999999, .999999)) * np.sqrt(np.clip(n - 3, 1, None))
            p_fisher = np.array([math.erfc(abs(v) / math.sqrt(2)) if np.isfinite(v) else np.nan for v in z])
            # p de cada píxel bajo cada permutación → % de píxeles con p<0,05 en el nulo
            R = np.abs(np.stack(null_frac['todos']))                      # N_PERM × píxeles
            umbral = np.nanpercentile(R, 95, axis=0)                      # |r| crítico por píxel al 5 %
            for esc, m in [('todos', np.isfinite(r_s)), ('plausibles', np.isfinite(r_s) & mask_pl)]:
                obs = 100 * np.mean(np.abs(r_s[m]) >= umbral[m])
                nula = 100 * np.mean(R[:, m] >= umbral[m], axis=1)
                campo.append(dict(alineacion=al, predictor=pred, escenario=esc, pixeles=int(m.sum()),
                                  pct_pixeles_p05_observado=obs, pct_nulo_p50=np.percentile(nula, 50),
                                  pct_nulo_p95=np.percentile(nula, 95),
                                  significancia_de_campo=bool(obs > np.percentile(nula, 95)),
                                  p_campo=(np.sum(nula >= obs) + 1) / (N_PERM + 1)))
            # significancia de campo por región (plausibles)
            regs = info.reindex(pix).region.to_numpy()
            for reg in pd.unique(regs):
                m = np.isfinite(r_s) & mask_pl & (regs == reg)
                if m.sum() < 30: continue
                obs = 100 * np.mean(np.abs(r_s[m]) >= umbral[m])
                nula = 100 * np.mean(R[:, m] >= umbral[m], axis=1)
                campo_reg.append(dict(alineacion=al, predictor=pred, region=reg, pixeles=int(m.sum()),
                                      rho_mediana=float(np.median(r_s[m])),
                                      pct_pixeles_p05_observado=obs, pct_nulo_p95=np.percentile(nula, 95),
                                      significancia_de_campo=bool(obs > np.percentile(nula, 95)),
                                      p_campo=(np.sum(nula >= obs) + 1) / (N_PERM + 1)))
            t = pd.DataFrame(dict(pixel_id=pix, alineacion=al, predictor=pred, n=n, pearson=r_p, spearman=r_s,
                                  p_perm=p_perm, p_fisher=p_fisher)).join(info, on='pixel_id')
            t['plausible'] = t.pixel_id.isin(plaus)
            t['q_fdr'] = fdr_bh(t.p_fisher)
            t['q_fdr_region'] = np.nan
            for _, idx in t.groupby('region').groups.items():
                t.loc[idx, 'q_fdr_region'] = fdr_bh(t.loc[idx, 'p_fisher'])
            filas.append(t)
            log(f'  {al} | {pred}: {np.isfinite(r_s).sum():,} píxeles | FDR<0,05: {(t.q_fdr < ALFA).sum():,} '
                f'| campo: {campo[-2]["pct_pixeles_p05_observado"]:.1f}% obs vs {campo[-2]["pct_nulo_p95"]:.1f}% nulo p95')
            if pred == 'ONI_temporada':
                mapa(t, 'spearman', f'ONI de temporada vs rendimiento z — {al}', OUT / f'mapa_ONI_temporada_{al}.png')
    res = pd.concat(filas, ignore_index=True); res.to_csv(OUT / 'oni_rendimiento_por_pixel.csv', index=False)
    pd.DataFrame(campo).to_csv(OUT / 'significancia_de_campo.csv', index=False)
    cr = pd.DataFrame(campo_reg); cr.to_csv(OUT / 'significancia_de_campo_por_region.csv', index=False)
    log('  regiones con significancia de campo:\n' + cr[cr.significancia_de_campo].round(2).to_string(index=False))
    reg = (res.assign(sig=res.q_fdr_region < ALFA, neg=(res.q_fdr_region < ALFA) & (res.spearman < 0),
                      pos=(res.q_fdr_region < ALFA) & (res.spearman > 0))
              .groupby(['alineacion', 'predictor', 'region'])
              .agg(pixeles=('pixel_id', 'size'), rho_mediana=('spearman', 'median'), pct_sig_FDR=('sig', 'mean'),
                   pct_sig_neg=('neg', 'mean'), pct_sig_pos=('pos', 'mean')).reset_index())
    for c in ['pct_sig_FDR', 'pct_sig_neg', 'pct_sig_pos']: reg[c] *= 100
    reg.to_csv(OUT / 'resumen_por_region.csv', index=False)
    log('  significancia de campo:\n' + pd.DataFrame(campo).round(2).to_string(index=False))
    json.dump(dict(fuente=str(SRC), n_perm=N_PERM, min_pares=MIN_PARES, semilla=20261023),
              open(OUT / 'procedencia.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    (OUT / 'LEEME.md').write_text(__doc__ + """
Cómo leer:
1. `significancia_de_campo.csv` primero: si `significancia_de_campo` es False, el conjunto de píxeles
   "significativos" no se distingue del azar para ese predictor y alineación.
2. `resumen_por_region.csv`: dónde están los píxeles con FDR<0,05 y con qué signo (se cancelan si mezclas signos).
3. `mapa_ONI_temporada_*.png`: solo se colorean píxeles con FDR<0,05.
4. `oni_rendimiento_por_pixel.csv`: detalle por píxel.
No elijas la alineación por el mejor resultado. Asociación no es causalidad.
""", encoding='utf-8')
    log(f'TERMINÓ. Resultados en {OUT}')


try:
    main()
except Exception as ex:
    log(f'ERROR: {ex}\n{traceback.format_exc()}'); sys.exit(1)
