"""Construye matriz_grupos.html a partir de matriz_grupos.csv y grupos_calendario.csv (salidas de correlaciones_calendario_maiz.py).

Contenido: (1) cómo se agrupa, con tabla y mapa de grupos; (2) ranking de las correlaciones más fuertes que superan al azar;
(3) un gráfico de barras por variable: barra = mediana del r de los píxeles del grupo, raya = rango del 80 % central de los r
(percentiles 10–90); barra llena = significancia de campo, barra clara = no supera al azar; (4) la matriz completa.
SVG generado aquí mismo: el archivo funciona sin internet.
Uso: python html_matriz_grupos.py --corrida RUTA_correlaciones_calendario [--mapa RUTA_png_grupos]
"""
import argparse, base64, html
from pathlib import Path
import numpy as np
import pandas as pd

TRIM = {'DEF': 'dic–feb', 'MAM': 'mar–may', 'JJA': 'jun–ago', 'SON': 'sep–nov'}
MES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
PEQ = 300  # grupos con menos píxeles: resultados inestables
LIM = .55


def desc(v):
    """Nombre legible del predictor para el título de cada gráfica."""
    if v == 'ONI mes de cosecha': return 'el ONI del mes de cosecha'
    if v.startswith('ONI mes-'): return f'el ONI de {v.split("-")[1]} meses antes de la cosecha'
    if v.startswith('MJO'): return f'los días en fase {v[3]} de la MJO durante {v.split(" en ")[1]}'
    return v


FASE = {'EST': 'establecimiento (EST)', 'VEG': 'crecimiento vegetativo (VEG)', 'FLO': 'floración (FLO)', 'REP': 'cuajado (REP)',
        'FIL': 'llenado de grano (FIL)', 'MAT': 'madurez (MAT)'}
UMBRAL = {'EST': '34,0', 'VEG': '34,6', 'FLO': '33,7', 'REP': '33,7', 'FIL': '32,9'}


def que_es(v):
    """Qué es X, en palabras, con unidad y fuente (tabla maestra v2, ONI v6, RMM)."""
    f = v.split()[-1]
    if v.startswith('calor'):
        return f'% de días de {FASE[f]} con temperatura máxima ≥ {UMBRAL[f]} °C, en rachas de 2 días o más.'
    if v.startswith('sequia'):
        return f'Lluvia menos evapotranspiración (P − ETP, Hargreaves) sumada en {FASE[f]}, en mm. Más alto = más agua; negativo = déficit.'
    if v.startswith('EDD29'):
        return f'Grados-día sobre 29 °C en {FASE[f]}: cada día suma lo que la máxima pasó de 29 °C (°C·día). Más alto = más calor dañino.'
    if v.startswith('lluvia'):
        return f'% de días de {FASE["MAT"]} con lluvia > 10 mm (exceso de lluvia en el secado).'
    if v.startswith('ONI'):
        k = 'del mes de cosecha' if v == 'ONI mes de cosecha' else f'de {v.split("-")[1]} meses antes del mes de cosecha'
        return (f'ONI v6 {k}: anomalía de temperatura del Pacífico (Niño 3.4, °C). ≥ +0,5 El Niño, ≤ −0,5 La Niña. '
                'Un valor por año, sin promediar.')
    k, fase = v[3], v.split(' en ')[1]
    return f'Fracción de los días de {FASE[fase]} en que la MJO estuvo en su fase {k} (0 a 1). Sin cosechas 2014–2016.'


def sentido(v, r):
    """Qué significa el signo de r para esta variable."""
    if v.startswith('sequia'):
        return 'más agua va con más rendimiento' if r > 0 else 'más agua va con menos rendimiento (posible exceso)'
    if v.startswith('ONI'):
        return ('El Niño va con más rendimiento y La Niña con menos' if r > 0 else 'El Niño va con menos rendimiento y La Niña con más')
    nom = {'calor': 'calor', 'EDD29': 'calor sobre 29 °C', 'lluvia': 'lluvia en la madurez'}.get(v.split()[0], f'días en esa fase de la MJO')
    return f'más {nom} va con {"menos" if r < 0 else "más"} rendimiento'


