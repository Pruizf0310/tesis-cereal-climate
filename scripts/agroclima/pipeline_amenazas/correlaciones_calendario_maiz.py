"""Correlaciones por píxel de maíz (rendimiento vs amenazas, ONI mensual y MJO), resumidas por grupo de calendario.

Qué se correlaciona (Pearson por píxel, una variable a la vez, años 1981–2016, alineación maturity-year = año de cosecha GDHY):
  Y  = z_rendimiento (GDHY sin tendencia, estandarizado por píxel), sin promediar nada.
  X  = una de estas variables, un valor por píxel y temporada:
   1. Amenazas de la tabla maestra v2 (13 variables por fase; la compuesta seco-cálida no está calculada):
      calor EST ≥34,0 · VEG ≥34,6 · FLO ≥33,7 · REP ≥33,7 °C  → pct_dias_afectados (reglas v1, ≥2 d)
      calor FIL ≥32,9 °C                                       → pct_dias_racha_v2 (≥2 d)
      sequía EST, VEG, FLO, FIL                                → p_menos_et0 (Σ diaria P − ETP Hargreaves, mm)
      EDD29 FLO, REP, FIL                                      → edd29 (Σ max(0, Tmax − 29), °C·día)
      lluvia MAT > 10 mm                                       → pct_dias_afectados (% de días)
   2. ONI mensual (ERSSTv6, un valor por mes, cada mes entra una sola vez): ONI del mes de cosecha y de los 11 meses
      anteriores (cosecha = mes en que termina MAT esa temporada). 12 variables: ONI_m0 … ONI_m-11.
   3. MJO (RMM): fracción de días de la fase del cultivo en cada fase MJO 1–8 (conteo de días / días de la ventana).
      48 variables. Se excluyen cosechas 2014–2016: desde 2014 el archivo RMM ya no tiene removida la señal ENSO.
Grupos de calendario (definidos antes de mirar resultados, no por resultado):
  grupo = hemisferio (latitud ≥ 0 → N) × trimestre del mes de siembra (mes modal de inicio de EST en el píxel).
  Por grupo NO se promedian datos: se resumen los r de los píxeles (mediana, % significativos) y se calcula
  significancia de campo por permutación de temporadas (misma permutación para todos los píxeles).
Uso: .venv/Scripts/python.exe correlaciones_calendario_maiz.py [--perm 1000] [--muestra N]
"""
import argparse, math, sqlite3, time
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path('C:/Users/paola/Tesis')
SQL = ROOT / '03_Resultados/Agroclima/vigente/rendimiento/cruce_v2_20261024_184932/cruce_rendimiento_v2.sqlite'
AUDIT = ROOT / 'Repositorio/tesis-cereal-climate/outputs/agroclima_vigente/auditoria_rendimiento/maize/auditoria_por_pixel.csv'
ONI = ROOT / 'Repositorio/tesis-cereal-climate/outputs/agroclima_vigente/correlaciones/maize_ONI_Pearson/20261008_095854_51632d/oni_v6_monthly_centers.csv'
YEARS = np.arange(1981, 2017)
MIN_PARES = 20
# (nombre, columna en pares_v2, fase, familia, signo esperado)
AMENAZAS = [('calor EST', 'pct_dias_afectados', 'EST', 'calor', -1), ('sequia EST', 'p_menos_et0', 'EST', 'sequia', 1),
            ('calor VEG', 'pct_dias_afectados', 'VEG', 'calor', -1), ('sequia VEG', 'p_menos_et0', 'VEG', 'sequia', 1),
            ('calor FLO', 'pct_dias_afectados', 'FLO', 'calor', -1), ('sequia FLO', 'p_menos_et0', 'FLO', 'sequia', 1),
            ('EDD29 FLO', 'edd29', 'FLO', 'EDD29', -1),
            ('calor REP', 'pct_dias_afectados', 'REP', 'calor', -1), ('EDD29 REP', 'edd29', 'REP', 'EDD29', -1),
            ('calor FIL', 'pct_dias_racha_v2', 'FIL', 'calor', -1), ('sequia FIL', 'p_menos_et0', 'FIL', 'sequia', 1),
            ('EDD29 FIL', 'edd29', 'FIL', 'EDD29', -1),
            ('lluvia MAT', 'pct_dias_afectados', 'MAT', 'lluvia', -1)]
