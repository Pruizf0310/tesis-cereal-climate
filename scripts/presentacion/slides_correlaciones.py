"""Correlaciones del píxel de Nebraska (después de «¿Y el clima? También puede tener tendencia»), por bloques:
A) amenaza → rendimiento: una diapositiva por fase (VEG, FLO, REP-pos, FIL; EST y MAT juntas) y la matriz resumen;
B) ENSO: la cadena índice → amenaza → rendimiento, el contexto Colombia frente a Nebraska y los veranos de transición.

Reejecutable: borra las diapositivas con la forma PX_numero y las vuelve a crear. Datos de
pixel_tipico/correlaciones_<fecha>/correlaciones.xlsx (pixel_tipico_correlaciones.py).
Uso (con el .venv del pipeline):  python slides_correlaciones.py --corr <carpeta correlaciones_...> [--salida ruta.pptx]
"""
import argparse, json, math
from pathlib import Path

import numpy as np
import pandas as pd
from pptx import Presentation
from pptx.chart.data import XyChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

from slides_pixel_tipico import (PPT, BG, TXT, TXT2, SRC, LINE, CIAN, MAG, PANEL, SERIF, SANS, SANSB, FASE_COLOR,
                                 caja, rect, base, estilo_ejes, puntos, recta, etiqueta, num, mover, renumerar, rgb)
from slide_tesis import AMARILLO
from slides_inicio import por_titulo

CALOR = 'E5484D'
FASES = ['EST', 'VEG', 'FLO', 'REP', 'FIL', 'MAT']
FUENTE = 'Fuente: pixel_tipico/correlaciones_{}/correlaciones.xlsx · píxel 191325 · 36 cosechas (1981–2016), todo sin tendencia lineal.'


def mezcla(h, a):
    """Color h sobre el panel con opacidad a (0–1)."""
    c = [int(h[i:i + 2], 16) for i in (0, 2, 4)]; b = [int(PANEL[i:i + 2], 16) for i in (0, 2, 4)]
    return ''.join(f'{round(b[k] + (c[k] - b[k]) * a):02X}' for k in range(3))


def nueva(prs, titulo, subtitulo, fuente, notas):
    s = base(prs, titulo, subtitulo, fuente, notas)
    for sh in s.shapes:
        if sh.name == 'PT_numero': sh.name = 'PX_numero'
    return s


def flecha(s, x1, y1, x2, y2, color, ancho=2.5):
    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = rgb(color); c.line.width = Pt(ancho)
    ln = c.line._get_or_add_ln(); fin = ln.makeelement('{http://schemas.openxmlformats.org/drawingml/2006/main}tailEnd', {})
    fin.set('type', 'triangle'); fin.set('w', 'med'); fin.set('len', 'med'); ln.append(fin)
    return c


# ---------- matrices fase × amenaza ----------
FILAS = [('conteo_original', 'Rachas de calor', 'episodios ≥ 2 días (MAT: días P > 10 mm)'), ('edd29', 'Calor continuo', 'EDD29, °C·día'),
         ('p_menos_et0', 'Balance de agua', 'P − ETP, mm')]