def magnitud(r):
    a = abs(r)
    return 'sin relación útil' if a < .1 else 'débil' if a < .3 else 'moderada'


def direccion(v, r):
    """Dirección según los píxeles significativos de cada signo (no según la mediana)."""
    neg, pos = r.pct_sig_negativo, r.pct_sig_positivo
    dom = -1 if neg >= pos else 1; a, b = (neg, pos) if dom < 0 else (pos, neg)
    if a < 2 * b:
        return (f'píxeles significativos de ambos signos ({coma(neg, 1, False)} % negativos, {coma(pos, 1, False)} % positivos): '
                'la relación existe pero cambia de sentido según la zona')
    return f'{coma(a, 1, False)} % de los píxeles con r significativo {"negativo" if dom < 0 else "positivo"} ({sentido(v, dom)}), contra {coma(b, 1, False)} % del otro signo'


def interpretar(v, sub, grupos, tam, fam_ok):
    """Lectura automática de la gráfica, solo con los números de matriz_grupos.csv."""
    L = []
    t = sub.loc['todos'] if 'todos' in sub.index else None
    if t is not None:
        L.append(f'<b>Todos los píxeles:</b> mediana r = {coma(t.r_mediana)} ({magnitud(t.r_mediana)} en el píxel típico). '
                 + (f'Supera al azar (p de campo {coma(t.p_campo, 3, False)}): {direccion(v, t)}.'
                    if t.significancia_campo else f'No supera al azar (p de campo {coma(t.p_campo, 3, False)}).'))
    sig = [g for g in grupos[1:] if g in sub.index and sub.loc[g].significancia_campo]
    if sig:
        L.append('<b>Grupos que superan al azar:</b> ' + '; '.join(
            f'{corto(g)}, mediana r = {coma(sub.loc[g].r_mediana)}: {direccion(v, sub.loc[g])}'
            f'{" (grupo pequeño)" if tam.get(g, 0) < PEQ else ""}' for g in sig) + '.')
    else:
        L.append('<b>Ningún grupo de calendario supera al azar.</b>')
    nos = sub.drop(index=['todos'] + sig, errors='ignore')
    if len(nos):
        g = nos.r_mediana.abs().idxmax(); r = nos.loc[g]
        if abs(r.r_mediana) >= .1:
            L.append(f'La barra más alta sin significancia es {corto(g)} (r = {coma(r.r_mediana)}): no alcanza para afirmarla.')
    mix = [g for g in grupos if g in sub.index and sub.loc[g].r_p10 < -.2 and sub.loc[g].r_p90 > .2]
    if mix:
        L.append(f'Rayas largas a ambos lados en {", ".join(corto(g) for g in mix)}: dentro del grupo hay zonas con signos opuestos '
                 '(revisar en el mapa).')
    if not fam_ok:
        L.append('<b>Cautela:</b> en esta familia de variables ninguna celda sobrevive a la corrección por número de pruebas; tómalo como indicio.')
    return '<ul class="interp">' + ''.join(f'<li>{x}</li>' for x in L) + '</ul>'


def corto(g):
    return 'Todos' if g == 'todos' else g.replace(' · siembra ', '·')


def orden_grupos(M):
    gs = [g for g in M.grupo.unique() if g != 'todos']
    tam = M.groupby('grupo').pixeles.max()
    return ['todos'] + sorted(gs, key=lambda g: (g[0], -tam[g]))


def coma(v, k=2, signo=True):
    s = (f'{v:+.{k}f}' if signo else f'{v:.{k}f}').replace('.', ',').replace('-', '−')
    return s


