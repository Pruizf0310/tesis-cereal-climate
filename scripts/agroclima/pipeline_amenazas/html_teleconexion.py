"""Construye matriz_teleconexion.html (salida de correlaciones_teleconexion_maiz.py) con el mismo formato de matriz_grupos.html:
qué se prueba, cómo se agrupa, ranking, una gráfica de barras con interpretación por cada predictor → objetivo, y la matriz.

Los resúmenes (mediana, percentiles 10–90, % de píxeles significativos) se recalculan desde correlacion_por_pixel.csv.gz.
Sin permutaciones no hay prueba formal contra el azar: la barra llena marca solo que ≥ 10 % de los píxeles tienen r significativo
del mismo signo (4 veces el ≈ 2,5 % que da el azar). Es una guía de lectura, no una prueba.
Uso: python html_teleconexion.py --corrida RUTA_teleconexion [--grupos RUTA_grupos_calendario.csv] [--mapa RUTA_png_grupos]
"""
import argparse, base64, html
from pathlib import Path
import numpy as np
import pandas as pd
from html_matriz_grupos import TRIM, MES, PEQ, FASE, UMBRAL, coma, corto, barras

GUIA = 10.0  # % de píxeles significativos de un signo para marcar la barra (≈ 4 × azar)


def que_es_x(p):
    if p == 'ONI mes de inicio': return 'ONI v6 del mes en que empieza la fase (anomalía del Pacífico, Niño 3.4, °C; ≥ +0,5 El Niño, ≤ −0,5 La Niña).'
    if p.startswith('ONI mes-'): return f'ONI v6 de {p.split("-")[1]} meses antes del mes en que empieza la fase.'
    if p == 'Niño fuerte': return 'Año de El Niño fuerte (ONI ≥ +1,0 en el mes de inicio de la fase) contra años neutros (|ONI| < 0,5).'
    if p == 'Niña fuerte': return 'Año de La Niña fuerte (ONI ≤ −1,0 en el mes de inicio de la fase) contra años neutros (|ONI| < 0,5).'
    return f'Fracción de los días de la fase del cultivo en que la MJO estuvo en su fase {p[3]} (0 a 1). Sin cosechas 2014–2016.'


def que_es_y(o):
    if o.startswith('rendimiento'): return 'z del rendimiento (año de cosecha). Para el rendimiento se usa el ONI del mes en que empieza FLO.'
    f = o.split()[-1]
    if o.startswith('calor'): return f'% de días de {FASE[f]} con máxima ≥ {UMBRAL[f]} °C (rachas de ≥ 2 días).'
    if o.startswith('sequia'): return f'P − ETP sumada en {FASE[f]} (mm). Más alto = más agua.'
    if o.startswith('EDD29'): return f'Grados-día sobre 29 °C en {FASE[f]} (°C·día).'
    return '% de días de madurez (MAT) con lluvia > 10 mm.'


def efecto(o, p, s):
    """Qué significa un r de signo s para el par predictor → objetivo."""
    if o.startswith('sequia'): y = 'más agua' if s > 0 else 'menos agua (más seco)'
    elif o.startswith('rendimiento'): y = 'más rendimiento' if s > 0 else 'menos rendimiento'
    else:
        nom = {'calor': 'días de calor', 'EDD29': 'calor sobre 29 °C', 'lluvia': 'días de lluvia fuerte en la madurez'}[o.split()[0]]
        y = f'{"más" if s > 0 else "menos"} {nom}'
    if p.startswith('ONI'): return f'El Niño va con {y} y La Niña con lo contrario'
    if p == 'Niño fuerte': return f'en años de El Niño fuerte hay {y} que en años neutros'
    if p == 'Niña fuerte': return f'en años de La Niña fuerte hay {y} que en años neutros'
    return f'más días en la fase {p[3]} de la MJO van con {y}'