FASES = ['EST', 'VEG', 'FLO', 'REP', 'FIL', 'MAT']
TRIM = {12: 'DEF', 1: 'DEF', 2: 'DEF', 3: 'MAM', 4: 'MAM', 5: 'MAM', 6: 'JJA', 7: 'JJA', 8: 'JJA', 9: 'SON', 10: 'SON', 11: 'SON'}


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


def fdr(p):
    p = np.asarray(p, float); q = np.full_like(p, np.nan); ok = np.isfinite(p); m = ok.sum()
    if m == 0: return q
    i = np.argsort(p[ok]); r = p[ok][i] * m / np.arange(1, m + 1)
    r = np.minimum.accumulate(r[::-1])[::-1].clip(max=1); t = np.empty(m); t[i] = r; q[ok] = t
    return q


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sqlite', default=str(SQL)); ap.add_argument('--perm', type=int, default=1000)
    ap.add_argument('--muestra', type=int, default=0, help='solo N píxeles al azar (prueba)')
    a = ap.parse_args()
    out = Path(a.sqlite).parent / f'correlaciones_calendario_{time.strftime("%Y%m%d_%H%M%S")}{"_PRUEBA" if a.muestra else ""}'
    out.mkdir(parents=True)
    LOG = open(out / 'registro.log', 'w', encoding='utf-8'); t0 = time.perf_counter()
    def log(m):
        l = f'[{time.perf_counter() - t0:7.0f} s] {m}'; print(l, flush=True); LOG.write(l + '\n'); LOG.flush()

    # ---------- 1. Datos ----------
    plaus = set(pd.read_csv(AUDIT).query("clase in ['OK','DUDOSO_RATIO_FAO']").pixel_id)
    con = sqlite3.connect(f'file:{Path(a.sqlite).as_posix()}?mode=ro', uri=True)
    mjo = [f'fraccion_dias_mjo_{k}' for k in range(1, 9)]
    q = f"""select pixel_id, latitud, longitud, region, temporada, fase, inicio, fin, anio_rendimiento, z_rendimiento as z,
                   pct_dias_afectados, pct_dias_racha_v2, p_menos_et0, edd29, {', '.join(mjo)}
            from pares_v2 where alineacion = 'maturity-year' and par_amenaza_rendimiento_valido = 1"""
    d = pd.concat(pd.read_sql_query(q, con, chunksize=500_000), ignore_index=True); con.close()
    d = d[d.pixel_id.isin(plaus)]
    if a.muestra:
        pick = np.random.default_rng(1).choice(d.pixel_id.unique(), a.muestra, replace=False); d = d[d.pixel_id.isin(pick)]
    log(f'filas maturity-year, píxeles plausibles: {len(d):,} · píxeles: {d.pixel_id.nunique():,}')

    # ---------- 2. Grupos de calendario ----------
    est = d[d.fase == 'EST'].assign(mes=lambda t: pd.to_datetime(t.inicio).dt.month)
    mat = d[d.fase == 'MAT'].assign(mes=lambda t: pd.to_datetime(t.fin).dt.month)
    info = d.drop_duplicates('pixel_id').set_index('pixel_id')[['latitud', 'longitud', 'region']]
    info['mes_siembra'] = est.groupby('pixel_id').mes.agg(lambda s: s.mode().iloc[0])
    info['mes_cosecha'] = mat.groupby('pixel_id').mes.agg(lambda s: s.mode().iloc[0])
    info['hemisferio'] = np.where(info.latitud >= 0, 'N', 'S')
    info['grupo'] = info.hemisferio + ' · siembra ' + info.mes_siembra.map(TRIM)
    info = info.dropna(subset=['mes_siembra'])
    info.to_csv(out / 'grupos_calendario.csv')
    log('píxeles por grupo:\n' + info.grupo.value_counts().to_string())

    # ---------- 3. Matrices píxel × año (una por variable) ----------
    pix = info.index.to_numpy()
    def tabla(sub, col):
        return sub.pivot_table(index='pixel_id', columns='temporada', values=col, aggfunc='first').reindex(index=pix, columns=YEARS).to_numpy(float).copy()
    base = d.drop_duplicates(['pixel_id', 'temporada'])
    Y = tabla(base, 'z')
    cosecha = tabla(base, 'anio_rendimiento')
    V = {}  # nombre -> (matriz, familia, fase, signo)
    for nom, col, fase, fam, sg in AMENAZAS:
        V[nom] = (tabla(d[d.fase == fase], col), fam, fase, sg)
    # ONI mensual por meses antes de la cosecha (fin de MAT de esa temporada)
    oni = pd.read_csv(ONI, parse_dates=['month_center'])
    oni_ym = dict(zip(oni.month_center.dt.year * 12 + oni.month_center.dt.month - 1, oni.oni))
    fin = d[d.fase == 'MAT'].assign(f=lambda t: pd.to_datetime(t.fin))
    ym_cos = tabla(fin.assign(ym=fin.f.dt.year * 12 + fin.f.dt.month - 1), 'ym')
    for k in range(12):
        m = np.vectorize(lambda v: oni_ym.get(int(v) - k, np.nan) if np.isfinite(v) else np.nan)(ym_cos)
        V[f'ONI mes-{k}' if k else 'ONI mes de cosecha'] = (m, 'ONI', f'cosecha-{k}', 0)
    # MJO: fracción de días por fase MJO dentro de cada fase del cultivo; sin cosechas 2014–2016
    excl = cosecha >= 2014
    for fase in FASES:
        sub = d[d.fase == fase]
        for k in range(1, 9):
            m = tabla(sub, f'fraccion_dias_mjo_{k}'); m[excl] = np.nan
            V[f'MJO{k} en {fase}'] = (m, 'MJO', fase, 0)
    log(f'variables: {len(V)} (amenazas {len(AMENAZAS)}, ONI 12, MJO 48)')

    # ---------- 4. Correlación por píxel + significancia de campo por grupo ----------
    rng = np.random.default_rng(20261027); perms = np.stack([rng.permutation(len(YEARS)) for _ in range(a.perm)])
    grp = info.grupo.to_numpy(); grupos = ['todos'] + sorted(pd.unique(grp))
    filas, mat_rows = [], []
    for nom, (X, fam, fase, sg) in V.items():
        r, n = corr_rows(X, Y); p = p_fisher(r, n)
        R = np.abs(np.stack([corr_rows(X, Y[:, pm])[0] for pm in perms]))
        crit = np.nanpercentile(R, 95, axis=0)
        filas.append(pd.DataFrame(dict(pixel_id=pix, grupo=grp, region=info.region.to_numpy(), variable=nom, familia=fam, fase=fase,
                                       n=n, pearson=r, p=p, q_fdr=fdr(p))))
        for g in grupos:
            m = np.isfinite(r) & ((grp == g) if g != 'todos' else True)
            if m.sum() < 30: continue
            sig = p[m] < .05
            obs = 100 * np.mean(np.abs(r[m]) >= crit[m]); nula = 100 * np.mean(R[:, m] >= crit[m], axis=1)
            mat_rows.append(dict(grupo=g, variable=nom, familia=fam, fase=fase, signo_esperado=sg, pixeles=int(m.sum()),
                                 r_mediana=float(np.median(r[m])), r_p10=float(np.percentile(r[m], 10)), r_p90=float(np.percentile(r[m], 90)),
                                 pct_sig_negativo=100 * float(np.mean(sig & (r[m] < 0))), pct_sig_positivo=100 * float(np.mean(sig & (r[m] > 0))),
                                 pct_campo_obs=obs, pct_campo_nulo_p95=float(np.percentile(nula, 95)),
                                 p_campo=float((np.sum(nula >= obs) + 1) / (a.perm + 1))))
        log(f'  {nom}: {np.isfinite(r).sum():,} píxeles · mediana r = {np.nanmedian(r):.3f}')
    pd.concat(filas).to_csv(out / 'correlacion_por_pixel.csv.gz', index=False)
    M = pd.DataFrame(mat_rows); M['significancia_campo'] = M.p_campo < .05
    M.to_csv(out / 'matriz_grupos.csv', index=False)

    # ---------- 5. Matriz HTML ----------
    from html_matriz_grupos import construir
    construir(out)
    (out / 'LEEME.md').write_text(__doc__ + f"""
Fuentes (solo lectura):
- Pares píxel-año: {a.sqlite} (vista pares_v2; amenazas v2 de GEE ERA5-Land y v1; z_rendimiento; fracciones MJO)
- Píxeles plausibles: {AUDIT} (clases OK y DUDOSO_RATIO_FAO)
- ONI v6 mensual: {ONI}
Archivos:
- grupos_calendario.csv: mes de siembra y de cosecha (modales) y grupo de cada píxel.
- correlacion_por_pixel.csv.gz: un r por píxel × variable (n, p de Fisher, q FDR global).
- matriz_grupos.csv / matriz_grupos.html: resumen por grupo × variable. p_campo < 0,05 = el % de píxeles
  significativos supera lo que da el azar ({a.perm} permutaciones de temporadas).
Cautelas: r con 36 años (|r| ≥ 0,33 ≈ p < 0,05); asociación, no causa; MJO sin cosechas 2014–2016;
la sequía es P − ETP continua (la tabla define el evento como < Q1); muchas pruebas: mirar significancia de campo.
""", encoding='utf-8')
    log(f'TERMINÓ. Resultados en {out}')


