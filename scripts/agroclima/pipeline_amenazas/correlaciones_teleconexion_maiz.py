"""¿Cómo actúan el ONI y la MJO sobre las amenazas del maíz (y sobre el rendimiento en años extremos)? Por píxel y grupo de calendario.

Eslabón que se prueba: ONI / MJO → amenaza de cada fase. Unidad: píxel × temporada, maturity-year, píxeles plausibles.
Objetivos (Y), uno a la vez: las 13 amenazas de la tabla v2 (mismas columnas que correlaciones_calendario_maiz.py)
y, solo para años extremos, el z de rendimiento.
Predictores (X), uno a la vez, cada valor mensual del ONI v6 entra una sola vez (sin promediar):
  ONI mes-k     ONI del mes que está k meses antes del mes en que EMPIEZA la fase (k = 0…6): ¿con cuánta anticipación actúa?
  Niño fuerte   1 si ese ONI (k = 0) ≥ +1,0; 0 si es neutral (|ONI| < 0,5); vacío si está entre 0,5 y 1,0.
  Niña fuerte   1 si ONI ≤ −1,0; 0 si neutral; vacío en los intermedios.
                Pearson con una variable 0/1 = diferencia estandarizada entre años extremos y neutrales.
  MJOk          fracción de los días de la misma fase del cultivo en la fase k de la MJO (k = 1…8); sin cosechas 2014–2016.
Para el rendimiento: Niño fuerte y Niña fuerte con el ONI del mes en que empieza FLO (fijado antes de ver resultados).
Resumen por grupo de calendario (grupos_calendario.csv de la corrida de correlaciones): mediana de r, % de píxeles
significativos por signo y significancia de campo por permutación de temporadas. El signo puede cambiar entre zonas:
para eso están los mapas (mapa_correlacion_pixel.py acepta esta corrida con --objetivo).
Uso: .venv/Scripts/python.exe correlaciones_teleconexion_maiz.py --grupos RUTA/grupos_calendario.csv [--perm 1000] [--muestra N]
"""
import argparse, sqlite3, time
from pathlib import Path
import numpy as np
import pandas as pd
from correlaciones_calendario_maiz import SQL, AUDIT, ONI, AMENAZAS, YEARS, corr_rows, p_fisher, fdr