def barras(sub, grupos, tam):
    """SVG de barras verticales: mediana de r por grupo, con raya p10–p90."""
    W, H, L, B, T = 640, 230, 46, 46, 14
    bw = (W - L - 10) / len(grupos)
    Y = lambda v: T + (LIM - np.clip(v, -LIM, LIM)) / (2 * LIM) * (H - T - B)
    s = [f'<svg viewBox="0 0 {W} {H}" class="bar" role="img">']
    for v in [-.4, -.2, 0, .2, .4]:
        s.append(f'<line x1="{L}" x2="{W - 10}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" class="{"cero" if v == 0 else "grid"}"/>'
                 f'<text x="{L - 6}" y="{Y(v) + 4:.1f}" text-anchor="end" class="ax">{coma(v, 1, False)}</text>')
    for i, g in enumerate(grupos):
        x = L + i * bw; cx = x + bw / 2
        lab = corto(g); peq = g != 'todos' and tam.get(g, 0) < PEQ
        s.append(f'<text x="{cx:.1f}" y="{H - B + 16}" text-anchor="middle" class="ax{" peq" if peq else ""}">{lab}</text>'
                 f'<text x="{cx:.1f}" y="{H - B + 30}" text-anchor="middle" class="ax2">{tam.get(g, 0):,} píx.</text>'.replace(',', '.'))
        if g not in sub.index: continue
        r = sub.loc[g]; v = r.r_mediana
        y0, y1 = sorted([Y(0), Y(v)])
        cls = ('neg' if v < 0 else 'pos') + (' sig' if r.significancia_campo else '')
        tip = (f'{html.escape(r.variable)} · {g}: mediana r {coma(v)} · 80 % de los píxeles entre {coma(r.r_p10)} y {coma(r.r_p90)} · '
               f'signif. − {coma(r.pct_sig_negativo, 1, False)} % / + {coma(r.pct_sig_positivo, 1, False)} %'
               + (f' · p de campo {coma(r.p_campo, 3, False)}' if np.isfinite(r.p_campo) else ''))
        s.append(f'<g><title>{tip}</title>'
                 f'<line x1="{cx:.1f}" x2="{cx:.1f}" y1="{Y(r.r_p10):.1f}" y2="{Y(r.r_p90):.1f}" class="rango"/>'
                 f'<rect x="{x + bw * .2:.1f}" y="{y0:.1f}" width="{bw * .6:.1f}" height="{max(y1 - y0, 1):.1f}" rx="3" class="{cls}"/>'
                 f'<text x="{cx + 4:.1f}" y="{(Y(v) - 6 if v >= 0 else Y(v) + 14):.1f}" text-anchor="start" class="val{" sigt" if r.significancia_campo else ""}">{coma(v)}</text></g>')
    s.append('</svg>')
    return ''.join(s)