def matriz(s, celdas, color):
    """celdas[(fase, variable)] = (r, p, texto_debajo); color(r) da el tono de la celda."""
    x0, wc, y0, hf = 5.2, 2.13, 3.05, 1.35
    for j, f in enumerate(FASES):
        rect(s, x0 + j * wc, y0, wc - 0.08, 0.45, FASE_COLOR[f])
        caja(s, x0 + j * wc, y0, wc - 0.08, 0.45, [[('REP-pos' if f == 'REP' else f, SANSB, 15, BG)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    for i, (v, nom, sub) in enumerate(FILAS):
        y = y0 + 0.6 + i * (hf + 0.12)
        caja(s, 1.98, y, 3.1, hf, [[(nom, SANSB, 17, TXT)], [(sub, SANS, 13, SRC)]], anchor=MSO_ANCHOR.MIDDLE)
        for j, f in enumerate(FASES):
            r, p, debajo = celdas[(f, v)]; xx = x0 + j * wc
            if pd.isna(r):
                rect(s, xx, y, wc - 0.08, hf, PANEL)
                caja(s, xx, y, wc - 0.08, hf, [[('sin casos', SANS, 13, SRC)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE); continue
            sig = p < 0.05
            rect(s, xx, y, wc - 0.08, hf, mezcla(color(r), min(abs(r) / 0.75, 1) * (0.95 if sig else 0.35)))
            caja(s, xx, y + 0.12, wc - 0.08, hf - 0.5, [[(num(r if abs(r) >= 0.005 else 0.0), SERIF if sig else SANS, 26 if sig else 17, TXT if sig else SRC)]],
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
            caja(s, xx, y + hf - 0.42, wc - 0.08, 0.32, [[(debajo, SANS, 11.5, TXT2 if sig else SRC)]], align=PP_ALIGN.CENTER)
    return y0 + 0.6 + 3 * (hf + 0.12) + 0.15


# ---------- 1: qué amenaza se asocia con la cosecha ----------
def s_clima(prs, x, tag):
    c = x['clima_rendimiento'].set_index(['fase', 'variable']); se = x['serie']
    y = se.rendimiento_sin_tendencia_t_ha.values; anios = se.anio.values; k = anios != 2012
    n_sig = int((c.p < 0.05).sum()); n = int(c.r.notna().sum())
    celdas = {}
    for f in FASES:
        for v, _, _ in FILAS:
            r, p = c.loc[(f, v), ['r', 'p']]
            xv = se[f'{f}_{v}'].values.astype(float)
            r12 = r_sin(xv[k], y[k], anios[k])[0] if not pd.isna(r) else np.nan
            celdas[(f, v)] = (r, p, f'sin 2012: {num(r12)}' if not pd.isna(r12) else '')
    s = nueva(prs, 'Qué amenaza se asocia con la cosecha',
              'Correlación de cada amenaza con el rendimiento, fase por fase. Negativa: más amenaza, menos cosecha.',
              FUENTE.format(tag),
              f'r de Pearson entre la variable de la fase y el rendimiento GDHY, ambos sin tendencia lineal 1981–2016 (n = 36). '
              f'Con 36 años, |r| ≥ 0,33 equivale a p < 0,05. Pruebas: {n}; con p < 0,05: {n_sig}; por azar se esperaría ~{n * 0.05:.0f}.\n'
              '«Sin 2012»: r recalculado con 35 cosechas, para ver si la relación depende de la sequía de ese año. '
              'Sin 2012 se sostienen VEG (EDD29), FLO y FIL; REP-pos y MAT pierden significancia.\n'
              'Variables de la primera ronda (cruce_v2_20261024_184932): rachas = episodios de Tmax ≥ umbral ≥ 2 d (v1: FIL con 32,7 °C; VEG solo V7–VT); '
              'en MAT, días con P > 10 mm. EDD29 = Σ max(0, Tmax − 29 °C). P − ETP con ETP de Hargreaves (continuo; aún no la bandera Q1 de v2). '
              'En EST no hubo ninguna racha en 36 años.\n'
              'Las gráficas de dispersión por fase siguen disponibles en slides_correlaciones.py (s_fase) y los datos en correlaciones.xlsx; el ejemplo más fuerte '
              '(EDD29 en llenado) está en «Sin quitarla, la tecnología tapa al clima». Asociación, no causalidad demostrada.')
    yb = matriz(s, celdas, lambda r: CALOR if r < 0 else CIAN)
    caja(s, 1.98, yb, 16, 0.45, [[('Grande y claro = p < 0,05 (|r| ≥ 0,33 con 36 años).  ', SANS, 15, TXT2),
                                  (f'{n_sig} de {n} pruebas', SANSB, 15, TXT), (f' lo superan; por azar saldría ~{n * 0.05:.0f}.', SANS, 15, TXT2)]])
    caja(s, 1.98, yb + 0.55, 16, 0.45, [[('El calor pesa de VEG a FIL, y más en el llenado. ', SANSB, 15, CALOR),
                                         ('El agua solo pesa en el llenado. REP-pos y MAT dependen de 2012.', SANS, 15, TXT2)]])
    return s


# ---------- 2: qué tanto se asocia el ONI con cada amenaza ----------
def s_oni(prs, x, tag):
    i = x['indices']; o = i[i.indice == 'ONI']
    celdas = {}
    for f in FASES:
        for v, _, _ in FILAS:
            q = o[(o.ventana == f) & (o.objetivo == f'{f}_{v}')]
            r, p = (q.r.iloc[0], q.p.iloc[0]) if len(q) else (np.nan, np.nan)
            celdas[(f, v)] = (r, p, f'acompaña {abs(r) ** 2 * 100:.0f} %' if not pd.isna(r) else '')
    cli = i[i.objetivo != 'rendimiento'].dropna(subset=['r']); n, sig = len(cli), int((cli.p < 0.05).sum())
    s = nueva(prs, 'Qué tanto se asocia el ONI con cada amenaza',
              'ONI del mes central de cada fase frente a la variable de esa fase. Positiva: sube con El Niño; negativa: con La Niña.',
              FUENTE.format(tag),
              'r de Pearson entre el ONI (CPC v6, media móvil de 3 meses del mes central de la fase) y la variable de la fase, ambos sin tendencia, n = 36. '
              '«Acompaña X %» = r² × 100: la parte de la variación de un año a otro de la amenaza que se mueve junto con el ONI. No es causalidad.\n'
              f'Conteo completo del tramo índice → amenaza (ONI, RONI, ONI del invierno previo y MJO por pares de fases): {n} pruebas, {sig} con p < 0,05; '
              f'por azar se esperaría ~{n * 0.05:.0f}. Índice → rendimiento directo: 0 de 44.\n'
              'Lo único que pasa el umbral: ONI en VEG frente a rachas de calor en VEG (RONI −0,41): con La Niña, más rachas. '
              'Coincide en dirección con los veranos de transición, pero con 36 años no se puede afirmar.\n'
              'Siguiente paso posible: este mismo tramo con ERA5-Land 1950–2024 (no necesita rendimiento), pendiente de decidir.')
    yb = matriz(s, celdas, lambda r: CALOR if r > 0 else CIAN)
    caja(s, 1.98, yb, 16, 0.45, [[('Rojo = sube con El Niño · azul = sube con La Niña (en agua, subir es más húmedo). Grande y claro = p < 0,05.  ', SANS, 14, TXT2),
                                  (f'{sig} de {n} pruebas', SANSB, 14, TXT), (f'; azar ~{n * 0.05:.0f}.', SANS, 14, TXT2)]])
    caja(s, 1.98, yb + 0.55, 16, 0.45, [[('El ONI acompaña poco a la amenaza en Nebraska. ', SANSB, 15, CIAN),
                                         ('Correlación no es causalidad: esto es solo el primer filtro.', SANS, 15, TXT2)]])
    return s


# ---------- 2: la cadena ----------
def s_cadena(prs, x, res, tag):
    i = x['indices']; rend = i[i.objetivo == 'rendimiento'].dropna(subset=['r']); cli = i[i.objetivo != 'rendimiento'].dropna(subset=['r'])
    c = x['clima_rendimiento'].dropna(subset=['r'])
    tramos = [(len(cli), int((cli.p < 0.05).sum())), (len(c), int((c.p < 0.05).sum())), (len(rend), int((rend.p < 0.05).sum()))]
    pista = i[(i.indice == 'ONI') & (i.ventana == 'VEG') & (i.objetivo == 'VEG_conteo_original')].iloc[0]
    pista_r = i[(i.indice == 'RONI') & (i.ventana == 'VEG') & (i.objetivo == 'VEG_conteo_original')].iloc[0]
    s = nueva(prs, 'Una correlación lineal no ve el ENSO aquí',
              'Contamos cuántas correlaciones pasan p < 0,05 en cada tramo de la cadena y las comparamos con lo que daría el azar.',
              FUENTE.format(tag),
              'Pruebas por tramo (todas las series sin tendencia, n = 36):\n'
              f'- Índice → amenaza: ONI y RONI del mes central de cada fase y del invierno previo (DEF), y MJO (fracción de días con amplitud RMM ≥ 1, total y por pares de fases 8–1, 2–3, 4–5, 6–7) '
              f'en la ventana de cada fase, contra las tres variables de esa fase. {tramos[0][0]} pruebas, {tramos[0][1]} con p < 0,05; azar ~{tramos[0][0] * 0.05:.0f}.\n'
              f'- Amenaza → rendimiento: {tramos[1][0]} pruebas, {tramos[1][1]} con p < 0,05.\n'
              f'- Índice → rendimiento: {tramos[2][0]} pruebas, {tramos[2][1]} con p < 0,05; la más alta |r| = {rend.r.abs().max():.2f}.\n'
              f'Única pista con sentido físico: ONI en VEG frente a rachas de calor en VEG, r = {pista.r:.2f} (RONI {pista_r.r:.2f}): con El Niño, menos rachas. '
              'Pero el número total de aciertos está por debajo del azar, así que no se puede afirmar.\n'
              'Límites: un solo píxel; ventanas de FLO y REP de 9–10 días (la fracción de días MJO es ruidosa); en verano boreal la oscilación intraestacional dominante es la BSISO, no la MJO de invierno. '
              'RMM del BoM: ENSO retirado hasta 2013; desde 2014 solo la media de 120 días.')
    nodos = [(1.98, 'ONI · MJO', 'índices del océano y la atmósfera', CIAN), (7.6, 'Amenaza', 'calor y agua en cada fase', CALOR), (13.22, 'Rendimiento', 'sin tendencia', AMARILLO)]
    y = 3.4; w, h = 4.8, 1.5
    for xx, t, sub, col in nodos:
        rect(s, xx, y, w, h, PANEL, linea=col); rect(s, xx, y, w, 0.07, col)
        caja(s, xx, y + 0.1, w, h - 0.1, [[(t, SANSB, 24, col)], [(sub, SANS, 15, TXT2)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    flecha(s, 6.85, y + h / 2, 7.5, y + h / 2, SRC); flecha(s, 12.47, y + h / 2, 13.12, y + h / 2, SRC)

    def marcador(xx, ww, total, sig, color, apagado):
        caja(s, xx, 5.15, ww, 0.9, [[(f'{sig} de {total}', SERIF, 40, SRC if apagado else color)]], align=PP_ALIGN.CENTER)
        caja(s, xx, 6.05, ww, 0.4, [[(f'con p < 0,05 · el azar da ~{total * 0.05:.0f}', SANS, 15, TXT2)]], align=PP_ALIGN.CENTER)
    marcador(4.0, 5.4, *tramos[0], CIAN, True)
    marcador(9.9, 5.4, *tramos[1], CALOR, False)
    # tramo directo índice → rendimiento, por debajo
    rect(s, 4.38, 7.0, 11.24, 0.012, '334155'); rect(s, 4.38, 6.75, 0.012, 0.26, '334155'); rect(s, 15.62, 6.75, 0.012, 0.26, '334155')
    caja(s, 4.4, 7.1, 11.2, 0.9, [[('Directo, índice → rendimiento:  ', SANS, 17, TXT2), (f'{tramos[2][1]} de {tramos[2][0]}', SERIF, 30, SRC),
                                   (f'   (azar ~{tramos[2][0] * 0.05:.0f})', SANS, 15, TXT2)]], align=PP_ALIGN.CENTER)
    rect(s, 1.98, 8.35, 16.04, 1.1, PANEL); rect(s, 1.98, 8.35, 0.07, 1.1, MAG)
    caja(s, 2.35, 8.47, 15.5, 0.9, [[('Qué quiere decir: ', SANSB, 17, TXT),
                                    ('la amenaza explica la cosecha, pero el ONI de cada fase no ordena la amenaza en línea recta. '
                                     'No detectarlo no es lo mismo que no existir: el efecto puede ser débil, asimétrico o depender de cómo cambia el ENSO en el año.', SANS, 17, TXT2)]])
    return s


# ---------- fase por fase: amenaza → rendimiento ----------
VENTANA = dict(EST=('26 abr – 5 may', 10), VEG=('6 may – 8 jul', 64), FLO=('9 – 17 jul', 9), REP=('18 – 27 jul', 10),
               FIL=('28 jul – 5 sep', 40), MAT=('6 – 20 sep', 15))  # calendario_pixel de tendencia_20261029_175706 (VEG = V7–VT)
VAR_COL = {'conteo_original': CALOR, 'edd29': 'F59E0B', 'p_menos_et0': CIAN}


def etiqueta_var(f, v):
    if v == 'conteo_original': return 'Días con P > 10 mm' if f == 'MAT' else 'Rachas de calor (episodios)'
    return {'edd29': 'Calor continuo, EDD29 (°C·día)', 'p_menos_et0': 'Balance de agua, P − ETP (mm)'}[v]


def rango(v):
    lo, hi = float(np.nanmin(v)), float(np.nanmax(v))
    paso = next(p for p in (1, 2, 5, 10, 20, 25, 50, 100) if (hi - lo) / p <= 5)
    lo, hi = np.floor(lo / paso) * paso, np.ceil(hi / paso) * paso
    return lo, (hi if hi > lo else lo + paso), paso


def s_fase(prs, x, fases, titulo, mensaje, tag):
    c = x['clima_rendimiento'].set_index(['fase', 'variable']); se = x['serie']
    y = se.rendimiento_sin_tendencia_t_ha.values; anios = se.anio.values
    sub = ' · '.join(f'{"REP-pos" if f == "REP" else f}: {VENTANA[f][0]} ({VENTANA[f][1]} días)' for f in fases)
    s = nueva(prs, titulo, f'{sub}. Cada punto es una cosecha; en magenta, 2012.', FUENTE.format(tag),
              'Eje x: valor de la amenaza en la fase (sin quitar tendencia, para leerlo en sus unidades). Eje y: rendimiento sin tendencia (t/ha). '
              'El r de cada panel se calculó con ambas series sin tendencia (la diferencia con x crudo es ≤ 0,004 en mediana; diapositiva anterior).\n'
              'Series de la primera ronda (cruce_v2_20261024_184932): rachas = episodios de Tmax ≥ umbral ≥ 2 d (FIL con 32,7 °C de v1; VEG solo V7–VT); '
              'EDD29 = Σ max(0, Tmax − 29 °C); P − ETP con ETP de Hargreaves. Con 36 años, |r| ≥ 0,33 ↔ p < 0,05. Asociación, no causalidad demostrada.\n'
              '«Sin 2012»: r recalculado con 35 cosechas (tendencia ajustada sin ese año); en gris claro si sigue con p < 0,05, en gris oscuro si no. '
              'Sirve para ver si la relación depende de la sequía de 2012.')
    filas = len(fases); alto = 5.7 if filas == 1 else 2.95
    for i, f in enumerate(fases):
        y0 = 2.95 + i * (alto + 0.15)
        if filas > 1:
            rect(s, 1.7, y0 + 0.1, 0.12, alto - 0.2, FASE_COLOR[f])
        for j, v in enumerate(VAR_COL):
            x0 = 1.95 + j * 5.4
            xv = se[f'{f}_{v}'].values.astype(float); r, p = c.loc[(f, v), ['r', 'p']]
            caja(s, x0 + 0.1, y0, 3.9, 0.4, [[((f'{f} · ' if filas > 1 else '') + etiqueta_var(f, v), SANSB, 14, TXT)]])
            if pd.isna(r):
                rect(s, x0, y0 + 0.5, 5.1, alto - 0.6, PANEL)
                caja(s, x0, y0 + 0.5, 5.1, alto - 0.6, [[('ninguna racha en 36 años', SANS, 15, SRC)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
                continue
            sig = p < 0.05
            caja(s, x0 + 3.6, y0 - 0.08, 1.5, 0.5, [[('r = ' + num(r), SERIF if sig else SANS, 20 if sig else 15, VAR_COL[v] if sig else SRC)]], align=PP_ALIGN.RIGHT)
            k = anios != 2012; r12, p12 = r_sin(xv[k], y[k], anios[k])
            caja(s, x0 + 2.6, y0 + 0.38, 2.5, 0.35, [[('sin 2012: ' + num(r12), SANS, 12, TXT2 if p12 < 0.05 else SRC)]], align=PP_ALIGN.RIGHT)
            cd = XyChartData()
            a = cd.add_series('cosechas'); b = cd.add_series('2012')
            for xx, yy, an in zip(xv, y, anios): (b if an == 2012 else a).add_data_point(float(xx), float(yy))
            gf = s.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER, Inches(x0 - 0.25), Inches(y0 + 0.4), Inches(5.35), Inches(alto - 0.4), cd)
            ch = gf.chart; ch.has_legend = False
            lo, hi, paso = rango(xv)
            estilo_ejes(ch, lo, hi, -5, 2, paso, 1 if filas == 1 else 2)
            ch.font.size = Pt(12)
            puntos(ch.series[0], VAR_COL[v] if sig else '64748B', 9 if filas > 1 else 10); puntos(ch.series[1], MAG, 11)
    caja(s, 1.98, 9.45, 16, 0.5, [[(mensaje(c), SANSB, 16, TXT)]])
    return s


def r_sin(xv, yv, anios):
    """r con ambas series sin tendencia, sobre los años dados."""
    from scipy import stats
    if np.std(xv) == 0: return np.nan, np.nan
    d = lambda v: v - np.polyval(np.polyfit(anios, v, 1), anios)
    return stats.pearsonr(d(xv), d(yv))


R = lambda c, f, v: num(c.loc[(f, v), 'r'])
FASE_SLIDES = [
    (['VEG'], 'Vegetativo: el calor ya resta',
     lambda c: f'Más calor, menos cosecha (calor continuo {R(c, "VEG", "edd29")}). Pocas rachas: casi todos los años tienen cero, y sin 2012 la señal se debilita.'),
    (['FLO'], 'Floración: rachas y calor continuo',
     lambda c: f'Pesan las rachas ({R(c, "FLO", "conteo_original")}) y el calor continuo ({R(c, "FLO", "edd29")}), también sin 2012. El agua no alcanza.'),
    (['REP'], 'Cuajado: una señal que depende de 2012',
     lambda c: f'El calor continuo da {R(c, "REP", "edd29")}, pero sin 2012 baja y deja de ser significativo. Las rachas no alcanzan.'),
    (['FIL'], 'Llenado: la fase más sensible',
     lambda c: f'Calor continuo {R(c, "FIL", "edd29")}, rachas {R(c, "FIL", "conteo_original")} y agua +{R(c, "FIL", "p_menos_et0")}. Las tres se sostienen sin 2012.'),
    (['EST', 'MAT'], 'Inicio y final: casi sin señal',
     lambda c: f'En la siembra nada pasa el umbral; en la maduración solo el calor continuo ({R(c, "MAT", "edd29")}), y eso lo pone 2012.')]


# ---------- ENSO: contexto ----------
def s_contexto(prs, tag):
    s = nueva(prs, 'El mismo ENSO, efectos distintos',
              'Lo que sabemos del ENSO en Colombia no se puede trasladar a Nebraska.', None,
              'Colombia: Poveda, G., Álvarez, D. M. y Rueda, Ó. A. (2011). Hydro-climatic variability over the Andes of Colombia associated with ENSO. '
              'Climate Dynamics, 36, 2233–2249. https://doi.org/10.1007/s00382-010-0931-y. Revisión con lluvia, caudales, humedad del suelo y NDVI: anomalías negativas en El Niño '
              '(sequías, heladas, incendios) y positivas en La Niña (lluvias torrenciales, inundaciones, deslizamientos).\n'
              'EE. UU. en verano: Barnston, A. (2015, 28 de mayo). With El Niño likely, what climate impacts are favored for this summer? NOAA Climate.gov, blog ENSO (archivado). '
              'En verano la circulación de Hadley y los patrones de latitudes medias son más débiles, y El Niño tiene efectos mayormente débiles o insignificantes en EE. UU.\n'
              'Transición: Jong, B.-T., Ting, M. y Seager, R. (2021). Assessing ENSO summer teleconnections, impacts, and predictability in North America. '
              'Journal of Climate, 34(9), 3629–3643. https://doi.org/10.1175/JCLI-D-20-0761.1. Resumen: en el verano en que El Niño pasa a La Niña, las teleconexiones dan '
              'anomalías cálidas robustas sobre el Medio Oeste, que amenazan la producción agrícola. Los modelos climáticos no lo reproducen bien.\n'
              'Verificado contra Crossref y el resumen el 2 nov 2026; leer el texto completo de Jong et al. antes de la defensa.')
    cols = [(1.98, 'Colombia', 'Andes · todo el año', [('El Niño', 'Menos lluvia, caudal y humedad del suelo: sequías, heladas e incendios.'),
                                                          ('La Niña', 'Más lluvia y suelos saturados: inundaciones y deslizamientos.')],
             'Poveda et al. (2011)', 'https://doi.org/10.1007/s00382-010-0931-y'),
            (10.2, 'Nebraska', 'verano del maíz', [('El Niño', 'Efecto débil o insignificante en el verano de EE. UU.'),
                                                   ('Niño → Niña', 'El verano en que El Niño pasa a La Niña: calor fuerte en el Medio Oeste.')],
             'Barnston (2015) · Jong et al. (2021)', 'https://doi.org/10.1175/JCLI-D-20-0761.1')]
    for x0, lugar, sub, filas, ref, url in cols:
        rect(s, x0, 2.95, 7.82, 4.65, PANEL); rect(s, x0, 2.95, 7.82, 0.07, CIAN)
        caja(s, x0 + 0.35, 3.15, 7.2, 0.6, [[(lugar, SANSB, 26, TXT), ('   ' + sub, SANS, 16, SRC)]])
        for k, (fase, txt) in enumerate(filas):
            yy = 4.05 + k * 1.45
            col = CALOR if fase == 'El Niño' else ('F59E0B' if '→' in fase else CIAN)
            caja(s, x0 + 0.35, yy, 2.2, 1.2, [[(fase, SANSB, 19, col)]])
            caja(s, x0 + 2.6, yy, 4.9, 1.3, [[(txt, SANS, 17, TXT2)]])
        tb = caja(s, x0 + 0.35, 7.0, 7.2, 0.4, [[(ref, SANS, 13, CIAN)]])
        tb.text_frame.paragraphs[0].runs[0].hyperlink.address = url
    caja(s, 1.98, 7.85, 16, 0.9, [[('Por qué: ', SANSB, 17, TXT),
                                   ('en el trópico el ENSO mueve directamente dónde llueve; a latitudes medias llega por la circulación atmosférica, '
                                    'que en verano es débil.', SANS, 17, TXT2)]])
    rect(s, 1.98, 8.85, 16.04, 0.9, PANEL); rect(s, 1.98, 8.85, 0.07, 0.9, 'F59E0B')
    caja(s, 2.35, 8.85, 15.5, 0.9, [[('Pregunta para Nebraska: ', SANSB, 17, TXT),
                                     ('¿los veranos de transición Niño → Niña traen más calor y menos cosecha?', SANS, 17, TXT2)]], anchor=MSO_ANCHOR.MIDDLE)
    return s


# ---------- ENSO: trayectoria del año ----------
TRAY = [('Niño en verano', CALOR), ('Niño→Niña', 'F59E0B'), ('Niña persistente', CIAN), ('Otro', '64748B')]


def s_trayectoria(prs, x, res, tag):
    se = x['serie']; t = x['enso_trayectoria'].set_index('tipo')
    s = nueva(prs, 'Los veranos de transición',
              'Clasificamos cada año por cómo cambia el ONI de diciembre–febrero a julio–septiembre. Anomalías sin tendencia.',
              FUENTE.format(tag),
              'Tipos (ONI CPC v6): Niño→Niña si DEF ≥ 0,5 y JAS ≤ −0,5; Niña persistente si ambos ≤ −0,5; Niño en verano si JAS ≥ 0,5; resto, otro.\n'
              + ''.join(f'{k} ({int(f.anios)}): {f.lista}.\n' for k, f in t.iterrows()) +
              f'Niño→Niña frente al resto (Mann-Whitney): rendimiento p = {t.loc["Niño→Niña", "p_mw_rendimiento"]:.2f}; EDD29 en llenado p = {t.loc["Niño→Niña", "p_mw_FIL_edd29"]:.2f}.\n'
              'La dirección coincide con Jong, Ting y Seager (2021), pero con 6 años no se puede afirmar. Dos de los seis (1988 y 1995) fueron malos; 1998, 2010 y 2016 no.\n'
              'P − ETP en llenado no fue más seco en los años de transición (anomalía media +11 mm): la señal es de calor, no de lluvia.\n'
              f'Siguiente: tramo ONI → amenaza con ERA5-Land 1950–2024 (no necesita rendimiento): {len(res.get("transicion_1950_2024", []))} veranos de transición '
              f'({", ".join(map(str, res.get("transicion_1950_2024", [])))}).')
    paneles = [('FIL_edd29_sin_tendencia', 'Calor continuo en llenado (°C·día)', -50, 75, 25, 'FIL_edd29_anomalia', '0'),
               ('rendimiento_sin_tendencia_t_ha', 'Rendimiento (t/ha)', -5, 2, 1, 'rendimiento_media', '0')]
    for k, (col, titulo, lo, hi, paso, media, fmt) in enumerate(paneles):
        x0 = 1.7 + k * 8.2
        cd = XyChartData()
        for j, (tipo, _) in enumerate(TRAY):
            m = se.enso_trayectoria.values == tipo; v = se[col].values[m]
            sr = cd.add_series(tipo); off = np.zeros(m.sum()); off[np.argsort(v)] = (np.arange(m.sum()) % 5 - 2) * 0.07
            for yy, o in zip(v, off): sr.add_data_point(j + 1 + float(o), float(yy))
        for j, (tipo, _) in enumerate(TRAY):
            mu = float(t.loc[tipo, media]); sr = cd.add_series('media ' + tipo)
            sr.add_data_point(j + 1 - 0.3, mu); sr.add_data_point(j + 1 + 0.3, mu)
        gf = s.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS, Inches(x0), Inches(3.35), Inches(7.9), Inches(5.0), cd)
        ch = gf.chart; ch.has_legend = False
        estilo_ejes(ch, 0.4, 4.6, lo, hi, 1, paso, xfmt=';;;', yfmt=fmt)
        for j, (tipo, c) in enumerate(TRAY):
            puntos(ch.series[j], c, 11); recta(ch.series[j + 4], TXT, 3)
        caja(s, x0 + 0.2, 2.9, 7.5, 0.4, [[(titulo, SANSB, 17, TXT)]])
        for j, (tipo, c) in enumerate(TRAY):
            caja(s, x0 + 0.45 + j * 1.8, 8.35, 1.8, 0.6, [[(tipo, SANSB, 13, c if c != '64748B' else TXT2)], [(f'{int(t.loc[tipo, "anios"])} años', SANS, 12, SRC)]], align=PP_ALIGN.CENTER)
    f = t.loc['Niño→Niña']; g = t.loc['Niño en verano']
    caja(s, 1.98, 9.15, 16, 0.85, [[('Niño → Niña: ', SANSB, 16, 'F59E0B'), (f'{"+" if f.FIL_edd29_anomalia > 0 else ""}{num(f.FIL_edd29_anomalia, 0)} °C·día y {num(f.rendimiento_media)} t/ha.   ', SANS, 16, TXT),
                                    ('Niño en verano: ', SANSB, 16, CALOR), (f'{num(g.FIL_edd29_anomalia, 0)} °C·día y +{num(g.rendimiento_media)} t/ha.   ', SANS, 16, TXT)],
                                   [('La dirección es la esperada, pero con 6 años no alcanza ', SANS, 15, TXT2),
                                    (f'(p = {num(f.p_mw_FIL_edd29)} y {num(f.p_mw_rendimiento)}). Con 1950–2024 habría 11 veranos de transición para el tramo del clima.', SANS, 15, TXT2)]])
    return s


# ---------- 3: eventos por tipo ----------
def s_enso(prs, x, res, tag):
    se = x['serie']; comp = x['enso_por_tipo'].set_index('tipo')
    tipos = [('El Niño', MAG), ('Neutro', '64748B'), ('La Niña', CIAN)]
    s = nueva(prs, 'Contar cosechas por tipo de año',
              'Cada punto es una cosecha, clasificada por el ONI de julio (floración). Rendimiento sin tendencia, en t/ha.',
              FUENTE.format(tag),
              'Clasificación: El Niño si ONI de julio (MJJ… valor de julio en CPC v6) ≥ 0,5; La Niña si ≤ −0,5; resto neutro. Julio = floración del maíz en el píxel.\n'
              f'El Niño ({comp.loc["El Niño", "anios"]}): {comp.loc["El Niño", "lista"]}.\n'
              f'La Niña ({comp.loc["La Niña", "anios"]}): {comp.loc["La Niña", "lista"]}.\n'
              f'Neutro ({comp.loc["Neutro", "anios"]}): {comp.loc["Neutro", "lista"]}.\n'
              f'Prueba de Kruskal-Wallis entre los tres grupos: p = {res["kruskal_enso_julio_p"]:.2f}. Con 6 y 7 años por grupo, la diferencia de medias cabe en el azar.\n'
              'La dirección (El Niño algo mejor, La Niña algo peor para el maíz de EE. UU.) es la que reporta la literatura (p. ej., Iizumi et al. 2014, Nature Communications); CITA POR VERIFICAR antes de usarla.\n'
              'Lo siguiente: contar eventos con duración e intensidad sobre la serie diaria (requiere earthengine authenticate).')
    cd = XyChartData(); y = se.rendimiento_sin_tendencia_t_ha.values; anios = se.anio.values
    for k, (t, _) in enumerate(tipos):
        m = se.enso_julio.values == t
        serie = cd.add_series(t)
        orden = np.argsort(y[m]); off = np.zeros(m.sum())
        off[orden] = (np.arange(m.sum()) % 5 - 2) * 0.07
        for yy, o in zip(y[m], off): serie.add_data_point(k + 1 + float(o), float(yy))
    for k, (t, _) in enumerate(tipos):
        mu = float(comp.loc[t, 'rendimiento_media']); m = cd.add_series(f'media {t}')
        m.add_data_point(k + 1 - 0.32, mu); m.add_data_point(k + 1 + 0.32, mu)
    gf = s.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS, Inches(1.7), Inches(2.95), Inches(9.6), Inches(6.6), cd)
    ch = gf.chart; ch.has_legend = False
    estilo_ejes(ch, 0.4, 3.6, -5, 2, 1, 1, xfmt=';;;', yfmt='0')
    for k, (t, col) in enumerate(tipos):
        puntos(ch.series[k], col, 13)
        recta(ch.series[k + 3], TXT, 3)
    neutros = list(se[se.enso_julio == 'Neutro'].anio)
    if 2012 in neutros: etiqueta(ch.series[1], neutros.index(2012), '2012', MAG)
    for k, (t, col) in enumerate(tipos):
        caja(s, 1.7 + 0.75 + k * 2.85, 9.25, 2.6, 0.4, [[(t, SANSB, 16, col if col != '64748B' else TXT2)]], align=PP_ALIGN.CENTER)
    # tabla a la derecha
    xr = 12.0
    caja(s, xr, 3.1, 6.0, 0.4, [[('', SANSB, 14, SRC)]])
    hdr = [(xr, 2.0, 'Tipo'), (xr + 2.0, 1.1, 'Años'), (xr + 3.1, 1.5, 'Media t/ha'), (xr + 4.6, 1.45, 'Caída > 1 t')]
    for xx, ww, t in hdr: caja(s, xx, 3.1, ww, 0.4, [[(t, SANSB, 14, SRC)]], align=PP_ALIGN.LEFT if t == 'Tipo' else PP_ALIGN.RIGHT)
    for k, (t, col) in enumerate(tipos):
        yy = 3.65 + k * 0.85; f = comp.loc[t]
        perd = int(round(f.pct_anios_perdida_1t * f.anios / 100))
        caja(s, xr, yy, 2.0, 0.6, [[(t, SANSB, 17, col if col != '64748B' else TXT2)]], anchor=MSO_ANCHOR.MIDDLE)
        caja(s, xr + 2.0, yy, 1.1, 0.6, [[(str(int(f.anios)), SANS, 17, TXT)]], align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
        caja(s, xr + 3.1, yy, 1.5, 0.6, [[(('+' if f.rendimiento_media > 0 else '') + num(f.rendimiento_media), SERIF, 20, TXT)]], align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
        caja(s, xr + 4.6, yy, 1.45, 0.6, [[(str(perd), SERIF, 20, TXT)]], align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
        rect(s, xr, yy + 0.72, 6.05, 0.01, LINE)
    caja(s, xr, 6.35, 6.0, 3.2, [
        [('La peor cosecha, 2012, fue un año neutro: ', SANSB, 16, TXT), ('la sequía y el calor no vinieron del ENSO.', SANS, 16, TXT2)],
        [('', SANS, 8, TXT2)],
        [('El orden es el esperado ', SANSB, 16, TXT), ('(El Niño arriba, La Niña abajo), ', SANS, 16, TXT2),
         (f'pero con 6 y 7 años no se distingue del azar (p = {num(res["kruskal_enso_julio_p"])}).', SANS, 16, TXT2)]])
    return s


# ---------- eventos por gravedad (Li et al. 2025b, Tabla 2) ----------
GRADOS = [('bajo_leve', 'Menor que leve', 0.15), ('leve', 'Leve', 0.35), ('moderado', 'Moderado', 0.6), ('severo', 'Severo', 0.9)]
# Tabla 2 de Li et al. (2025b): leve, moderado y severo desde esos días; etapas de la fuente que usa cada fase
LI_DIAS = {'VE–V6': (3.7, 5.9, 8.6), 'V6–VT': (3.5, 5.4, 7.5), 'R1–R3': (2.8, 4.7, 8.3), 'R3–R6': (3.2, 5.3, 8.1)}
ETAPAS_FASE = dict(VEG=['VE–V6', 'V6–VT'], FLO=['R1–R3'], REP=['R1–R3'], FIL=['R3–R6'])
UMBRAL_TXT = dict(VEG='Tmax ≥ 34,1 / 34,6 °C', FLO='Tmax ≥ 33,7 °C', REP='Tmax ≥ 33,7 °C', FIL='Tmax ≥ 32,9 °C')


def dias_grado(etapa):
    """Días enteros que caen en cada grado (las rachas duran días completos, desde 2)."""
    lv, md, sv = (math.ceil(v) for v in LI_DIAS[etapa])
    r = lambda a, b: f'{a} d' if a == b else f'{a}–{b} d'
    return [r(2, lv - 1) if lv > 2 else '—', r(lv, md - 1), r(md, sv - 1), f'≥ {sv} d']


def rango_fase(f, j):
    vals = list(dict.fromkeys(dias_grado(e)[j] for e in ETAPAS_FASE[f]))
    return ' / '.join(v.replace(' d', '') for v in vals[:-1]) + (' / ' if len(vals) > 1 else '') + vals[-1]


FASES6 = ['EST', 'VEG', 'FLO', 'REP', 'FIL', 'MAT']
CAL_IDS = ['MAI-EST-CAL', 'MAI-VEG1-CAL', 'MAI-VEG2-CAL', 'MAI-FLO-CAL', 'MAI-REP-CAL', 'MAI-FIL-CAL']
SEQ_IDS = ['MAI-EST-SEQ', 'MAI-VEG-SEQ', 'MAI-FLO-SEQ', 'MAI-FIL-SEQ']
FILAS_EV = [  # (amenaza, regla, color, ids, tipo, fases con regla)
    ('Calor', 'Tmax ≥ umbral de la fase, ≥ 2 d', CALOR, CAL_IDS, 'racha', FASES6[:5]),
    ('Calor sobre 29 °C', 'Tmax > 29 °C, ≥ 2 d', CALOR, ['MAI-RACHA-29'], 'racha', FASES6),
    ('Racha seca', 'P < 1 mm, ≥ 2 d', CIAN, ['MAI-RACHA-SECA'], 'racha', FASES6),
    ('Lluvia', 'P > 10 mm, cada día', CIAN, ['MAI-MAT-LLU'], 'dia', ['MAT']),
    ('Sequía', 'P − ETP < Q1, sí o no', CIAN, SEQ_IDS, 'ventana', ['EST', 'VEG', 'FLO', 'FIL']),
    ('Seco-cálido', 'P < p20 y T > p80, sí o no', CALOR, ['MAI-TARDIA-SECA-CALIDA'], 'ventana', ['FLO', 'REP', 'FIL'])]


def s_eventos(prs, conteo):
    """Cuántos eventos de cada amenaza de maíz hay por fase y cuánto duran (pixel_tipico_conteo_reglas.py). Sin rendimiento."""
    ev = pd.read_csv(conteo / 'eventos.csv'); ra = pd.read_csv(conteo / 'regla_anio.csv')
    ev = ev[ev.anio.between(1981, 2016)]; ra = ra[ra.anio.between(1981, 2016) & (ra.cultivo == 'maize')]
    n_anios = ra.anio.nunique()

    def dias_fase(sub):
        d = dict.fromkeys(FASES6, 0)
        for o in sub.itertuples():
            for f, k in zip(o.fases.split(' → '), str(o.dias_por_fase).split(' + ')): d[f] += int(k)
        return d
    cal = ev[ev.id.isin(CAL_IDS)]
    grados = cal.grado.value_counts()
    ej = cal[(cal.anio == 1987) & cal.cruza_borde].iloc[0]
    s = nueva(prs, 'Cuántos eventos y cuánto duran',
              'Cada amenaza se cuenta por separado. Arriba, eventos en 36 años; abajo, días en evento por año en esa fase.',
              f'Fuente: pixel_tipico/{conteo.name} (eventos.csv, regla_anio.csv), reglas_vigentes.csv · píxel 191325, maíz, 1981–2016.',
              'Evento del píxel: en cada una de las 25 celdas de ERA5-Land se marcan los días que forman racha según la regla de la amenaza; '
              'el píxel está en evento el día en que al menos la mitad de las celdas (ponderadas por cos(lat)) lo está. Cada amenaza se cuenta '
              'por separado: un mismo día puede estar en un evento de calor y en uno de racha seca. Un evento que pasa de una fase a otra se '
              'cuenta una sola vez, en la fase donde tiene más días, y sus días se reparten entre las fases (no se duplica ningún día). '
              'Calor: Tmax ≥ 34,0 / 34,1 / 34,6 / 33,7 / 33,7 / 32,9 °C de EST a FIL (Li et al., 2025a); grado por la duración completa con la '
              'Tabla 2 de Li et al. (2025b) en días enteros. Lluvia en MAT: cada día con P > 10 mm es un evento. Sequía y seco-cálido son '
              'condiciones de ventana: se cuentan años (sí o no por temporada); la sequía sale en 25 % de los años por construcción (primer cuartil). '
              'EDD29 no es evento (°C·día) y no está en la tabla. Verificación: el calor da las mismas 65 que la versión anterior, con las mismas '
              'fechas, grados y días por fase.')
    x0, y0, wl, wc, wx, hf = 1.98, 2.95, 3.55, 1.72, 1.85, 0.74
    caja(s, x0, y0, wl, 0.42, [[('Amenaza · regla', SANSB, 13, SRC)]], anchor=MSO_ANCHOR.MIDDLE)
    for k, f in enumerate(FASES6):
        x = x0 + wl + k * wc
        rect(s, x, y0, wc - 0.06, 0.42, FASE_COLOR[f])
        caja(s, x, y0, wc - 0.06, 0.42, [[('REP-pos' if f == 'REP' else f, SANSB, 13, BG)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    xx = x0 + wl + 6 * wc + 0.05
    rect(s, xx, y0, wx, 0.42, '3A3410')
    caja(s, xx, y0, wx, 0.42, [[('Pasan de fase', SANSB, 13, TXT)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    for r, (nom, regla, color, ids, tipo, fases) in enumerate(FILAS_EV):
        y = y0 + 0.52 + r * (hf + 0.06)
        rect(s, x0, y, 0.1, hf, color)
        caja(s, x0 + 0.2, y, wl - 0.25, hf, [[(nom, SANSB, 15, TXT)], [(regla, SANS, 11, SRC)]], anchor=MSO_ANCHOR.MIDDLE)
        if tipo == 'ventana':
            sub = ra[ra.id.isin(ids)]
            por_fase = ({f.split(' ')[0]: int(g.hubo.sum()) for f, g in sub.groupby('fase')} if len(ids) > 1
                        else {'FLO': int(sub.hubo.sum())})
        else:
            sub = ev[ev.id.isin(ids)]
            n = sub.groupby('fase').size() if tipo == 'racha' else sub.groupby('fase').dias.sum()
            dias = dias_fase(sub)
        for k, f in enumerate(FASES6):
            x = x0 + wl + k * wc
            if nom == 'Seco-cálido' and f in ('REP', 'FIL'): continue
            ancho = (3 * wc if nom == 'Seco-cálido' and f == 'FLO' else wc) - 0.06
            if f not in fases:
                rect(s, x, y, ancho, hf, '0B1328')
                caja(s, x, y, ancho, hf, [[('—', SANS, 14, '475569')]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
                continue
            rect(s, x, y, ancho, hf, PANEL)
            if tipo == 'ventana':
                v = por_fase.get(f, 0)
                lineas = [[(str(v), SERIF, 20, TXT)], [(f'años de {n_anios}' + (' · FLO–FIL' if nom == 'Seco-cálido' else ''), SANS, 10.5, TXT2)]]
            else:
                v = int(n.get(f, 0)); d = dias[f] / n_anios
                lineas = [[(str(v), SERIF, 20, TXT if v else SRC)], [(f'{num(d, 1)} d/año', SANS, 10.5, TXT2)]]
            caja(s, x, y, ancho, hf, lineas, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        rect(s, xx, y, wx, hf, PANEL)
        cr = '—' if tipo == 'ventana' else str(int(ev[ev.id.isin(ids)].cruza_borde.sum()))
        caja(s, xx, y, wx, hf, [[(cr, SERIF if cr != '—' else SANS, 20 if cr != '—' else 14, AMARILLO if cr not in ('—', '0') else SRC)]],
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    yg = y0 + 0.52 + len(FILAS_EV) * (hf + 0.06) + 0.02
    caja(s, x0, yg, 16.04, 0.35, [[('Calor por grado ', SANSB, 12.5, TXT2), ('(Li et al., 2025b, por la duración completa): ', SANS, 12.5, SRC)] +
                                   [(f'{nom_g.lower()} {int(grados.get(g, 0))}' + ('  ·  ' if k < 3 else ''), SANS, 12.5, TXT2)
                                    for k, (g, nom_g, _) in enumerate(GRADOS)]])
    pasos = [('1', 'Contar', 'En cada celda y día se revisa la regla de la amenaza. 2 o más días seguidos son racha. Si la mitad del '
                             'píxel está en racha, ese día hay evento.'),
             ('2', 'Asignar fase', f'El evento se cuenta una vez, en la fase con más días; sus días se reparten. Ej.: 1987, '
                                   f'{ej.dias_por_fase.replace(" + ", " d en REP-pos + ")} d en FIL → un evento de FIL.'),
             ('3', 'Clasificar', 'Calor: grado por la duración completa. Sequía y seco-cálido: sí o no por temporada.')]
    for k, (nn, cab_, txt) in enumerate(pasos):
        xk, yk = x0 + k * 5.4, 8.8
        rect(s, xk, yk, 5.2, 1.15, PANEL)
        caja(s, xk + 0.15, yk + 0.08, 0.5, 0.6, [[(nn, SERIF, 28, CIAN)]])
        caja(s, xk + 0.7, yk + 0.08, 4.35, 1.02, [[(cab_, SANSB, 14, TXT)], [(txt, SANS, 12, TXT2)]])
    return s


def s_olas(prs, olas, x):
    """Olas de calor de toda la temporada, año por año (pixel_tipico_rachas_temporada.py)."""
    ol = pd.read_csv(olas / 'rachas.csv'); dd = pd.read_csv(olas / 'dias.csv')
    y = x['serie'].set_index('anio').rendimiento_sin_tendencia_t_ha
    lim = dd[dd.anio == dd.anio.min()].groupby('fase').agg(i=('dia_ciclo', 'min'), f=('dia_ciclo', 'max'))
    d0, d1 = int(lim.loc['VEG', 'i']), int(lim.loc['FIL', 'f']) + 1
    cruzan = ol[ol.cruza_borde]; dos = cruzan[cruzan.pedazos_v3 > 1]; corta = cruzan[cruzan.dias_fuera_v3 > 0]
    s = nueva(prs, 'Los eventos de calor, año por año',
              'Cada fila es un año y cada barra un evento de calor. Así se ve cuáles quedan dentro de una fase y cuáles pasan a la siguiente.',
              f'Fuente: pixel_tipico/{olas.name}/rachas.csv (umbrales de reglas v3 por subfase, sin cortar en el borde de la fase) · '
              'rendimiento GDHY sin tendencia.',
              'Cómo explicarla: cada fila es una temporada (1981 arriba, 2016 abajo); el eje horizontal va del 6 de mayo al 5 de septiembre '
              'con las fases arriba. Cada barra es un evento: empieza el primer día en que la mitad del píxel está en racha de calor y termina '
              'el último. El color es el grado por la duración completa (Li et al., 2025b). Borde amarillo: el evento pasa de una fase a otra; '
              'se cuenta una sola vez, en la fase donde tiene más días. A la derecha, el rendimiento sin tendencia de ese año. '
              f'{len(ol)} eventos en 36 años; {len(cruzan)} pasan de fase y sus días se reparten entre las fases. Lo que sale de aquí para el análisis, por fase y año: número de '
              'eventos, días en evento, evento más largo y grado mayor. Antes (reglas por fase) la racha se cortaba en el borde: '
              f'{len(dos)} eventos se contaban dos veces ({", ".join(map(str, dos.anio))}); ya no.')
    xl, xg0, xg1, xy, yt, yb = 1.98, 2.75, 12.35, 12.5, 3.25, 9.75
    esc = (xg1 - xg0) / (d1 - d0); h = (yb - yt) / 36

    def xd(d): return xg0 + (d - d0) * esc
    for f in ['VEG', 'FLO', 'REP', 'FIL']:
        a, b = int(lim.loc[f, 'i']), int(lim.loc[f, 'f']) + 1
        rect(s, xd(a) + 0.02, yt - 0.42, (b - a) * esc - 0.04, 0.07, FASE_COLOR[f])
        caja(s, xd(a), yt - 0.34, (b - a) * esc, 0.3, [[('REP-pos' if f == 'REP' else f, SANSB, 12, TXT)]], align=PP_ALIGN.CENTER)
        if f != 'VEG': rect(s, xd(a) - 0.005, yt - 0.05, 0.01, yb - yt + 0.05, '1E293B')
    for fecha, d in [('6 may', d0), ('9 jul', int(lim.loc['FLO', 'i'])), ('28 jul', int(lim.loc['FIL', 'i'])), ('5 sep', d1)]:
        caja(s, xd(d) - 0.5, yb + 0.03, 1.0, 0.25, [[(fecha, SANS, 10.5, SRC)]], align=PP_ALIGN.CENTER)
    caja(s, xy - 0.1, yt - 0.42, 1.0, 0.4, [[('Rend.', SANSB, 11, SRC)], [('t/ha', SANS, 10, SRC)]], align=PP_ALIGN.CENTER)
    alfa = {'bajo_leve': 0.25, 'leve': 0.5, 'moderado': 0.75, 'severo': 1.0}  # más contraste que la tabla: barras delgadas
    for k, anio in enumerate(range(1981, 2017)):
        yy = yt + k * h
        if k % 2 == 0: rect(s, xg0, yy, xg1 - xg0, h, '08122A')
        caja(s, xl, yy, 0.65, h, [[(str(anio), SANS, 9.5, SRC)]], anchor=MSO_ANCHOR.MIDDLE)
        r = float(y.loc[anio])
        caja(s, xy, yy, 0.8, h, [[(num(r, 1), SANSB if r <= -1 else SANS, 9.5, TXT if r <= -1 else SRC)]], align=PP_ALIGN.CENTER,
             anchor=MSO_ANCHOR.MIDDLE)
        for o in ol[ol.anio == anio].itertuples():
            b = rect(s, xd(o.dia_ini), yy + 0.03, max(o.dias * esc - 0.02, 0.05), h - 0.06,
                     mezcla(CALOR, alfa[o.grado_completa]), linea=AMARILLO if o.cruza_borde else None)
            if o.cruza_borde: b.line.width = Pt(1.75)
    xp, wp = 13.6, 4.4
    rect(s, xp, yt - 0.42, wp, yb - yt + 0.42, PANEL)
    def fase_mayor(o):
        fs, ds = o.fases.split(' → '), [int(v) for v in str(o.dias_por_fase).split(' + ')]
        return fs[ds.index(max(ds))]
    def tramo(o):
        fs, ds = o.fases.replace('REP', 'REP-pos').split(' → '), str(o.dias_por_fase).split(' + ')
        return ' + '.join(f'{d} d {f}' for d, f in zip(ds, fs)) + f' → {fase_mayor(o).replace("REP", "REP-pos")}'
    caja(s, xp + 0.3, yt - 0.25, wp - 0.6, 6.5, [
        [('Cómo leerla', SANSB, 15, TXT)],
        [('Fila = un año. Barra = un evento de calor, de su primer a su último día. Color = grado por la duración completa.', SANS, 12.5, TXT2)],
        [('', SANS, 6, TXT)],
        [(f'{len(cruzan)} de {len(ol)}', SERIF, 28, AMARILLO)],
        [('eventos pasan de una fase a otra (borde amarillo)', SANSB, 13, TXT)],
        [('Se cuentan una vez, en la fase con más días; sus días se reparten:', SANS, 12.5, TXT2)],
        *[[(f'{o.anio}   ', SANSB, 11.5, TXT), (tramo(o), SANS, 11.5, TXT2)] for o in cruzan.itertuples()],
        [('', SANS, 6, TXT)],
        [('Lo que sale de aquí, por fase y año', SANSB, 13, TXT)],
        [('eventos · días en evento · evento más largo · grado mayor', SANS, 12.5, CIAN)],
    ])
    caja(s, xp + 0.3, 7.85, 3.0, 0.3, [[('Leyenda', SANSB, 12, SRC)]])
    for j, (g, nom, a) in enumerate(GRADOS):
        yy = 8.2 + j * 0.3
        rect(s, xp + 0.3, yy + 0.06, 0.5, 0.16, mezcla(CALOR, alfa[g]))
        caja(s, xp + 0.95, yy, 1.6, 0.28, [[(nom, SANS, 11.5, TXT2)]], anchor=MSO_ANCHOR.MIDDLE)
    r_ = rect(s, xp + 2.6, 8.26, 0.5, 0.16, None, linea=AMARILLO); r_.line.width = Pt(1.75)
    caja(s, xp + 3.2, 8.2, 1.1, 0.28, [[('cruza borde', SANS, 11.5, TXT2)]], anchor=MSO_ANCHOR.MIDDLE)
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--corr', required=True)
    ap.add_argument('--reglas', help='carpeta conteo_reglas_<fecha> (pixel_tipico_conteo_reglas.py); agrega la diapositiva de eventos por amenaza y fase')
    ap.add_argument('--olas', help='carpeta rachas_temporada_<fecha> (pixel_tipico_rachas_temporada.py); agrega la de olas')
    ap.add_argument('--entrada', default=str(PPT))
    ap.add_argument('--salida', default=str(PPT))
    a = ap.parse_args()
    carpeta = Path(a.corr); tag = carpeta.name.replace('correlaciones_', '')
    x = pd.read_excel(carpeta / 'correlaciones.xlsx', sheet_name=None)
    res = json.loads((carpeta / 'resumen.json').read_text(encoding='utf-8'))
    prs = Presentation(a.entrada)
    lst = prs.slides._sldIdLst
    for e in list(lst):
        if any(sh.name == 'PX_numero' for sh in prs.slides.part.related_part(e.rId).slide.shapes):
            prs.part.drop_rel(e.rId); lst.remove(e)
    # sin esto, add_slide reutiliza nombres slideN.xml que aún existen y el archivo queda con partes duplicadas
    prs.part.rename_slide_parts([e.rId for e in lst])
    # Orden del 3 nov 2026: amenazas del píxel → eventos → tendencia → amenaza-cosecha → el mar → ONI, contexto y transición.
    # versión resumida (2 nov 2026): s_fase, s_cadena y s_enso quedan disponibles pero no se insertan
    bloques = [('¿Y el clima? También puede tener tendencia', [s_clima(prs, x, tag)]),
               ('El mar y el rendimiento', [s_oni(prs, x, tag), s_contexto(prs, tag), s_trayectoria(prs, x, res, tag)])]
    if a.reglas:
        bloques.insert(0, ('El sustento de los umbrales de maíz', [s_eventos(prs, Path(a.reglas))] +
                           ([s_olas(prs, Path(a.olas), x)] if a.olas else [])))
    for titulo, nuevas in bloques:
        pos = [k for k, s in enumerate(prs.slides) if s is por_titulo(prs, titulo)][0] + 1
        for k, s in enumerate(nuevas): mover(prs, s, pos + k)
        print(f'después de «{titulo}»:', len(nuevas))
    renumerar(prs)
    prs.save(a.salida); print('guardado', a.salida, len(prs.slides), 'diapositivas')


if __name__ == '__main__':
    main()


# ---------- mala cosecha ----------
def s_mala(prs, carpeta, pixel=191325):
    """Qué es una mala cosecha en el píxel: anomalía robusta (malas_cosechas_pixeles.py)."""
    a = pd.read_csv(carpeta / 'anual_maize.csv.gz')
    a = a[a.pixel_id == pixel].set_index('anio')
    rel = a.perdida_relativa_pct
    med = float(rel.median()); mad = 1.4826 * float((rel - med).abs().median())
    corte = med - mad
    z_sd = (rel - rel.mean()) / rel.std()
    malas = a[a.mala_cosecha == 1].index.tolist()
    con_sd = rel[(z_sd <= -1) & (rel <= -5)].index.tolist()
    res = pd.read_excel(carpeta / 'malas_cosechas.xlsx', sheet_name='resumen').set_index('cultivo')
    s = nueva(prs, 'Qué es una mala cosecha',
              'En cada píxel: perder bastante más de lo que ese píxel suele variar, y al menos 5 % de lo esperado.',
              f'Fuente: rendimiento/{carpeta.name} (malas_cosechas_pixeles.py) · GDHY 1981–2016, píxel {pixel} · '
              'Leys et al. (2013), J. Exp. Soc. Psychol. 49:764 · Utku et al. (2026), Sci. Rep. 16:25339 · GEOGLAM Crop Monitor.',
              'Primer intento: llamar mala cosecha a toda pérdida de 5 % frente a la tendencia. En Nebraska daba 9 años, pero en los '
              'píxeles variables marcaba un tercio de los años o más: una baja de 5 % es variación normal donde el rendimiento sube y '
              'baja ±18 %. Por eso cada píxel se mide con su propia vara. La anomalía relativa es rendimiento ÷ tendencia − 1; se '
              'estandariza con la mediana y la MAD (por 1,4826, comparable a la desviación típica; Leys et al. 2013, p. 2–3), que no '
              f'se dejan arrastrar por un año extremo. Con la desviación típica, 2012 agranda la vara y quedan solo {len(con_sd)} años '
              f'({", ".join(map(str, con_sd))}). El corte z ≤ −1 viene de Utku et al. (2026), que definen un choque negativo de '
              'rendimiento como Z < −1 y prueban −0,5 y −1,5. El 5 % (clase «Poor» de GEOGLAM) evita que en un píxel muy estable entre '
              'un año sin pérdida real. Ningún artículo combina las tres piezas: la combinación es nuestra y se declara así.')
    x0, x1, yt, yb = 2.35, 11.6, 3.15, 8.55
    vmin, vmax = -45.0, 20.0

    def yv(v): return yt + (vmax - v) / (vmax - vmin) * (yb - yt)
    for v in (-40, -30, -20, -10, 0, 10, 20):
        rect(s, x0, yv(v) - 0.004, x1 - x0, 0.008, '1E293B' if v else '475569')
        caja(s, x0 - 0.75, yv(v) - 0.13, 0.6, 0.26, [[(f'{v:+d} %' if v else '0', SANS, 10.5, SRC)]], align=PP_ALIGN.RIGHT)
    w = (x1 - x0) / 36
    for k, anio in enumerate(range(1981, 2017)):
        v = float(rel.loc[anio]); xx = x0 + k * w
        top, bot = (yv(v), yv(0)) if v >= 0 else (yv(0), yv(v))
        rect(s, xx + 0.04, top, w - 0.08, max(bot - top, 0.01), AMARILLO if anio in malas else '334155')
        if anio in malas:
            caja(s, xx - 0.3, yv(v) + 0.05, w + 0.6, 0.25, [[(str(anio), SANSB, 10.5, AMARILLO)]], align=PP_ALIGN.CENTER)
        if anio % 5 == 0:
            caja(s, xx - 0.3, yb + 0.06, w + 0.6, 0.25, [[(str(anio), SANS, 10, SRC)]], align=PP_ALIGN.CENTER)
    for v, col, txt in ((corte, MAG, f'z = −1  ({num(corte, 1)} %)'), (-5, CIAN, '−5 %')):
        rect(s, x0, yv(v) - 0.012, x1 - x0, 0.024, col)
        caja(s, x1 + 0.08, yv(v) - 0.14, 1.6, 0.28, [[(txt, SANSB, 11, col)]])
    caja(s, x0, yb + 0.38, x1 - x0, 0.3, [[('Pérdida o ganancia frente a la tendencia del píxel, por cosecha. ', SANS, 12, SRC),
                                            ('Amarillo: mala cosecha.', SANSB, 12, AMARILLO)]])

    xp, wp = 13.55, 4.5
    rect(s, xp, yt - 0.1, wp, 4.75, PANEL)
    caja(s, xp + 0.3, yt + 0.1, wp - 0.6, 5.6, [
        [(f'{len(malas)} de 36', SERIF, 30, AMARILLO)], [('cosechas malas en Nebraska', SANSB, 14, TXT)], [('', SANS, 8, TXT)],
        [('1 · Anomalía', SANSB, 13, TXT)], [('rendimiento ÷ tendencia − 1', SANS, 12.5, TXT2)], [('', SANS, 6, TXT)],
        [('2 · La vara del píxel', SANSB, 13, TXT)],
        [('z = (anomalía − mediana) ÷ (1,4826 × MAD). Mediana y MAD no se dejan arrastrar por 2012 (Leys et al., 2013).', SANS, 12.5, TXT2)],
        [('', SANS, 6, TXT)],
        [('3 · Mala cosecha', SANSB, 13, TXT)],
        [('z ≤ −1 (Utku et al., 2026) y pérdida de al menos 5 % (GEOGLAM).', SANS, 12.5, TXT2)], [('', SANS, 6, TXT)],
        [(f'Con la desviación típica quedarían {len(con_sd)}: 2012 agranda la vara.', SANS, 12, SRC)],
    ])
    m = {c: int(res.loc[c, 'mediana_malas']) for c in ('Maíz', 'Arroz', 'Trigo', 'Soya')}
    caja(s, x0 - 0.37, 9.4, 16.0, 0.5, [[('En todos los píxeles: ', SANSB, 14, TXT),
                                          ('mediana de ' + ', '.join(f'{v} en {k.lower()}' for k, v in m.items()) +
                                           ' malas cosechas en 36 años. El número sale de cada píxel, no de un percentil fijo.', SANS, 14, TXT2)]])
    return s


# ---------- paso 1: amenaza con rendimiento ----------
FILAS_P1 = [('Calor', 'días en evento', CALOR), ('Calor sobre 29 °C', 'días en evento', CALOR), ('Racha seca', 'días en evento', CIAN),
            ('Lluvia', 'días en evento', CIAN), ('Sequía', 'déficit P − ETP', CIAN), ('Seco-cálido', 'sí o no, FLO–FIL', CALOR),
            ('EDD29', '°C·día, no es evento', CALOR)]
AZUL = '60A5FA'


def s_paso1(prs, paso1):
    """Paso 1: qué amenaza, en qué fase, acompaña las pérdidas (pixel_tipico_paso1.py)."""
    c = pd.read_excel(paso1 / 'paso1.xlsx', sheet_name='celdas')
    res = json.loads((paso1 / 'resumen.json').read_text(encoding='utf-8'))
    fuertes = c[c.q_bh < .05]
    s = nueva(prs, 'Qué amenaza acompaña las pérdidas',
              'Paso 1. Cada amenaza, fase por fase, frente a la pérdida del año. Ambos sin tendencia; 36 cosechas.',
              f'Fuente: pixel_tipico/{paso1.name}/paso1.xlsx · eventos de conteo_reglas_20261105_150123 · pérdida relativa de '
              'malas_cosechas_20261104_213842 · píxel 191325.',
              'Qué se compara: por amenaza y fase, una variable por año en la que más amenaza = valor mayor (días en evento; en sequía, '
              'déficit = −Σ(P − ETP); en seco-cálido, 1 o 0; EDD29 en °C·día), frente a la pérdida relativa del año (rendimiento / '
              'tendencia − 1, la misma de la mala cosecha). La amenaza se deja sin tendencia con una recta 1981–2016. ρ de Spearman: '
              'negativa = más amenaza, menos cosecha. Para qué: es el filtro; solo lo que acompaña las pérdidas pasa al paso 2 (ONI). '
              f'{res["pruebas"]} pruebas; {res["p05"]} con p < 0,05 (por azar ~{num(res["esperado_azar"], 1)}); {res["q05"]} se sostienen con la '
              'corrección de Benjamini–Hochberg (q < 0,05, borde amarillo). «Malas» = de las 5 malas cosechas (1983, 1988, 1991, 1995, 2012), '
              'cuántas tuvieron la amenaza en esa fase. Racha seca y calor sobre 29 °C ocurren todos los años: ahí cuenta cuántos días, no si hubo. '
              'En EST la relación es positiva: más días secos al establecer acompañan mejores cosechas.')
    x0, y0, wl, wc, hf = 1.98, 2.95, 3.15, 1.6, 0.72
    for k, f in enumerate(FASES6):
        x = x0 + wl + k * wc
        rect(s, x, y0, wc - 0.06, 0.4, FASE_COLOR[f])
        caja(s, x, y0, wc - 0.06, 0.4, [[('REP-pos' if f == 'REP' else f, SANSB, 13, BG)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    for r, (nom, var, color) in enumerate(FILAS_P1):
        y = y0 + 0.48 + r * (hf + 0.06)
        rect(s, x0, y, 0.1, hf, color)
        caja(s, x0 + 0.2, y, wl - 0.25, hf, [[(nom, SANSB, 14, TXT)], [(var, SANS, 10.5, SRC)]], anchor=MSO_ANCHOR.MIDDLE)
        for k, f in enumerate(FASES6):
            x = x0 + wl + k * wc
            fila = c[(c.amenaza == nom) & (c.fase == f)]
            if fila.empty or pd.isna(fila.rho.iloc[0]):
                rect(s, x, y, wc - 0.06, hf, '0B1328')
                caja(s, x, y, wc - 0.06, hf, [[('sin eventos' if not fila.empty else '—', SANS, 10.5, '475569')]],
                     align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
                continue
            o = fila.iloc[0]
            a = min(abs(o.rho) / 0.65, 1) * 0.85
            caja_r = rect(s, x, y, wc - 0.06, hf, mezcla(CALOR if o.rho < 0 else AZUL, a) if o.p < .05 else PANEL,
                          linea=AMARILLO if o.q_bh < .05 else None)
            if o.q_bh < .05: caja_r.line.width = Pt(2)
            abajo = f'malas {int(o.malas_con_amenaza)}/{int(o.malas)}' if pd.notna(o.malas_con_amenaza) else f'sin 2012: {num(o.rho_sin_2012, 2)}'
            caja(s, x, y, wc - 0.06, hf, [[(num(o.rho, 2), SERIF if o.p < .05 else SANS, 18 if o.p < .05 else 15, TXT if o.p < .05 else SRC)],
                                          [(abajo, SANS, 10, TXT2)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    xp = x0 + wl + 6 * wc + 0.25; wp = 18.02 - xp
    rect(s, xp, y0, wp, 5.8, PANEL); rect(s, xp, y0, 0.07, 5.8, AMARILLO)
    pasan = ' · '.join(f'{o.amenaza} {("REP-pos" if o.fase == "REP" else o.fase)}' for o in fuertes.itertuples())
    caja(s, xp + 0.25, y0 + 0.15, wp - 0.4, 5.5, [
        [('Qué dice', SANSB, 15, TXT)],
        [('El llenado concentra la señal: calor, días sobre 29 °C, racha seca y EDD29 en FIL.', SANS, 12.5, TXT2)],
        [('', SANS, 6, TXT)],
        [('Las 5 malas cosechas tuvieron calor en FIL, pero también 15 años normales: cuentan los días, no el sí o no.', SANS, 12.5, TXT2)],
        [('', SANS, 6, TXT)],
        [('Pasan al paso 2 (ONI)', SANSB, 13, AMARILLO)],
        [(pasan, SANS, 12, TXT2)]])
    yl = y0 + 0.48 + len(FILAS_P1) * (hf + 0.06) + 0.02
    caja(s, x0, yl, 16.04, 0.6, [[('▌', SANSB, 13, CALOR), (' más amenaza, menos cosecha   ', SANS, 12, TXT2), ('▌', SANSB, 13, AZUL),
                                  (' más amenaza, más cosecha   ', SANS, 12, TXT2), ('▢', SANSB, 13, AMARILLO),
                                  (' se sostiene tras corregir por azar (q < 0,05)', SANS, 12, TXT2)],
                                 [(f'Color solo si p < 0,05. {res["pruebas"]} pruebas: {res["p05"]} con p < 0,05 (por azar ~{num(res["esperado_azar"], 1)}); '
                                   f'{res["q05"]} se sostienen. «malas 5/5»: cuántas de las 5 malas cosechas tuvieron la amenaza en esa fase.', SANS, 12, SRC)]])
    return s


# ---------- paso 2: ONI con amenaza ----------
CLASE_COLOR = {'Niña': '60A5FA', 'Neutro': '94A3B8', 'Niño': 'E5484D'}


def s_paso2(prs, paso2):
    """Paso 2: % de años con amenaza alta en Niña, neutro y Niño (pixel_tipico_paso2.py)."""
    r = pd.read_excel(paso2 / 'paso2.xlsx', sheet_name='resumen')
    fr = pd.read_excel(paso2 / 'paso2.xlsx', sheet_name='frecuencias')
    res = json.loads((paso2 / 'resumen.json').read_text(encoding='utf-8'))
    d = fr[fr.oni == 'durante']
    grupos = list(dict.fromkeys(zip(d.amenaza, d.fase)))
    s = nueva(prs, 'Qué hace el ENSO con esas amenazas',
              'Paso 2. Las amenazas que pasaron el paso 1, en años Niña, neutros y Niño (ONI durante la fase), 1950–2024.',
              f'Fuente: pixel_tipico/{paso2.name}/paso2.xlsx · ONI v6 del CPC (cpc_oni_v6_1950_2026.csv) · eventos de '
              'conteo_reglas_20261105_150123 · píxel 191325.',
              'Qué se compara: para cada amenaza que pasó el paso 1, cada año 1950–2024 se marca con amenaza alta si su valor sin tendencia '
              'cae en el tercio superior (por azar, 33 % de los años). Los años se clasifican por el ONI medio de los meses de la fase: '
              'Niño ≥ +0,5; Niña ≤ −0,5; neutro el resto (sin la regla de persistencia del CPC). Barras: % de años con amenaza alta en cada '
              'clase. Además, ρ de Spearman entre el ONI y la amenaza, con el ONI durante la fase y 3 meses antes de que empiece. '
              f'{res["pruebas"]} pruebas: {res["p05"]} con p < 0,05 (por azar ~{num(res["esperado_azar"], 1)}); {res["q05"]} con q < 0,05. '
              'Lectura: la dirección se repite en las amenazas del llenado (La Niña, más años de calor y sequedad; El Niño, menos), pero con un '
              'solo píxel no alcanza a separarse del azar. Hace falta el conteo global para ver si el patrón se mantiene en la región.')
    xg0, yb, yt, wgrp = 2.3, 8.15, 3.35, 2.0
    esc = (yb - yt) / 70
    rect(s, xg0 - 0.2, yb - 33.3 * esc, len(grupos) * wgrp + 0.2, 0.015, TXT2)
    caja(s, 1.55, yb - 33.3 * esc - 0.32, 0.6, 0.6, [[('azar', SANS, 10, TXT2)], [('33 %', SANS, 10, TXT2)]], align=PP_ALIGN.RIGHT)
    for g, (nom, f) in enumerate(grupos):
        xg = xg0 + g * wgrp
        for k, cl in enumerate(['Niña', 'Neutro', 'Niño']):
            o = d[(d.amenaza == nom) & (d.fase == f) & (d.clase == cl)].iloc[0]
            h = o.pct_alta * esc; x = xg + k * 0.52
            rect(s, x, yb - h, 0.46, h, CLASE_COLOR[cl])
            caja(s, x - 0.15, yb - h - 0.33, 0.76, 0.3, [[(f'{o.pct_alta:.0f}', SANSB, 11.5, TXT)]], align=PP_ALIGN.CENTER)
            caja(s, x - 0.15, yb + 0.02, 0.76, 0.25, [[(f'{int(o.anios_alta)}/{int(o.anios)}', SANS, 9.5, SRC)]], align=PP_ALIGN.CENTER)
        caja(s, xg - 0.1, yb + 0.3, 1.75, 0.6, [[(nom, SANSB, 12, TXT)], [('REP-pos' if f == 'REP' else f, SANS, 11, SRC)]], align=PP_ALIGN.CENTER)
    rect(s, xg0 - 0.2, yb, len(grupos) * wgrp + 0.2, 0.015, '475569')
    caja(s, 1.98, 2.9, 10, 0.35, [[('% de años con amenaza alta', SANSB, 12.5, SRC), ('   ', SANS, 12, SRC)] +
                                   sum(([('■', SANSB, 13, CLASE_COLOR[cl]), (f' {cl}   ', SANS, 12, TXT2)] for cl in ['Niña', 'Neutro', 'Niño']), [])])
    caja(s, 1.98, 9.25, 10.2, 0.55, [[('Debajo de cada barra: años con amenaza alta / años de esa clase. Amenaza alta = tercio superior '
                                       'de la serie sin tendencia.', SANS, 11.5, SRC)]])
    xp, wp = 12.55, 5.47
    rect(s, xp, 2.9, wp, 6.9, PANEL); rect(s, xp, 2.9, 0.07, 6.9, CIAN)
    lineas = [[('ρ de Spearman con el ONI', SANSB, 13, TXT)], [('durante la fase · 3 meses antes', SANS, 11, SRC)]]
    for nom, f in grupos:
        a_ = r[(r.amenaza == nom) & (r.fase == f) & (r.oni == 'durante')].iloc[0]; b_ = r[(r.amenaza == nom) & (r.fase == f) & (r.oni == 'antes')].iloc[0]
        lineas.append([(f'{nom} {f}: ', SANS, 11.5, TXT2), (num(a_.rho, 2) + ('*' if a_.p < .05 else ''), SANSB, 11.5, TXT),
                       ('  ·  ' + num(b_.rho, 2) + ('*' if b_.p < .05 else ''), SANS, 11.5, TXT2)])
    lineas += [[('* p < 0,05. Ninguna con q < 0,05.', SANS, 10.5, SRC)], [('', SANS, 6, TXT)],
               [('Qué dice', SANSB, 14, TXT)],
               [('Con La Niña en el verano, el llenado tiene más años de calor y sequedad; con El Niño, menos. La dirección se repite en las '
                 'cuatro amenazas de FIL.', SANS, 12, TXT2)], [('', SANS, 6, TXT)],
               [('Con un solo píxel no alcanza a separarse del azar: ', SANSB, 12, AMARILLO),
                ('hace falta el conteo global para ver si el patrón se sostiene en la región.', SANS, 12, TXT2)]]
    caja(s, xp + 0.25, 3.05, wp - 0.4, 6.6, lineas)
    return s
