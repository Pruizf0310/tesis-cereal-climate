"""Paquete de análisis sobre la SQLite v2 de maíz (sin GEE). Corre en orden y deja un resumen corto de una página.

A. Variabilidad entre años (criterio C4) de cada variable × fase.
B. Capacidad fuera de muestra por región (validación dejando un año fuera, panel con efecto fijo por píxel):
   R² fuera de muestra, AUC para años de pérdida (z < −1), tasa de aciertos (POD) y falsas alarmas (FAR).
   Modelos: M_calor_v1, M_completo (sequía 4 fases + EDD 3 fases), M_completo_ONI.
C. ONI de temporada dentro del modelo v2: t con SE agrupados por temporada.
D. Sensibilidad del umbral de sequía: Q1 por píxel frente a Q1 global (todas las celdas, como Le Roux et al. 2024).
E. Figuras: R² por región (v1 vs v2), AUC por región, mapas de Pearson (sequía VEG, EDD FIL).
F. resumen_v2.md (una página).
Escenario: píxeles plausibles; alineación maturity-year como principal y same-label como sensibilidad (no se elige por resultado).
Uso: .venv/Scripts/python.exe analisis_v2_maiz.py [--sqlite RUTA]
"""
import argparse, math, sqlite3, sys, time, traceback
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path('C:/Users/paola/Tesis')
SQL = ROOT / '03_Resultados/Agroclima/vigente/rendimiento/cruce_v2_20261024_184932/cruce_rendimiento_v2.sqlite'
AUDIT = ROOT / 'Repositorio/tesis-cereal-climate/outputs/agroclima_vigente/auditoria_rendimiento/maize/auditoria_por_pixel.csv'
PH = ['EST', 'VEG', 'FLO', 'REP', 'FIL', 'MAT']
MOD = {'M_calor_v1': [f'calor_v1|{p}' for p in PH],
       'M_completo': [f'sequia|{p}' for p in ['EST', 'VEG', 'FLO', 'FIL']] + [f'edd|{p}' for p in ['FLO', 'REP', 'FIL']]}
MOD['M_completo_ONI'] = MOD['M_completo'] + ['ONI']
PERDIDA = -1.0
MIN_FILAS = 500


def ols(X, y):
    b, *_ = np.linalg.lstsq(X, y, rcond=None); return b, y - X @ b


def cl_se(X, e, cl):
    inv = np.linalg.pinv(X.T @ X); meat = np.zeros((X.shape[1],) * 2)
    for c in np.unique(cl):
        m = cl == c; s = X[m].T @ e[m]; meat += np.outer(s, s)
    G = len(np.unique(cl)); n, k = X.shape
    return np.sqrt(np.diag(G / (G - 1) * (n - 1) / (n - k) * inv @ meat @ inv))


