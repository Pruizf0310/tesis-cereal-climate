"""Regresión en escalera para maíz: ¿qué agrega cada bloque de variables al rendimiento? Por grupo de calendario.

Unidad: píxel × temporada (año de cosecha = maturity-year), píxeles plausibles. Y = z_rendimiento.
Muestra común: cosechas 1981–2013 (el archivo RMM tiene señal ENSO desde 2014), así todos los modelos usan las mismas filas.
Modelos (regresión lineal con efecto fijo por píxel = cada variable centrada en la media del píxel):
  M1        13 amenazas de la tabla v2 (las mismas de correlaciones_calendario_maiz.py)
  M1_agua   M1 + (P − ETP)² en EST, VEG, FLO, FIL → deja que el exceso de agua también reste (curva, no recta)
  M2        M1_agua + ONI del mes en que empieza FLO (un valor mensual, sin promediar; mes fijado por fenología)
  M3        M2 + MJO: fracción de días de FLO en cada fase MJO 1–8
Por grupo de calendario (grupos_calendario.csv de la corrida de correlaciones) y para todos los píxeles:
  - Fuera de muestra, dejando un año fuera: medias y escalas del píxel se calculan SOLO con los años de entrenamiento.
    R² fuera de muestra, AUC de años de pérdida (z < −1), POD con alarma en el mismo % que la frecuencia de pérdida.
  - Coeficientes del modelo M3 ajustado con todos los años: beta por 1 DE y t con errores agrupados por año.
Uso: .venv/Scripts/python.exe regresion_escalera_maiz.py --grupos RUTA/grupos_calendario.csv [--muestra N]
"""
import argparse, sqlite3, time
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path('C:/Users/paola/Tesis')
SQL = ROOT / '03_Resultados/Agroclima/vigente/rendimiento/cruce_v2_20261024_184932/cruce_rendimiento_v2.sqlite'
AUDIT = ROOT / 'Repositorio/tesis-cereal-climate/outputs/agroclima_vigente/auditoria_rendimiento/maize/auditoria_por_pixel.csv'
ONI = ROOT / 'Repositorio/tesis-cereal-climate/outputs/agroclima_vigente/correlaciones/maize_ONI_Pearson/20261008_095854_51632d/oni_v6_monthly_centers.csv'
AMENAZAS = [('calor EST', 'pct_dias_afectados', 'EST'), ('sequia EST', 'p_menos_et0', 'EST'),
            ('calor VEG', 'pct_dias_afectados', 'VEG'), ('sequia VEG', 'p_menos_et0', 'VEG'),
            ('calor FLO', 'pct_dias_afectados', 'FLO'), ('sequia FLO', 'p_menos_et0', 'FLO'), ('EDD29 FLO', 'edd29', 'FLO'),
            ('calor REP', 'pct_dias_afectados', 'REP'), ('EDD29 REP', 'edd29', 'REP'),
            ('calor FIL', 'pct_dias_racha_v2', 'FIL'), ('sequia FIL', 'p_menos_et0', 'FIL'), ('EDD29 FIL', 'edd29', 'FIL'),
            ('lluvia MAT', 'pct_dias_afectados', 'MAT')]
M1 = [a[0] for a in AMENAZAS]
AGUA = [f'sequia {f}^2' for f in ['EST', 'VEG', 'FLO', 'FIL']]
MJO = [f'MJO{k} en FLO' for k in range(1, 9)]
MODELOS = {'M1': M1, 'M1_agua': M1 + AGUA, 'M2': M1 + AGUA + ['ONI inicio FLO'], 'M3': M1 + AGUA + ['ONI inicio FLO'] + MJO}
PERDIDA = -1.0
MIN_FILAS = 500