def lectura(o, p, sub, grupos, tam):
    def dir_(r):
        neg, pos = r.pct_sig_negativo, r.pct_sig_positivo
        s = -1 if neg >= pos else 1; a, b = (neg, pos) if s < 0 else (pos, neg)
        base = f'{coma(a, 1, False)} % de píxeles significativos {"negativos" if s < 0 else "positivos"} y {coma(b, 1, False)} % del otro signo'
        if a < GUIA: return base + ' (cerca de lo que da el azar)' if a < 2 * 2.5 else base + ' (por encima del azar, débil)'
        if b >= a / 2: return base + ': señal en los dos sentidos según la zona'
        return base + f' ({a / 2.5:.0f} veces el azar): {efecto(o, p, s)}'
    L = []
    t = sub.loc['todos'] if 'todos' in sub.index else None
    if t is not None:
        L.append(f'<b>Todos los píxeles:</b> mediana r = {coma(t.r_mediana)}; {dir_(t)}.')
    fuertes = [g for g in grupos[1:] if g in sub.index and max(sub.loc[g].pct_sig_negativo, sub.loc[g].pct_sig_positivo) >= GUIA]
    if fuertes:
        L.append('<b>Grupos con ≥ 10 % de un signo:</b> ' + '; '.join(
            f'{corto(g)} (mediana {coma(sub.loc[g].r_mediana)}): {dir_(sub.loc[g])}{" — grupo pequeño" if tam.get(g, 0) < PEQ else ""}'
            for g in fuertes) + '.')
    else:
        L.append('Ningún grupo llega a 10 % de píxeles significativos de un mismo signo.')
    if p in ('Niño fuerte', 'Niña fuerte') and 'anios_ext' in sub.columns and t is not None:
        L.append(f'Años extremos por píxel (mediana): {t.anios_ext:.0f}. Con tan pocos años la prueba solo detecta efectos grandes.')
    if not o.startswith('rendimiento') and p.startswith('ONI'):
        L.append('Cautela: la amenaza no tiene quitada la tendencia; si los años de El Niño caen en la parte más caliente del periodo, la relación puede salir inflada.')
    return '<ul class="interp">' + ''.join(f'<li>{x}</li>' for x in L) + '</ul>'