def construir(run, mapa=None):
    run = Path(run)
    M = pd.read_csv(run / 'matriz_grupos.csv')
    G = pd.read_csv(run / 'grupos_calendario.csv')
    grupos = orden_grupos(M); tam = M.groupby('grupo').pixeles.max().to_dict()
    nperm = int(round(1 / M.p_campo.min())) - 1

    # 1. cómo se agrupa
    filas_g = ''
    for g in grupos[1:]:
        s = G[G.grupo == g]; hem, trim = g.split(' · siembra ')
        regs = ', '.join(f'{k} ({v})' for k, v in s.region.value_counts().head(3).items())
        filas_g += (f'<tr><td><b>{corto(g)}</b></td><td>{"Norte" if hem == "N" else "Sur"}</td><td>{TRIM[trim]}</td>'
                    f'<td>{MES[int(s.mes_cosecha.mode().iloc[0]) - 1]}</td><td>{len(s):,}</td><td class="izq">{html.escape(regs)}</td>'
                    f'<td>{"pocos píxeles" if len(s) < PEQ else ""}</td></tr>').replace(',', '.', 1)
    img = ''
    if mapa and Path(mapa).exists():
        img = f'<img src="data:image/png;base64,{base64.b64encode(Path(mapa).read_bytes()).decode()}" alt="Mapa de grupos de calendario">'

    # 2. ranking
    fam_bonf = {f: int((s.p_campo < .05 / len(s)).sum()) for f, s in M.groupby('familia')}
    R = M[M.significancia_campo].assign(a=lambda t: t.r_mediana.abs()).sort_values('a', ascending=False).head(25)
    rk = ''
    for r in R.itertuples():
        notas = []
        if r.grupo != 'todos' and tam[r.grupo] < PEQ: notas.append('grupo pequeño')
        if fam_bonf.get(r.familia, 0) == 0: notas.append(f'{r.familia}: ninguna celda sobrevive a Bonferroni')
        w = abs(r.r_mediana) / .3 * 100
        rk += (f'<tr><td class="izq">{html.escape(r.variable)}</td><td>{corto(r.grupo)}</td>'
               f'<td class="izq"><span class="hb {"neg" if r.r_mediana < 0 else "pos"}" style="width:{min(w, 100):.0f}%"></span></td>'
               f'<td><b>{coma(r.r_mediana)}</b></td><td>{coma(r.pct_sig_negativo if r.r_mediana < 0 else r.pct_sig_positivo, 1, False)} %</td>'
               f'<td>{coma(r.p_campo, 3, False)}</td><td class="izq nota">{"; ".join(notas)}</td></tr>')

    # 3. barras por variable
    secciones = ''
    for titulo, fams, abierto in [('Amenazas', ['calor', 'sequia', 'EDD29', 'lluvia'], True), ('ONI mensual', ['ONI'], True), ('MJO', ['MJO'], False)]:
        vs = M[M.familia.isin(fams)].variable.drop_duplicates()
        tarjetas = ''
        for v in vs:
            sub = M[M.variable == v].set_index('grupo')
            esp = sub.signo_esperado.iloc[0]
            esp_t = {1: 'signo esperado: + (más agua, más rendimiento)', -1: 'signo esperado: − (más amenaza, menos rendimiento)'}.get(esp, 'sin signo esperado')
            fam = sub.familia.iloc[0]
            tarjetas += (f'<div class="card"><h4>r entre {html.escape(desc(v))} y el rendimiento</h4>'
                         f'<p class="xy"><b>X</b> = {que_es(v)}<br><b>Y</b> = z del rendimiento (año de cosecha). · {esp_t}</p>'
                         f'{barras(sub, grupos, tam)}{interpretar(v, sub, grupos, tam, fam_bonf.get(fam, 0) > 0)}</div>')
        secciones += f'<details{" open" if abierto else ""}><summary>{titulo} · {len(vs)} variables</summary><div class="grid">{tarjetas}</div></details>'

    # 4. matriz completa
    idx = {(r.grupo, r.variable): r for r in M.itertuples()}
    def celda(r):
        if r is None: return '<td class="m">—</td>'
        a = min(abs(r.r_mediana) / .3, 1) * 60
        return (f'<td{" class=campo" if r.significancia_campo else ""} style="background:color-mix(in srgb,var({"--neg" if r.r_mediana < 0 else "--pos"}) {a:.0f}%,transparent)">'
                f'{coma(r.r_mediana)}</td>')
    tabla = ''
    for titulo, fams, _ in [('Amenazas', ['calor', 'sequia', 'EDD29', 'lluvia'], 0), ('ONI mensual', ['ONI'], 0), ('MJO', ['MJO'], 0)]:
        tabla += f'<tr class="grp"><td colspan="{len(grupos) + 1}">{titulo}</td></tr>'
        for v in M[M.familia.isin(fams)].variable.drop_duplicates():
            tabla += f'<tr><td class="izq">{html.escape(v)}</td>' + ''.join(celda(idx.get((g, v))) for g in grupos) + '</tr>'
    head = '<tr><th class="izq">Variable</th>' + ''.join(f'<th>{corto(g)}</th>' for g in grupos) + '</tr>'

    out = run / 'matriz_grupos.html'
    out.write_text(f"""<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Matriz de correlaciones por calendario</title>
<style>
:root{{--bg:#f6f7f3;--sf:#fff;--fg:#1d2420;--muted:#5d685f;--line:#d9ded6;--neg:#c0532a;--pos:#2a6f9e;--acc:#2f6b4f;--warn:#a87612}}
@media (prefers-color-scheme:dark){{:root{{--bg:#141916;--sf:#1c231f;--fg:#e6ebe5;--muted:#9aa69c;--line:#2f3832;--neg:#e58a5c;--pos:#6fb0dc;--acc:#7cc19b;--warn:#e0b350;color-scheme:dark}}}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 "Segoe UI",system-ui,sans-serif;margin:0 auto;max-width:1200px;padding:24px 16px}}
h1{{font-size:1.5rem;margin:0 0 6px}} h2{{font-size:1.15rem;margin:34px 0 8px;color:var(--acc)}} h4{{margin:0;font-size:.95rem}}
p{{max-width:90ch;margin:0 0 8px}} .nota{{color:var(--muted);font-size:.8rem;margin:0}}
.box{{background:var(--sf);border:1px solid var(--line);border-radius:8px;padding:14px;margin:10px 0}}
.t{{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--sf)}}
table{{border-collapse:collapse;font-variant-numeric:tabular-nums;font-size:.86rem;width:100%}}
th,td{{padding:6px 9px;border-bottom:1px solid var(--line);text-align:center;white-space:nowrap}}
th{{color:var(--muted);font-size:.74rem;vertical-align:bottom}} .izq{{text-align:left}}
tr.grp td{{font-weight:600;color:var(--acc);text-align:left;background:var(--bg)}}
td.campo{{outline:2px solid var(--fg);outline-offset:-2px;font-weight:700}} td.m{{color:var(--muted)}}
img{{width:100%;height:auto;border-radius:6px;background:#fff;margin-top:8px}}
.hb{{display:inline-block;height:12px;border-radius:2px;vertical-align:middle}} .hb.neg{{background:var(--neg)}} .hb.pos{{background:var(--pos)}}
details{{margin:12px 0}} summary{{cursor:pointer;font-weight:600;font-size:1.02rem;color:var(--acc);padding:6px 0}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(430px,1fr));gap:12px}}
.card{{background:var(--sf);border:1px solid var(--line);border-radius:8px;padding:10px 12px;min-width:0}}
svg.bar{{width:100%;height:auto;display:block}}
.xy{{font-size:.8rem;color:var(--muted);margin:4px 0 0}} .xy b{{color:var(--fg)}}
ul.interp{{margin:6px 0 0;padding-left:18px;font-size:.84rem;display:grid;gap:3px}}
svg .grid{{stroke:var(--line);stroke-width:1}} svg .cero{{stroke:var(--muted);stroke-width:1.2}}
svg .ax{{fill:var(--muted);font-size:11px}} svg .ax2{{fill:var(--muted);font-size:9px}} svg .peq{{fill:var(--warn)}}
svg .rango{{stroke:var(--muted);stroke-width:1.5;opacity:.6}}
svg rect.neg{{fill:var(--neg);opacity:.3}} svg rect.pos{{fill:var(--pos);opacity:.3}} svg rect.sig{{opacity:1}}
svg .val{{fill:var(--muted);font-size:10.5px}} svg .sigt{{fill:var(--fg);font-weight:700}}
.ley{{display:flex;flex-wrap:wrap;gap:16px;font-size:.85rem;color:var(--muted)}} .ley span::before{{content:"";display:inline-block;width:14px;height:10px;margin-right:6px;vertical-align:middle;border-radius:2px}}
.l1::before{{background:var(--neg)}} .l2::before{{background:var(--neg);opacity:.3}} .l3::before{{background:var(--muted);width:2px!important;height:14px!important}}
@media (max-width:520px){{.grid{{grid-template-columns:1fr}}}}
</style>
<h1>Correlaciones del maíz con el rendimiento, por grupo de calendario</h1>
<p>Corrida <code>{run.name}</code>. Para cada píxel se calculó el r de Pearson entre el rendimiento (z, año de cosecha, 1981–2016) y <b>una</b> variable.
Aquí se resumen esos r por grupo. No se promedian datos entre píxeles: se resume el r de cada píxel.</p>

<h2>1. Cómo se agrupa</h2>
<div class="box">
<p><b>Grupo = hemisferio × trimestre en que se siembra.</b> Hemisferio: Norte si la latitud del píxel es ≥ 0, Sur si es negativa.
Trimestre: el mes en que empieza la fase EST (siembra) en el calendario del píxel, que es el mismo los 36 años. Los grupos se definieron antes de ver resultados.
Las letras son las iniciales de los meses: DEF = dic–feb, MAM = mar–may, JJA = jun–ago, SON = sep–nov.</p>
<p class="nota">Por qué así: el efecto del clima y del ENSO depende de la época del año en que el cultivo está en el campo. Límite: un grupo mezcla zonas con climas distintos
(por ejemplo, N·MAM junta EE. UU., China y África occidental), y en la franja ecuatorial el hemisferio dice poco de la temporada.</p>
<div class="t"><table><thead><tr><th>Grupo</th><th>Hemisferio</th><th>Siembra</th><th>Cosecha típica</th><th>Píxeles</th><th class="izq">Regiones con más píxeles</th><th></th></tr></thead>
<tbody>{filas_g}</tbody></table></div>
{img}
</div>

<h2>Cómo se decide si algo "supera al azar"</h2>
<div class="box">
<p><b>Permutaciones de años ({nperm}).</b> Se desordenan al azar los 36 años del rendimiento y se vuelve a calcular el r de cada píxel, dejando la variable
(amenaza, ONI o MJO) en su orden real. Así se rompe cualquier relación real entre los dos, pero cada serie conserva sus valores. Se repite {nperm} veces.</p>
<p><b>El mismo desorden para todos los píxeles.</b> En cada permutación los años se reordenan igual en todos los píxeles, para conservar que
píxeles vecinos se parecen entre sí (si un año fue malo en una región, lo fue en muchos píxeles a la vez).</p>
<p><b>Paso a paso, para cada variable y grupo:</b></p>
<ol>
<li><b>Umbral de cada píxel:</b> el valor de |r| que el azar supera solo el 5 % de las veces en ese píxel (percentil 95 de sus {nperm} |r| permutados).</li>
<li><b>% observado:</b> porcentaje de píxeles del grupo cuyo |r| real pasa su umbral.</li>
<li><b>% que da el azar:</b> el mismo porcentaje, calculado en cada una de las {nperm} permutaciones.</li>
<li><b>p de campo</b> = (número de permutaciones con un % igual o mayor que el observado + 1) / ({nperm} + 1). El mínimo posible es {coma(1 / (nperm + 1), 3, False)}.</li>
<li><b>Supera al azar</b> (barra llena, recuadro) si el p de campo es menor que 0,05.</li>
</ol>
<p class="nota">Dos aclaraciones: (a) la columna "% píxeles signif." usa otra prueba, la de cada píxel por separado (p &lt; 0,05 con la aproximación de Fisher, ≈ |r| ≥ 0,33 con 36 años);
la permutación es la que decide si el conjunto supera al azar. (b) Desordenar años rompe también la dependencia de un año con el siguiente; en el 34 % de los
píxeles esa autocorrelación pasa de 0,3, así que el umbral del azar puede quedar algo bajo y el p de campo algo optimista.</p>
</div>

<h2>2. Las correlaciones más fuertes que superan al azar</h2>
<p>Las 25 celdas (variable × grupo) con mayor |mediana de r| entre las que tienen significancia de campo ({nperm} permutaciones de años).
Cuidado con las notas: en ONI y MJO la cantidad de celdas significativas es la que daría el azar, y ninguna sobrevive a la corrección de Bonferroni.</p>
<div class="t"><table><thead><tr><th class="izq">Variable</th><th>Grupo</th><th class="izq" style="width:22%">Magnitud</th><th>Mediana r</th><th>% píxeles signif. (ese signo)</th><th>p de campo</th><th class="izq">Notas</th></tr></thead>
<tbody>{rk}</tbody></table></div>

<h2>3. Una gráfica por variable</h2>
<div class="box">
<div class="ley"><span class="l1">barra llena: supera al azar (significancia de campo)</span><span class="l2">barra clara: no supera al azar</span>
<span class="l3">raya: rango donde está el 80 % de los r de los píxeles (p10–p90)</span></div>
<p class="nota" style="margin-top:6px">Rojo = r negativo, azul = positivo. Escala igual en todas (−0,55 a +0,55). Nombres de grupo en amarillo: menos de {PEQ} píxeles, resultado inestable.
Una barra corta con raya larga hacia los dos lados indica zonas con signos opuestos dentro del grupo. Pasa el cursor sobre una barra para ver el detalle.</p>
</div>
{secciones}

<h2>4. Matriz completa</h2>
<p class="nota">Mediana de r. Recuadro = significancia de campo.</p>
<div class="t"><table><thead>{head}</thead><tbody>{tabla}</tbody></table></div>
""", encoding='utf-8')
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--corrida', required=True); ap.add_argument('--mapa', default=None)
    a = ap.parse_args(); print('Escrito', construir(a.corrida, a.mapa))