def auc(score, y):
    y = np.asarray(y, bool); s = -np.asarray(score, float); n1, n0 = y.sum(), (~y).sum()
    if n1 == 0 or n0 == 0: return np.nan
    r = pd.Series(s).rank().to_numpy()
    return (r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def centrar(df, cols, ref):
    """Centra y escala dentro del píxel usando solo las filas ref (entrenamiento)."""
    mu = df[ref].groupby('pixel_id')[cols].mean()
    c = df[cols] - mu.reindex(df.pixel_id).to_numpy()
    return c


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--grupos', required=True); ap.add_argument('--sqlite', default=str(SQL))
    ap.add_argument('--muestra', type=int, default=0)
    a = ap.parse_args()
    out = Path(a.grupos).parent / f'regresion_escalera_{time.strftime("%Y%m%d_%H%M%S")}{"_PRUEBA" if a.muestra else ""}'
    out.mkdir(parents=True)
    LOG = open(out / 'registro.log', 'w', encoding='utf-8'); t0 = time.perf_counter()
    def log(m):
        l = f'[{time.perf_counter() - t0:7.0f} s] {m}'; print(l, flush=True); LOG.write(l + '\n'); LOG.flush()

    G = pd.read_csv(a.grupos).set_index('pixel_id')
    plaus = set(pd.read_csv(AUDIT).query("clase in ['OK','DUDOSO_RATIO_FAO']").pixel_id)
    pix = [p for p in G.index if p in plaus]
    if a.muestra: pix = list(np.random.default_rng(1).choice(pix, a.muestra, replace=False))
    con = sqlite3.connect(f'file:{Path(a.sqlite).as_posix()}?mode=ro', uri=True)
    q = """select pixel_id, temporada, fase, inicio, anio_rendimiento, z_rendimiento as z, pct_dias_afectados, pct_dias_racha_v2,
                  p_menos_et0, edd29, """ + ', '.join(f'fraccion_dias_mjo_{k}' for k in range(1, 9)) + """
           from pares_v2 where alineacion = 'maturity-year' and par_amenaza_rendimiento_valido = 1"""
    d = pd.concat(pd.read_sql_query(q, con, chunksize=500_000), ignore_index=True); con.close()
    d = d[d.pixel_id.isin(set(pix)) & (d.anio_rendimiento <= 2013)]
    log(f'filas: {len(d):,} · píxeles: {d.pixel_id.nunique():,} · cosechas 1981–2013')

    keys = ['pixel_id', 'temporada']
    W = d.drop_duplicates(keys).set_index(keys)[['z', 'anio_rendimiento']]
    for nom, col, fase in AMENAZAS:
        W[nom] = d[d.fase == fase].set_index(keys)[col]
    for f in ['EST', 'VEG', 'FLO', 'FIL']:
        W[f'sequia {f}^2'] = W[f'sequia {f}'] ** 2
    flo = d[d.fase == 'FLO'].set_index(keys)
    ini = pd.to_datetime(flo.inicio)
    oni = pd.read_csv(ONI, parse_dates=['month_center'])
    oni_ym = dict(zip(oni.month_center.dt.year * 12 + oni.month_center.dt.month - 1, oni.oni))
    W['ONI inicio FLO'] = pd.Series((ini.dt.year * 12 + ini.dt.month - 1).map(oni_ym).to_numpy(), index=flo.index)
    for k in range(1, 9):
        W[f'MJO{k} en FLO'] = flo[f'fraccion_dias_mjo_{k}']
    W = W.reset_index()
    W['grupo'] = W.pixel_id.map(G.grupo)
    todas = MODELOS['M3']
    n0 = len(W); W = W.dropna(subset=todas + ['z'])
    log(f'filas con todas las variables: {len(W):,} de {n0:,} ({100 * len(W) / n0:.1f} %)')
    W[['pixel_id', 'temporada', 'grupo', 'z'] + todas].to_csv(out / 'datos_regresion.csv.gz', index=False)

    Brows, Crows = [], []
    for g in ['todos'] + sorted(W.grupo.unique()):
        dd = W if g == 'todos' else W[W.grupo == g]
        if len(dd) < MIN_FILAS: log(f'{g}: pocas filas ({len(dd)}), se omite'); continue
        dd = dd.reset_index(drop=True); yr = dd.anio_rendimiento.to_numpy()
        for mod, vs in MODELOS.items():
            pred = np.full(len(dd), np.nan); yc_all = np.full(len(dd), np.nan)
            for t in np.unique(yr):
                tr = yr != t
                Xc = centrar(dd, vs, tr); yc = centrar(dd, ['z'], tr).z.to_numpy()
                sd = Xc[tr].std().replace(0, np.nan); use = [c for c in vs if np.isfinite(sd[c])]
                X = (Xc[use] / sd[use]).to_numpy(float)
                b, *_ = np.linalg.lstsq(X[tr], yc[tr], rcond=None)
                pred[~tr] = X[~tr] @ b; yc_all[~tr] = yc[~tr]
            loss = dd.z.to_numpy() < PERDIDA
            cut = np.quantile(pred, loss.mean()) if loss.any() else np.nan
            Brows.append(dict(grupo=g, modelo=mod, variables=len(vs), filas=len(dd), pixeles=dd.pixel_id.nunique(),
                              R2_fuera_muestra=1 - np.sum((yc_all - pred) ** 2) / np.sum(yc_all ** 2),
                              AUC_perdida=auc(pred, loss), POD=float((pred <= cut)[loss].mean()), frecuencia_perdida=float(loss.mean())))
        # coeficientes de M3 con todos los años
        vs = MODELOS['M3']; allr = np.ones(len(dd), bool)
        Xc = centrar(dd, vs, allr); sd = Xc.std().replace(0, np.nan); use = [c for c in vs if np.isfinite(sd[c])]
        X = (Xc[use] / sd[use]).to_numpy(float); y = centrar(dd, ['z'], allr).z.to_numpy()
        b, *_ = np.linalg.lstsq(X, y, rcond=None); e = y - X @ b
        inv = np.linalg.pinv(X.T @ X); meat = np.zeros((X.shape[1],) * 2)
        for c in np.unique(yr):
            m = yr == c; s = X[m].T @ e[m]; meat += np.outer(s, s)
        Gn, (n, k) = len(np.unique(yr)), X.shape
        se = np.sqrt(np.diag(Gn / (Gn - 1) * (n - 1) / (n - k) * inv @ meat @ inv))
        for j, v in enumerate(use):
            Crows.append(dict(grupo=g, variable=v, beta_por_1DE=b[j], se_agrupado_anio=se[j], t=b[j] / se[j]))
        log(f'{g}: ' + ' · '.join(f"{r['modelo']} AUC {r['AUC_perdida']:.3f}" for r in Brows if r['grupo'] == g))
    B = pd.DataFrame(Brows); B.to_csv(out / 'escalera_por_grupo.csv', index=False)
    C = pd.DataFrame(Crows); C.to_csv(out / 'coeficientes_M3.csv', index=False)
    E = B.pivot(index='grupo', columns='modelo', values='AUC_perdida')
    E['agua_vs_M1'] = E.M1_agua - E.M1; E['ONI_vs_M1_agua'] = E.M2 - E.M1_agua; E['MJO_vs_M2'] = E.M3 - E.M2
    E.to_csv(out / 'escalera_AUC_resumen.csv')
    log('AUC por grupo y modelo (y cuánto agrega cada bloque):\n' + E.round(3).to_string())
    (out / 'LEEME.md').write_text(__doc__ + f"""
Fuentes: {a.sqlite} (pares_v2) · {AUDIT} · {ONI} · grupos: {a.grupos}
Archivos: datos_regresion.csv.gz (filas exactas que entran), escalera_por_grupo.csv, escalera_AUC_resumen.csv, coeficientes_M3.csv.
Lectura: AUC 0,5 = azar. Un bloque agrega información si sube el AUC y el R² fuera de muestra. |t| ≥ 2 ≈ coeficiente distinto de 0.
Cautelas: asociación, no causa; amenazas de calor colineales entre fases (los betas individuales son inestables);
ONI fijado al mes de inicio de FLO antes de ver resultados; MJO en FLO solamente.
""", encoding='utf-8')
    log(f'TERMINÓ. Resultados en {out}')


if __name__ == '__main__':
    main()