def construir(run, grupos_csv=None, mapa=None):
    run = Path(run)
    gpath = Path(grupos_csv) if grupos_csv else run.parent / 'grupos_calendario.csv'
    G = pd.read_csv(gpath)
    P = pd.read_csv(run / 'correlacion_por_pixel.csv.gz')
    P = P[P.pearson.notna()]
    sig = P.p < .05
    P = P.assign(neg=(sig & (P.pearson < 0)) * 100.0, pos=(sig & (P.pearson > 0)) * 100.0)
    def resumen(df):
        return df.groupby(['objetivo', 'predictor', 'familia']).agg(
            pixeles=('pearson', 'size'), r_mediana=('pearson', 'median'), r_p10=('pearson', lambda s: s.quantile(.1)),
            r_p90=('pearson', lambda s: s.quantile(.9)), pct_sig_negativo=('neg', 'mean'), pct_sig_positivo=('pos', 'mean'),
            anios_ext=('anios_extremos', 'median')).reset_index()
    M = pd.concat([resumen(P).assign(grupo='todos'), *[resumen(s).assign(grupo=g) for g, s in P.groupby('grupo')]])
    M = M[M.pixeles >= 30]
    M['significancia_campo'] = M[['pct_sig_negativo', 'pct_sig_positivo']].max(axis=1) >= GUIA  # guía visual (ver docstring)
    M['variable'] = M.predictor; M['p_campo'] = np.nan
    gs = [g for g in M.grupo.unique() if g != 'todos']; tam = M.groupby('grupo').pixeles.max().to_dict()
    grupos = ['todos'] + sorted(gs, key=lambda g: (g[0], -tam[g]))
    M.to_csv(run / 'resumen_grupos_desde_pixeles.csv', index=False)

    # cómo se agrupa
    filas_g = ''
    for g in grupos[1:]:
        s = G[G.grupo == g]; hem, trim = g.split(' · siembra ')
        regs = ', '.join(f'{k} ({v})' for k, v in s.region.value_counts().head(3).items())
        filas_g += (f'<tr><td><b>{corto(g)}</b></td><td>{"Norte" if hem == "N" else "Sur"}</td><td>{TRIM[trim]}</td>'
                    f'<td>{MES[int(s.mes_cosecha.mode().iloc[0]) - 1]}</td><td>{len(s):,}</td><td class="izq">{html.escape(regs)}</td>'
                    f'<td>{"pocos píxeles" if len(s) < PEQ else ""}</td></tr>').replace(',', '.', 1)
    img = (f'<img src="data:image/png;base64,{base64.b64encode(Path(mapa).read_bytes()).decode()}" alt="Mapa de grupos">'
           if mapa and Path(mapa).exists() else '')

    # ranking: grupos con al menos PEQ píxeles
    R = M[(M.grupo == 'todos') | M.grupo.map(lambda g: tam.get(g, 0) >= PEQ)].copy()
    R['dom'] = R[['pct_sig_negativo', 'pct_sig_positivo']].max(axis=1)
    R = R.sort_values('dom', ascending=False).head(25)
    rk = ''
    for r in R.itertuples():
        s = -1 if r.pct_sig_negativo >= r.pct_sig_positivo else 1
        rk += (f'<tr><td class="izq">{html.escape(r.predictor)} → {html.escape(r.objetivo)}</td><td>{corto(r.grupo)}</td>'
               f'<td class="izq"><span class="hb {"neg" if s < 0 else "pos"}" style="width:{min(r.dom, 70) / 70 * 100:.0f}%"></span></td>'
               f'<td><b>{coma(r.dom, 1, False)} %</b> {"−" if s < 0 else "+"}</td><td>{coma(r.r_mediana)}</td>'
               f'<td class="izq nota">{efecto(r.objetivo, r.predictor, s)}</td></tr>')

    # tarjetas por objetivo
    fuerza = R.groupby('objetivo').dom.max()
    objs = list(dict.fromkeys(M.objetivo)); objs = sorted(objs, key=lambda o: -fuerza.get(o, 0))
    secciones = ''
    for o in objs:
        tarjetas = ''
        for p in M[M.objetivo == o].predictor.drop_duplicates():
            sub = M[(M.objetivo == o) & (M.predictor == p)].set_index('grupo')
            tarjetas += (f'<div class="card"><h4>r entre {html.escape(p)} y {html.escape(o)}</h4>'
                         f'<p class="xy"><b>X</b> = {que_es_x(p)}<br><b>Y</b> = {que_es_y(o)}</p>'
                         f'{barras(sub, grupos, tam)}{lectura(o, p, sub, grupos, tam)}</div>')
        top = fuerza.get(o, 0)
        secciones += (f'<details{" open" if o == objs[0] else ""}><summary>{html.escape(o)} · máximo {coma(top, 1, False)} % de píxeles '
                      f'significativos de un signo</summary><div class="grid">{tarjetas}</div></details>')

    # matriz completa: una tabla por grupo, predictor (fila) × objetivo (columna)
    preds = list(dict.fromkeys(M.predictor)); objs_m = list(dict.fromkeys(M.objetivo))
    idx = {(r.grupo, r.objetivo, r.predictor): r for r in M.itertuples()}
    def celda(r):
        if r is None: return '<td class="m">—</td>'
        a = min(abs(r.r_mediana) / .3, 1) * 60
        t = (f'{r.predictor} → {r.objetivo} · {r.grupo}: {r.pixeles} píx. · signif. − {coma(r.pct_sig_negativo, 1, False)} % · '
             f'+ {coma(r.pct_sig_positivo, 1, False)} %')
        return (f'<td{" class=campo" if r.significancia_campo else ""} title="{html.escape(t)}" '
                f'style="background:color-mix(in srgb,var({"--neg" if r.r_mediana < 0 else "--pos"}) {a:.0f}%,transparent)">{coma(r.r_mediana)}</td>')
    matriz = ''
    for g in grupos:
        filas = ''.join(f'<tr><td class="izq">{html.escape(p)}</td>' + ''.join(celda(idx.get((g, o, p))) for o in objs_m) + '</tr>' for p in preds)
        matriz += (f'<details{" open" if g == "todos" else ""}><summary>{corto(g)} · {tam.get(g, 0):,} píxeles</summary>'.replace(',', '.')
                   + '<div class="t"><table><thead><tr><th class="izq">Predictor ↓ · Objetivo →</th>'
                   + ''.join(f'<th>{html.escape(o)}</th>' for o in objs_m) + f'</tr></thead><tbody>{filas}</tbody></table></div></details>')

    css = (Path(__file__).parent / 'html_matriz_grupos.py').read_text(encoding='utf-8')
    estilo = css[css.index('<style>'):css.index('</style>') + 8].replace('{{', '{').replace('}}', '}')
    out = run / 'matriz_teleconexion.html'
    out.write_text(f"""<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ONI y MJO sobre amenazas</title>
{estilo}
<h1>¿Cómo actúan el ONI y la MJO sobre las amenazas del maíz?</h1>
<p>Corrida <code>{run.name}</code>. Para cada píxel se calculó el r de Pearson entre <b>un</b> predictor (ONI o MJO) y <b>una</b> amenaza de la
tabla v2 en su fase (36 años, año de cosecha). También El Niño y La Niña fuertes contra el rendimiento. Aquí se resumen esos r por grupo.</p>

<h2>Qué se prueba</h2>
<div class="box">
<p>El eslabón <b>ONI / MJO → amenaza</b> de la cadena ONI → amenaza → rendimiento. Si el ONI cambia la amenaza en una zona y la amenaza baja el
rendimiento ahí, se explica por qué el ONI no aparece directo contra el rendimiento.</p>
<p><b>Predictores:</b> ONI de 0 a 6 meses antes de que empiece la fase (cada mes es un valor mensual del ONI v6, sin promediar);
El Niño y La Niña fuertes (|ONI| ≥ 1,0) contra años neutros; MJO: días de la misma fase del cultivo en cada fase 1–8 de la MJO.</p>
<p><b>Corrida exploratoria SIN permutaciones.</b> No hay prueba formal de si un grupo supera al azar. Como guía: por azar se espera ≈ 2,5 % de píxeles
significativos (p &lt; 0,05) de cada signo. <b>Barra llena</b> = un signo llega a ≥ 10 % de los píxeles (4 veces el azar); es una ayuda de lectura, no una prueba.
Los meses consecutivos del ONI se parecen entre sí: varios meses seguidos con señal son una sola señal, no varias.</p>
</div>

<h2>Cómo se agrupa</h2>
<div class="box">
<p><b>Grupo = hemisferio × trimestre de siembra</b> (mismos grupos de la matriz de rendimiento). Norte si la latitud es ≥ 0. Trimestre del mes en que empieza EST,
fijo en el calendario de cada píxel. DEF = dic–feb, MAM = mar–may, JJA = jun–ago, SON = sep–nov.</p>
<div class="t"><table><thead><tr><th>Grupo</th><th>Hemisferio</th><th>Siembra</th><th>Cosecha típica</th><th>Píxeles</th><th class="izq">Regiones con más píxeles</th><th></th></tr></thead>
<tbody>{filas_g}</tbody></table></div>
{img}
</div>

<h2>Dónde está la señal más fuerte</h2>
<p>Las 25 combinaciones con mayor % de píxeles significativos de un mismo signo (grupos con al menos {PEQ} píxeles). Azar ≈ 2,5 %.</p>
<div class="t"><table><thead><tr><th class="izq">Predictor → objetivo</th><th>Grupo</th><th class="izq" style="width:20%">Magnitud</th><th>% signif. (signo)</th><th>Mediana r</th><th class="izq">Lectura</th></tr></thead>
<tbody>{rk}</tbody></table></div>

<h2>Una gráfica por predictor, agrupadas por amenaza</h2>
<div class="box">
<div class="ley"><span class="l1">barra llena: ≥ 10 % de píxeles significativos de un signo</span><span class="l2">barra clara: menos</span>
<span class="l3">raya: 80 % de los r de los píxeles (p10–p90)</span></div>
<p class="nota" style="margin-top:6px">Rojo = r negativo, azul = positivo. Escala igual en todas. Grupos en amarillo: menos de {PEQ} píxeles. Las amenazas están ordenadas de la que tiene señal más fuerte a la más débil;
haz clic en cada una para abrirla.</p>
</div>
{secciones}

<h2>Matriz completa</h2>
<p class="nota">Mediana del r de los píxeles del grupo. Filas: predictor; columnas: amenaza (y rendimiento). Rojo negativo, azul positivo.
Recuadro = un signo llega a ≥ 10 % de píxeles significativos (guía, no prueba). Pasa el cursor sobre una celda para ver los % de cada signo. Un grupo por tabla.</p>
{matriz}
<p class="nota" style="margin-top:20px">Resumen numérico usado aquí: <code>resumen_grupos_desde_pixeles.csv</code> (recalculado desde <code>correlacion_por_pixel.csv.gz</code>).</p>
""", encoding='utf-8')
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--corrida', required=True)
    ap.add_argument('--grupos', default=None); ap.add_argument('--mapa', default=None)
    a = ap.parse_args(); print('Escrito', construir(a.corrida, a.grupos, a.mapa))