def auc(score, y):
    """AUC por rangos (Mann-Whitney): score bajo = más riesgo de pérdida."""
    y = np.asarray(y, bool); s = -np.asarray(score, float)
    n1, n0 = y.sum(), (~y).sum()
    if n1 == 0 or n0 == 0: return np.nan
    r = pd.Series(s).rank().to_numpy()
    return (r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--sqlite', default=str(SQL))
    a = ap.parse_args()
    out = Path(a.sqlite).parent / f'analisis_v2_{time.strftime("%Y%m%d_%H%M%S")}'; out.mkdir(parents=True)
    LOG = open(out / 'registro.log', 'w', encoding='utf-8'); t0 = time.perf_counter()
    def log(m):
        l = f'[{time.perf_counter() - t0:7.0f} s] {m}'; print(l, flush=True); LOG.write(l + '\n'); LOG.flush()

    con = sqlite3.connect(f'file:{Path(a.sqlite).as_posix()}?mode=ro', uri=True)
    q = """select pixel_id, latitud, longitud, temporada, fase, alineacion, region, z_rendimiento as z,
                  pct_dias_afectados, p_menos_et0, p_menos_et0_z, sequia_q1, edd29, oni_ventana, dias_ventana
           from pares_v2 where par_amenaza_rendimiento_valido = 1"""
    d = pd.concat(pd.read_sql_query(q, con, chunksize=500_000), ignore_index=True); con.close()
    plaus = set(pd.read_csv(AUDIT).query("clase in ['OK','DUDOSO_RATIO_FAO']").pixel_id)
    d = d[d.pixel_id.isin(plaus)]
    log(f'filas plausibles: {len(d):,}')
    keys = ['alineacion', 'pixel_id', 'temporada']
    W = pd.concat([
        d.pivot_table(index=keys, columns='fase', values='pct_dias_afectados', aggfunc='first').add_prefix('calor_v1|'),
        d.pivot_table(index=keys, columns='fase', values='p_menos_et0_z', aggfunc='first').add_prefix('sequia|'),
        d.pivot_table(index=keys, columns='fase', values='edd29', aggfunc='first').add_prefix('edd|')], axis=1)
    d['ox'] = d.oni_ventana * d.dias_ventana
    o = d.dropna(subset=['oni_ventana']).groupby(keys)[['ox', 'dias_ventana']].sum()
    W['ONI'] = o.ox / o.dias_ventana
    W = W.join(d.drop_duplicates(keys).set_index(keys)[['region', 'latitud', 'longitud', 'z']]).reset_index()

    # ---------- A. Variabilidad (C4) ----------
    try:
        filas = []
        for col in [c for c in W.columns if '|' in c]:
            g = W[W.alineacion == 'maturity-year'].groupby('pixel_id')[col]
            var = g.var(); ev = W[W.alineacion == 'maturity-year'].assign(e=W[col] > 0).groupby('pixel_id').e.sum()
            filas.append(dict(variable=col, pixeles=int(var.notna().sum()),
                              pct_pixeles_con_variacion=100 * float((var > 1e-12).mean()),
                              pct_pixeles_5_o_mas_anios_con_evento=100 * float((ev >= 5).mean()) if not col.startswith('sequia') else np.nan))
        A = pd.DataFrame(filas); A.to_csv(out / 'A_variabilidad_C4.csv', index=False)
        log('A listo:\n' + A.round(1).to_string(index=False))
    except Exception as e:
        log(f'ERROR A: {e}\n{traceback.format_exc()}'); A = pd.DataFrame()

    # ---------- B y C. Fuera de muestra + ONI ----------
    Brows, Crows = [], []
    for (al, reg), dd in W.groupby(['alineacion', 'region']):
        for mod, vs in MOD.items():
            try:
                sub = dd.dropna(subset=vs + ['z'])
                if len(sub) < MIN_FILAS: continue
                cen = sub[vs + ['z']] - sub.groupby('pixel_id')[vs + ['z']].transform('mean')
                sd = cen[vs].std(); use = [c for c in vs if sd[c] > 1e-9]
                X = (cen[use] / sd[use]).to_numpy(float); y = cen.z.to_numpy(float); yr = sub.temporada.to_numpy()
                pred = np.full(len(y), np.nan)
                for t in np.unique(yr):
                    tr = yr != t; b, _ = ols(X[tr], y[tr]); pred[~tr] = X[~tr] @ b
                r2o = 1 - np.sum((y - pred) ** 2) / np.sum(y ** 2)
                loss = sub.z.to_numpy() < PERDIDA
                cut = np.quantile(pred, loss.mean()) if loss.any() else np.nan
                alarm = pred <= cut
                pod = float((alarm & loss).sum() / max(loss.sum(), 1)); far = float((alarm & ~loss).sum() / max(alarm.sum(), 1))
                Brows.append(dict(alineacion=al, region=reg, modelo=mod, filas=len(sub), R2_fuera_muestra=r2o,
                                  AUC_perdida=auc(pred, loss), POD_aciertos=pod, FAR_falsas_alarmas=far,
                                  frecuencia_perdida=float(loss.mean())))
                if mod == 'M_completo_ONI' and 'ONI' in use:
                    b, e = ols(X, y); se = cl_se(X, e, yr); j = use.index('ONI')
                    Crows.append(dict(alineacion=al, region=reg, beta_ONI_por_1sd=b[j], t_ONI=b[j] / se[j]))
            except Exception as ex:
                log(f'ERROR B {al} {reg} {mod}: {ex}')
        log(f'B/C {al} | {reg}')
    B = pd.DataFrame(Brows); B.to_csv(out / 'B_fuera_de_muestra.csv', index=False)
    C = pd.DataFrame(Crows); C.to_csv(out / 'C_ONI_en_modelo_v2.csv', index=False)

    # ---------- D. Q1 por píxel vs Q1 global ----------
    try:
        m = d[d.alineacion == 'maturity-year'].copy()
        m['q1_global'] = m.groupby('fase').p_menos_et0.transform(lambda s: s.quantile(.25))
        m['sequia_q1_global'] = (m.p_menos_et0 < m.q1_global).astype(float)
        Drows = []
        for ph, g in m[m.fase.isin(['EST', 'VEG', 'FLO', 'FIL'])].groupby('fase'):
            for col in ['sequia_q1', 'sequia_q1_global']:
                r = g.groupby('pixel_id')[[col, 'z']].corr().xs(col, level=1)['z']
                n = g.groupby('pixel_id').size().reindex(r.index)
                zf = np.arctanh(r.clip(-.999999, .999999)) * np.sqrt((n - 3).clip(lower=1))
                p = zf.abs().apply(lambda v: math.erfc(v / math.sqrt(2)) if np.isfinite(v) else np.nan)
                Drows.append(dict(fase=ph, umbral=col, pixeles_con_variacion=int(r.notna().sum()),
                                  pearson_mediana=float(r.median()), pct_p05=100 * float((p < .05).mean())))
        D = pd.DataFrame(Drows); D.to_csv(out / 'D_q1_pixel_vs_global.csv', index=False)
        log('D listo:\n' + D.round(3).to_string(index=False))
    except Exception as e:
        log(f'ERROR D: {e}\n{traceback.format_exc()}'); D = pd.DataFrame()

    # ---------- E. Figuras ----------
    try:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
        b = B[B.alineacion == 'maturity-year']
        for met, fn in [('R2_fuera_muestra', 'E1_R2_fuera_muestra_por_region.png'), ('AUC_perdida', 'E2_AUC_perdida_por_region.png')]:
            p = b.pivot(index='region', columns='modelo', values=met).reindex(columns=list(MOD)).sort_values('M_completo')
            ax = p.plot.barh(figsize=(9, 8)); ax.set_xlabel(met); ax.axvline(0.5 if 'AUC' in met else 0, color='k', lw=.8)
            ax.set_title(f'{met} por región (maíz, maturity-year, plausibles)'); plt.tight_layout(); plt.savefig(out / fn, dpi=130); plt.close()
        mm = W[W.alineacion == 'maturity-year']
        for col, fn in [('sequia|VEG', 'E3_mapa_pearson_sequia_VEG.png'), ('edd|FIL', 'E4_mapa_pearson_EDD_FIL.png')]:
            r = mm.groupby('pixel_id')[[col, 'z']].corr().xs(col, level=1)['z']
            ll = mm.drop_duplicates('pixel_id').set_index('pixel_id')[['latitud', 'longitud']].join(r.rename('r')).dropna()
            fig, ax = plt.subplots(figsize=(14, 6.5), layout='constrained')
            sc = ax.scatter(ll.longitud, ll.latitud, c=ll.r, cmap='RdBu', vmin=-.6, vmax=.6, s=4, lw=0)
            fig.colorbar(sc, ax=ax, shrink=.7, label=f'Pearson {col} vs rendimiento z'); ax.set_xlim(-180, 180); ax.set_ylim(-60, 75)
            ax.set_aspect('equal'); ax.set_title(f'{col} vs rendimiento (maíz, maturity-year)'); fig.savefig(out / fn, dpi=130); plt.close(fig)
        log('E listo')
    except Exception as e:
        log(f'ERROR E: {e}\n{traceback.format_exc()}')

    # ---------- F. Resumen corto ----------
    try:
        b = B[B.alineacion == 'maturity-year'].pivot(index='region', columns='modelo', values=['R2_fuera_muestra', 'AUC_perdida'])
        top = b['AUC_perdida'].reindex(columns=list(MOD)).sort_values('M_completo', ascending=False).head(6)
        lines = ['# Resultados v2 de maíz — resumen', '',
                 f'Generado automáticamente el {time.strftime("%d %b %Y %H:%M")}. Píxeles plausibles, alineación maturity-year. '
                 'Revisar y redactar con criterio propio antes de enviar.', '',
                 '## Qué cambió', 'Se agregaron sequía por fase (P − ETP, Hargreaves) y grados-día sobre 29 °C (EDD29); FIL pasó a 32,9 °C.', '',
                 '## Capacidad para anticipar años de pérdida (z < −1), fuera de muestra', '',
                 '| Región | AUC v1 | AUC v2 | AUC v2 + ONI |', '|---|---|---|---|']
        for reg, r in top.iterrows():
            lines.append(f"| {reg} | {r.get('M_calor_v1', np.nan):.2f} | {r.get('M_completo', np.nan):.2f} | {r.get('M_completo_ONI', np.nan):.2f} |")
        lines += ['', 'AUC = 0,5 es azar; 1 es perfecto. Ver `B_fuera_de_muestra.csv` para todas las regiones, POD y FAR.', '']
        if len(C):
            cs = C[(C.alineacion == 'maturity-year') & (C.t_ONI.abs() >= 2)]
            lines += ['## ONI dentro del modelo v2', 'Regiones con |t| ≥ 2: ' + (', '.join(f'{r.region} ({r.t_ONI:+.1f})' for r in cs.itertuples()) or 'ninguna'), '']
        lines += ['## Decisiones pendientes', '1. Convención de año de GDHY (cambia el signo en África austral).',
                  '2. Umbral de FLO: 34,8 °C (VT–R1) o 33,7 °C (R1–R3).', '3. Q1 de sequía por píxel o global (ver `D_q1_pixel_vs_global.csv`).',
                  '4. Regla de rendimientos atípicos.', '',
                 'Figuras: `E1`–`E4`. Cautelas: ETP Hargreaves, regiones provisionales, asociación no es causalidad.']
        (out / 'resumen_v2.md').write_text('\n'.join(lines), encoding='utf-8')
        log('F listo')
    except Exception as e:
        log(f'ERROR F: {e}\n{traceback.format_exc()}')
    log(f'TERMINÓ. Resultados en {out}')


if __name__ == '__main__':
    main()