FUERTE, NEUTRO = 1.0, 0.5


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--grupos', required=True); ap.add_argument('--perm', type=int, default=1000)
    ap.add_argument('--muestra', type=int, default=0)
    a = ap.parse_args()
    out = Path(a.grupos).parent / (f'teleconexion_{time.strftime("%Y%m%d_%H%M%S")}{"_sin_permutaciones" if not a.perm else ""}'
                                   f'{"_PRUEBA" if a.muestra else ""}')
    out.mkdir(parents=True)
    LOG = open(out / 'registro.log', 'w', encoding='utf-8'); t0 = time.perf_counter()
    def log(m):
        l = f'[{time.perf_counter() - t0:7.0f} s] {m}'; print(l, flush=True); LOG.write(l + '\n'); LOG.flush()

    G = pd.read_csv(a.grupos).set_index('pixel_id')
    plaus = set(pd.read_csv(AUDIT).query("clase in ['OK','DUDOSO_RATIO_FAO']").pixel_id)
    pix = np.array([p for p in G.index if p in plaus])
    if a.muestra: pix = np.random.default_rng(1).choice(pix, a.muestra, replace=False)
    con = sqlite3.connect(f'file:{SQL.as_posix()}?mode=ro', uri=True)
    q = """select pixel_id, temporada, fase, inicio, anio_rendimiento, z_rendimiento as z,
                  pct_dias_afectados, pct_dias_racha_v2, p_menos_et0, edd29, """ + \
        ', '.join(f'fraccion_dias_mjo_{k}' for k in range(1, 9)) + """
           from pares_v2 where alineacion = 'maturity-year' and par_amenaza_rendimiento_valido = 1"""
    d = pd.concat(pd.read_sql_query(q, con, chunksize=500_000), ignore_index=True); con.close()
    d = d[d.pixel_id.isin(set(pix))]
    log(f'filas: {len(d):,} · píxeles: {d.pixel_id.nunique():,}')

    def tabla(sub, col):
        return sub.pivot_table(index='pixel_id', columns='temporada', values=col, aggfunc='first').reindex(index=pix, columns=YEARS).to_numpy(float).copy()
    oni = pd.read_csv(ONI, parse_dates=['month_center'])
    oni_ym = dict(zip(oni.month_center.dt.year * 12 + oni.month_center.dt.month - 1, oni.oni))
    def oni_mes(ym, k):
        return np.vectorize(lambda v: oni_ym.get(int(v) - k, np.nan) if np.isfinite(v) else np.nan)(ym)
    def extremo(o, signo):
        x = np.full(o.shape, np.nan); x[np.abs(o) < NEUTRO] = 0
        x[(o >= FUERTE) if signo > 0 else (o <= -FUERTE)] = 1
        return x
    base = d.drop_duplicates(['pixel_id', 'temporada'])
    cosecha = tabla(base, 'anio_rendimiento'); excl = cosecha >= 2014

    pruebas = []  # (objetivo, predictor, familia, Y, X)
    for nom, col, fase, *_ in AMENAZAS:
        sub = d[d.fase == fase]
        Y = tabla(sub, col)
        ini = pd.to_datetime(sub.inicio); ym = tabla(sub.assign(ym=ini.dt.year * 12 + ini.dt.month - 1), 'ym')
        for k in range(7):
            pruebas.append((nom, f'ONI mes-{k}' if k else 'ONI mes de inicio', 'ONI', Y, oni_mes(ym, k)))
        o0 = oni_mes(ym, 0)
        pruebas.append((nom, 'Niño fuerte', 'ONI extremo', Y, extremo(o0, 1)))
        pruebas.append((nom, 'Niña fuerte', 'ONI extremo', Y, extremo(o0, -1)))
        for k in range(1, 9):
            X = tabla(sub, f'fraccion_dias_mjo_{k}'); X[excl] = np.nan
            pruebas.append((nom, f'MJO{k}', 'MJO', Y, X))
    flo = d[d.fase == 'FLO']; ini = pd.to_datetime(flo.inicio)
    o_flo = oni_mes(tabla(flo.assign(ym=ini.dt.year * 12 + ini.dt.month - 1), 'ym'), 0)
    Yz = tabla(base, 'z')
    pruebas.append(('rendimiento (z)', 'Niño fuerte', 'ONI extremo', Yz, extremo(o_flo, 1)))
    pruebas.append(('rendimiento (z)', 'Niña fuerte', 'ONI extremo', Yz, extremo(o_flo, -1)))
    log(f'pruebas por píxel: {len(pruebas)} (13 amenazas × [7 ONI + 2 extremos + 8 MJO] + 2 de rendimiento)')

    grp = G.reindex(pix).grupo.to_numpy(); grupos = ['todos'] + sorted(pd.unique(grp))
    rng = np.random.default_rng(20261028); perms = [rng.permutation(len(YEARS)) for _ in range(a.perm)]
    if not a.perm: log('SIN permutaciones: se calculan r, p por píxel y FDR; no hay significancia de campo (exploración).')
    filas, mat = [], []
    for obj, pred, fam, Y, X in pruebas:
        r, n = corr_rows(X, Y); p = p_fisher(r, n)
        n_ext = np.nansum(X == 1, axis=1) if fam == 'ONI extremo' else np.full(len(pix), np.nan)
        if a.perm:
            R = np.abs(np.stack([corr_rows(X, Y[:, pm])[0] for pm in perms]))
            crit = np.nanpercentile(R, 95, axis=0)
        filas.append(pd.DataFrame(dict(pixel_id=pix, grupo=grp, objetivo=obj, predictor=pred, familia=fam, n=n,
                                       anios_extremos=n_ext, pearson=r, p=p, q_fdr=fdr(p))))
        for g in grupos:
            m = np.isfinite(r) & ((grp == g) if g != 'todos' else True)
            if m.sum() < 30: continue
            sig = p[m] < .05
            if a.perm:
                obs = 100 * np.mean(np.abs(r[m]) >= crit[m]); nula = 100 * np.mean(R[:, m] >= crit[m], axis=1)
                campo = dict(pct_campo_obs=obs, pct_campo_nulo_p95=float(np.percentile(nula, 95)),
                             p_campo=float((np.sum(nula >= obs) + 1) / (a.perm + 1)))
            else:
                campo = dict(pct_campo_obs=np.nan, pct_campo_nulo_p95=np.nan, p_campo=np.nan)
            mat.append(dict(grupo=g, objetivo=obj, predictor=pred, familia=fam, pixeles=int(m.sum()),
                            r_mediana=float(np.median(r[m])), pct_sig_negativo=100 * float(np.mean(sig & (r[m] < 0))),
                            pct_sig_positivo=100 * float(np.mean(sig & (r[m] > 0))),
                            anios_extremos_mediana=float(np.nanmedian(n_ext[m])) if fam == 'ONI extremo' else np.nan, **campo))
        log(f'  {obj} ← {pred}: {np.isfinite(r).sum():,} píxeles · mediana r = {np.nanmedian(r):.3f}')
    pd.concat(filas).to_csv(out / 'correlacion_por_pixel.csv.gz', index=False)
    M = pd.DataFrame(mat); M['significancia_campo'] = M.p_campo < .05
    M.to_csv(out / 'matriz_grupos.csv', index=False)
    for fam, s in M.groupby('familia') if a.perm else []:
        log(f'{fam}: {int(s.significancia_campo.sum())} de {len(s)} celdas con p de campo < 0,05 (azar ≈ {0.05 * len(s):.1f}); '
            f'con Bonferroni (p < {0.05 / len(s):.5f}): {int((s.p_campo < 0.05 / len(s)).sum())} · resolución mínima del p: {1 / (a.perm + 1):.4f}')
    from html_teleconexion import construir
    construir(out, a.grupos)
    (out / 'LEEME.md').write_text(__doc__ + f"""
Fuentes: {SQL} (pares_v2) · {AUDIT} · ONI v6: {ONI} · grupos: {a.grupos}
Archivos: correlacion_por_pixel.csv.gz (un r por píxel × objetivo × predictor; anios_extremos = años Niño/Niña fuertes del píxel),
matriz_grupos.csv y matriz_teleconexion.html (una tabla por grupo; recuadro = significancia de campo con {a.perm} permutaciones).
Cautelas: con 1.000 permutaciones el p de campo mínimo es 0,001, así que Bonferroni sobre muchas celdas puede no alcanzarse;
los años extremos son pocos (ver anios_extremos); la mediana de r puede ser ≈ 0 aunque haya zonas con signos opuestos.
""", encoding='utf-8')
    log(f'TERMINÓ. Resultados en {out}')


