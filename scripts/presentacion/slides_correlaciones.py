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


def s_eventos(prs, olas):
    """Cuántas olas de calor hay por fase y de qué grado (pixel_tipico_olas_amenazas.py, olas.csv). Sin rendimiento."""
    ol = pd.read_csv(olas / 'olas.csv')
    ol = ol[ol.amenaza == 'calor']
    tot = pd.crosstab(ol.fase, ol.grado).reindex(index=['VEG', 'FLO', 'REP', 'FIL'], columns=[g for g, _, _ in GRADOS], fill_value=0)
    cruzan = ol.groupby('fase').cruza_borde.sum()
    fuertes = sorted(ol[ol.grado.isin(['moderado', 'severo'])].anio.unique())
    ej = ol[(ol.anio == 1987) & ol.cruza_borde].iloc[0]
    s = nueva(prs, 'Cuántas olas y cuánto duran',
              'Una ola son días seguidos de calor en al menos la mitad del píxel. Se cuenta entera y una sola vez.',
              f'Fuente: pixel_tipico/{olas.name}/olas.csv (igual a conteo_reglas_20261105_133648) · Li et al. (2025b), Agronomy 15:1545, '
              'Tabla 2 · píxel 191325, 1981–2016.',
              'Ola del píxel: en cada una de las 25 celdas de ERA5-Land se marcan los días que forman racha (2 o más días seguidos con Tmax '
              'sobre el umbral de su fase); el píxel está en ola el día en que al menos la mitad de las celdas (ponderadas por cos(lat)) lo '
              'está. La ola no se corta en el borde de la fase: se cuenta completa y se asigna a la fase donde tiene más días. Grado por la '
              'duración completa con la Tabla 2 de Li et al. (2025b), por etapa, en días enteros (techo). «Menor que leve»: 2 días o más sin '
              'llegar al mínimo de leve. Verificación (5 nov 2026): pixel_tipico_conteo_reglas.py, que lee reglas_vigentes.csv, da las '
              'mismas 65 olas con las mismas fechas. La versión anterior de esta diapositiva contaba rachas por celda, cortadas en el borde '
              'y promediadas (por eso tenía decimales). EST y V1–V6 no tuvieron olas: sus umbrales (34,0 y 34,1 °C) no se alcanzan.')
    x0, y0, wf, wc, hf = 1.98, 3.05, 2.5, 1.55, 0.9
    cab = [nom for _, nom, _ in GRADOS] + ['Pasan de fase']
    caja(s, x0, y0, wf, 0.45, [[('Olas en 36 años', SANSB, 13, SRC)]], anchor=MSO_ANCHOR.MIDDLE)
    for j, nom in enumerate(cab):
        a = GRADOS[j][2] if j < 4 else None
        rect(s, x0 + wf + j * wc, y0, wc - 0.08, 0.45, mezcla(CALOR, a) if a else '3A3410')
        caja(s, x0 + wf + j * wc, y0, wc - 0.08, 0.45, [[(nom, SANSB, 13 if len(nom) > 10 else 14, TXT)]], align=PP_ALIGN.CENTER,
             anchor=MSO_ANCHOR.MIDDLE)
    for i, f in enumerate(['VEG', 'FLO', 'REP', 'FIL']):
        yy = y0 + 0.6 + i * (hf + 0.1)
        rect(s, x0, yy, 0.12, hf, FASE_COLOR[f])
        caja(s, x0 + 0.25, yy, wf - 0.3, hf, [[('REP-pos' if f == 'REP' else f, SANSB, 17, TXT)],
                                               [(UMBRAL_TXT[f] + ', ≥ 2 d', SANS, 11, SRC)]], anchor=MSO_ANCHOR.MIDDLE)
        for j, (g, _, a) in enumerate(GRADOS + [('cruza', '', None)]):
            v = int(tot.loc[f, g]) if g != 'cruza' else int(cruzan.get(f, 0))
            xx = x0 + wf + j * wc
            fondo = (mezcla(CALOR, a * min(v / 8, 1)) if a else '3A3410') if v else PANEL
            rect(s, xx, yy, wc - 0.08, hf, fondo)
            caja(s, xx, yy + 0.06, wc - 0.08, 0.5, [[(str(v), SERIF if v else SANS, 22 if v else 16, TXT if v else SRC)]],
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
            caja(s, xx, yy + 0.56, wc - 0.08, 0.28, [[(rango_fase(f, j) if a is not None or j < 4 else 'cruzan un borde', SANS, 11.5, TXT2)]],
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    caja(s, x0, y0 + 0.6 + 4 * (hf + 0.1) + 0.05, wf + 5 * wc, 0.6,
         [[('Arriba, cuántas olas en 36 años (números enteros: cada ola es del píxel completo); abajo, cuántos días seguidos dura '
            'una ola de ese grado (Li et al., 2025b, Tabla 2, por etapa).', SANS, 12, SRC)]])
    xr = x0 + wf + 5 * wc + 0.35; wr = 18.0 - xr
    rect(s, xr, y0, wr, 4.55, PANEL); rect(s, xr, y0, 0.07, 4.55, CIAN)
    caja(s, xr + 0.3, y0 + 0.15, wr - 0.5, 4.3, [
        [(f'{len(ol)} olas', SERIF, 30, AMARILLO)],
        [('Verificadas: ', SANSB, 13, TXT), ('el conteo desde reglas_vigentes.csv da las mismas 65, con las mismas fechas.', SANS, 13, TXT2)],
        [('', SANS, 6, TXT)],
        [('Antes: ', SANSB, 13, TXT), ('rachas por celda, cortadas en el borde de la fase y promediadas; por eso había decimales.', SANS, 13, TXT2)],
        [('', SANS, 6, TXT)],
        [('Años con ola moderada o severa', SANSB, 13, TXT)],
        [(', '.join(map(str, fuertes)), SANS, 13, AMARILLO)]])
    pasos = [('1', 'Contar', 'En cada celda y día: ¿Tmax ≥ umbral de la fase? 2 o más días seguidos son racha. Si la mitad del píxel '
                             'está en racha, ese día hay ola.'),
             ('2', 'Asignar fase', f'La ola se cuenta entera y una sola vez, en la fase donde tiene más días. Si pasa de una fase a otra, '
                                   f'queda marcada ({int(ol.cruza_borde.sum())} de {len(ol)}).'),
             ('3', 'Clasificar', f'Grado por la duración completa. Ej.: 1987, {ej.dias} días ({ej.dias_por_fase.replace(" + ", " en REP-pos + ")} '
                                 f'en FIL) → FIL, {ej.grado}.')]
    for k, (n, cab_, txt) in enumerate(pasos):
        xx, yy = x0 + k * 5.4, 8.75
        rect(s, xx, yy, 5.2, 1.2, PANEL)
        caja(s, xx + 0.15, yy + 0.1, 0.5, 0.6, [[(n, SERIF, 28, CIAN)]])
        caja(s, xx + 0.7, yy + 0.1, 4.35, 1.05, [[(cab_, SANSB, 14, TXT)], [(txt, SANS, 12, TXT2)]])
    return s


def s_olas(prs, olas, x):
    """Olas de calor de toda la temporada, año por año (pixel_tipico_rachas_temporada.py)."""
    ol = pd.read_csv(olas / 'rachas.csv'); dd = pd.read_csv(olas / 'dias.csv')
    y = x['serie'].set_index('anio').rendimiento_sin_tendencia_t_ha
    lim = dd[dd.anio == dd.anio.min()].groupby('fase').agg(i=('dia_ciclo', 'min'), f=('dia_ciclo', 'max'))
    d0, d1 = int(lim.loc['VEG', 'i']), int(lim.loc['FIL', 'f']) + 1
    cruzan = ol[ol.cruza_borde]; dos = cruzan[cruzan.pedazos_v3 > 1]; corta = cruzan[cruzan.dias_fuera_v3 > 0]
    s = nueva(prs, 'Las olas de calor, año por año',
              'Cada fila es un año y cada barra una ola. Así se ve qué olas quedan dentro de una fase y cuáles pasan a la siguiente.',
              f'Fuente: pixel_tipico/{olas.name}/rachas.csv (umbrales de reglas v3 por subfase, sin cortar en el borde de la fase) · '
              'rendimiento GDHY sin tendencia.',
              'Cómo explicarla: cada fila es una temporada (1981 arriba, 2016 abajo); el eje horizontal va del 6 de mayo al 5 de septiembre '
              'con las fases arriba. Cada barra es una ola: empieza el primer día en que la mitad del píxel está en racha de calor y termina '
              'el último. El color es el grado por la duración completa (Li et al., 2025b). Borde amarillo: la ola pasa de una fase a otra; '
              'se cuenta una sola vez, en la fase donde tiene más días. A la derecha, el rendimiento sin tendencia de ese año. '
              f'{len(ol)} olas en 36 años; {len(cruzan)} pasan de fase. Lo que sale de aquí para el análisis, por fase y año: número de '
              'olas, días en ola, ola más larga y grado mayor. Antes (reglas por fase) la racha se cortaba en el borde: '
              f'{len(dos)} olas se contaban dos veces ({", ".join(map(str, dos.anio))}); ya no.')
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
        [('Fila = un año. Barra = una ola, de su primer a su último día. Color = grado por la duración completa.', SANS, 12.5, TXT2)],
        [('', SANS, 6, TXT)],
        [(f'{len(cruzan)} de {len(ol)}', SERIF, 28, AMARILLO)],
        [('olas pasan de una fase a otra (borde amarillo)', SANSB, 13, TXT)],
        [('Se cuentan una vez, en la fase con más días:', SANS, 12.5, TXT2)],
        *[[(f'{o.anio}   ', SANSB, 11.5, TXT), (tramo(o), SANS, 11.5, TXT2)] for o in cruzan.itertuples()],
        [('', SANS, 6, TXT)],
        [('Lo que sale de aquí, por fase y año', SANSB, 13, TXT)],
        [('olas · días en ola · ola más larga · grado mayor', SANS, 12.5, CIAN)],
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
    ap.add_argument('--reglas', help='carpeta olas_amenazas_<fecha> (pixel_tipico_olas_amenazas.py); agrega la diapositiva de olas por fase')
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