def html_matriz(M, info, path, nperm):
    gs = ['todos'] + [g for g in sorted(M.grupo.unique()) if g != 'todos']
    npx = {g: int(M[M.grupo == g].pixeles.max()) for g in gs}
    fams = [('Amenazas', ['calor', 'sequia', 'EDD29', 'lluvia']), ('ONI mensual', ['ONI']), ('MJO', ['MJO'])]
    def celda(row):
        if row is None: return '<td class="na">—</td>'
        r = row.r_mediana; a = min(abs(r) / .3, 1) * 60
        col = 'var(--neg)' if r < 0 else 'var(--pos)'
        cls = ' class="campo"' if row.significancia_campo else ''
        return (f'<td{cls} style="background:color-mix(in srgb,{col} {a:.0f}%,transparent)" '
                f'title="{row.variable} · {row.grupo}: {row.pixeles} píxeles · signif. negativos {row.pct_sig_negativo:.1f} % · positivos {row.pct_sig_positivo:.1f} % · p de campo {row.p_campo:.3f}">'
                f'{("%+.2f" % r).replace(".", ",").replace("-", "−")}</td>')
    idx = {(r.grupo, r.variable): r for r in M.itertuples()}
    body = ''
    for titulo, fl in fams:
        body += f'<tr class="grp"><td colspan="{len(gs) + 1}">{titulo}</td></tr>'
        for v in M[M.familia.isin(fl)].variable.drop_duplicates():
            body += f'<tr><td>{v}</td>' + ''.join(celda(idx.get((g, v))) for g in gs) + '</tr>'
    head = '<tr><th>Variable</th>' + ''.join(f'<th>{g}<br><span>{npx[g]:,} píx.</span></th>'.replace(',', '.') for g in gs) + '</tr>'
    path.write_text(f"""<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Matriz de correlaciones por calendario</title>
<style>
:root{{--bg:#f6f7f3;--fg:#1d2420;--muted:#5d685f;--line:#d9ded6;--neg:#c0532a;--pos:#2a6f9e;--acc:#2f6b4f}}
@media (prefers-color-scheme:dark){{:root{{--bg:#141916;--fg:#e6ebe5;--muted:#9aa69c;--line:#2f3832;--neg:#e58a5c;--pos:#6fb0dc;--acc:#7cc19b;color-scheme:dark}}}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 "Segoe UI",system-ui,sans-serif;margin:0;padding:24px 16px}}
h1{{font-size:1.4rem;margin:0 0 8px}} p{{max-width:75ch;margin:0 0 8px}}
.t{{overflow-x:auto;border:1px solid var(--line);border-radius:8px;margin-top:12px}}
table{{border-collapse:collapse;font-variant-numeric:tabular-nums;font-size:.88rem}}
th,td{{padding:6px 9px;border-bottom:1px solid var(--line);text-align:center;white-space:nowrap}}
th{{color:var(--muted);font-size:.75rem;vertical-align:bottom}} th span{{font-weight:400}}
td:first-child{{text-align:left}} tr.grp td{{font-weight:600;color:var(--acc);text-align:left;background:var(--bg)}}
td.campo{{outline:2px solid var(--fg);outline-offset:-2px;font-weight:700}} td.na{{color:var(--muted)}}
</style>
<h1>Correlación por píxel, resumida por grupo de calendario</h1>
<p>Cada celda es la <b>mediana del r de Pearson</b> de los píxeles del grupo (Y = z de rendimiento, año de cosecha, 1981–2016).
<span style="color:var(--neg)">Rojo</span> = negativo, <span style="color:var(--pos)">azul</span> = positivo; más intenso = más fuerte.
<b>Recuadro</b> = significancia de campo (el % de píxeles significativos supera al azar, {nperm} permutaciones).
Pasa el cursor sobre una celda para ver el % de píxeles significativos con cada signo.</p>
<p>Signo esperado: calor, EDD29 y lluvia en MAT negativo; sequía (P − ETP) positivo. ONI y MJO no tienen signo esperado global.</p>
<div class="t"><table><thead>{head}</thead><tbody>{body}</tbody></table></div>
""", encoding='utf-8')


if __name__ == '__main__':
    main()