def html(M, path, nperm):
    objs = list(dict.fromkeys(M.objetivo)); preds = list(dict.fromkeys(M.predictor))
    idx = {(r.grupo, r.objetivo, r.predictor): r for r in M.itertuples()}
    def celda(r):
        if r is None: return '<td class="na">—</td>'
        a = min(abs(r.r_mediana) / .3, 1) * 60; col = 'var(--neg)' if r.r_mediana < 0 else 'var(--pos)'
        t = (f'{r.objetivo} ← {r.predictor} · {r.grupo}: {r.pixeles} píx. · signif. − {r.pct_sig_negativo:.1f} % · + {r.pct_sig_positivo:.1f} % · '
             f'p de campo {r.p_campo:.3f}')
        return (f'<td{" class=campo" if r.significancia_campo else ""} title="{t}" style="background:color-mix(in srgb,{col} {a:.0f}%,transparent)">'
                f'{("%+.2f" % r.r_mediana).replace(".", ",").replace("-", "−")}</td>')
    bloques = ''
    for g in ['todos'] + sorted(x for x in M.grupo.unique() if x != 'todos'):
        sub = M[M.grupo == g]
        if sub.empty: continue
        filas = ''.join(f'<tr><td>{p}</td>' + ''.join(celda(idx.get((g, o, p))) for o in objs) + '</tr>' for p in preds)
        bloques += (f'<h2>{g} <span>{int(sub.pixeles.max()):,} píxeles</span></h2><div class="t"><table><thead><tr><th>Predictor ↓ · Objetivo →</th>'
                    + ''.join(f'<th>{o}</th>' for o in objs) + f'</tr></thead><tbody>{filas}</tbody></table></div>').replace(',', '.', 1)
    path.write_text(f"""<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ONI y MJO sobre amenazas</title>
<style>
:root{{--bg:#f6f7f3;--fg:#1d2420;--muted:#5d685f;--line:#d9ded6;--neg:#c0532a;--pos:#2a6f9e;--acc:#2f6b4f}}
@media (prefers-color-scheme:dark){{:root{{--bg:#141916;--fg:#e6ebe5;--muted:#9aa69c;--line:#2f3832;--neg:#e58a5c;--pos:#6fb0dc;--acc:#7cc19b;color-scheme:dark}}}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 "Segoe UI",system-ui,sans-serif;margin:0;padding:24px 16px}}
h1{{font-size:1.4rem;margin:0 0 8px}} h2{{font-size:1.05rem;margin:28px 0 6px;color:var(--acc)}} h2 span{{font-weight:400;color:var(--muted);font-size:.85rem}}
p{{max-width:80ch;margin:0 0 8px}} .t{{overflow-x:auto;border:1px solid var(--line);border-radius:8px}}
table{{border-collapse:collapse;font-variant-numeric:tabular-nums;font-size:.84rem}}
th,td{{padding:5px 8px;border-bottom:1px solid var(--line);text-align:center;white-space:nowrap}}
th{{color:var(--muted);font-size:.72rem;vertical-align:bottom}} td:first-child{{text-align:left}}
td.campo{{outline:2px solid var(--fg);outline-offset:-2px;font-weight:700}} td.na{{color:var(--muted)}}
</style>
<h1>¿Cómo actúan el ONI y la MJO sobre las amenazas del maíz?</h1>
<p>Cada celda: <b>mediana del r de Pearson</b> entre el predictor (fila) y el objetivo (columna), en los píxeles del grupo.
<span style="color:var(--neg)">Rojo</span> negativo, <span style="color:var(--pos)">azul</span> positivo.
{f"<b>Recuadro</b> = significancia de campo ({nperm} permutaciones de años)." if nperm else
 "<b>Corrida exploratoria SIN permutaciones:</b> no hay prueba de si el grupo supera al azar (ningún recuadro). Como guía, por azar se esperan ≈ 2,5 % de píxeles significativos de cada signo."}
Pasa el cursor para ver el % de píxeles significativos de cada signo: una mediana ≈ 0 con muchos píxeles significativos de ambos signos indica zonas opuestas.</p>
<p><b>ONI mes-k</b>: ONI k meses antes del inicio de la fase. <b>Niño/Niña fuerte</b>: |ONI| ≥ 1,0 contra años neutrales (|ONI| &lt; 0,5).
<b>MJOk</b>: fracción de días de la fase del cultivo en la fase k de la MJO (sin cosechas 2014–2016).</p>
{bloques}
""", encoding='utf-8')


if __name__ == '__main__':
    main()
