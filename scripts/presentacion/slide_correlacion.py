"""Diapositiva «Cómo leer una correlación»: positiva, negativa y casi nula con datos reales del píxel de Nebraska.

Tres dispersiones nativas (editables) con clima y rendimiento sin tendencia, y una regla de −1 a +1 donde se ubican los tres r.
Rojo = positiva y azul = negativa, como en los mapas de correlación. Se inserta antes de «Un primer intento: el mar y el
rendimiento». Reejecutable: borra la diapositiva anterior con el mismo título.
Uso (con el .venv del pipeline):  python slide_correlacion.py --tendencia <carpeta tendencia_...> [--salida ruta.pptx]
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from pptx import Presentation
from pptx.chart.data import XyChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches
from scipy import stats

from slides_pixel_tipico import (PPT, TXT, TXT2, SRC, PANEL, SERIF, SANS, SANSB, caja, rect, base, estilo_ejes, puntos,
                                 recta, num, renumerar, mover, rgb)
from slides_inicio import por_titulo

ROJO, AZUL, GRIS = 'E5484D', '2B6CD9', '94A3B8'
TITULO = 'Cómo leer una correlación'
EJEMPLOS = [('FIL_p_menos_et0', 'Agua en el llenado', 'P − ETP en FIL (mm)', 'Más agua, más rendimiento', ROJO, 'positiva'),
            ('FIL_edd29', 'Calor extremo en el llenado', 'EDD29 en FIL (°C·día)', 'Más calor, menos rendimiento', AZUL, 'negativa'),
            ('REP_p_menos_et0', 'Agua en el cuajado', 'P − ETP en REP (mm)', 'No se mueven juntos', GRIS, 'casi nula')]


def sin_tendencia(v, t):
    lr = stats.linregress(t, v); return v - (lr.intercept + lr.slope * t)


def construir(prs, serie):
    for sl in list(prs.slides):
        if any(sh.has_text_frame and sh.text_frame.text.strip() == TITULO for sh in sl.shapes):
            lst = prs.slides._sldIdLst
            e = [x for x in lst if prs.slides.part.related_part(x.rId) is sl.part][0]
            prs.part.drop_rel(e.rId); lst.remove(e)
    t = serie.anio_cosecha.values.astype(float); y = serie.rendimiento_sin_tendencia_t_ha.values
    res = []
    for col, *_ in EJEMPLOS:
        x = sin_tendencia(serie[col].values.astype(float), t); r, p = stats.pearsonr(x, y); res.append((x, r, p))
    s = base(prs, TITULO, 'Cada punto es una cosecha de Nebraska (1981–2016). Clima y rendimiento, los dos sin tendencia.',
             'Datos: pixel_tipico/tendencia_20261029_175706 (pares_v2, ERA5-Land y GDHY). r de Pearson, n = 36.',
             'Guía para leer todas las correlaciones de la presentación, con tres casos reales del mismo píxel.\n'
             f'- Positiva: P − ETP en FIL vs rendimiento, r = {res[0][1]:+.2f} (p = {res[0][2]:.3f}). Años con más agua en el llenado rinden más que su tendencia.\n'
             f'- Negativa: EDD29 en FIL vs rendimiento, r = {res[1][1]:+.2f} (p < 0,001). Años con más calor extremo en el llenado rinden menos.\n'
             f'- Casi nula: P − ETP en REP vs rendimiento, r = {res[2][1]:+.2f} (p = {res[2][2]:.2f}). El agua en esos 10 días no se relaciona con el rendimiento.\n'
             'Lectura: el signo dice la dirección; el valor absoluto, qué tan cerca de una línea quedan los puntos. Con 36 años, |r| ≥ 0,33 equivale a p < 0,05. '
             'Una correlación no prueba causa: el mismo año puede traer calor y sequía juntos. Colores iguales a los mapas: rojo positiva, azul negativa.')
    for sh in s.shapes:
        if sh.name == 'PT_numero': sh.name = 'CR_numero'   # para que slides_pixel_tipico.py no la borre
    w, gap, y0, h = 5.08, 0.4, 2.85, 4.75
    for i, ((col, cab, eje, frase, color, tipo), (x, r, p)) in enumerate(zip(EJEMPLOS, res)):
        X = 1.98 + i * (w + gap)
        rect(s, X, y0, w, h, PANEL); rect(s, X, y0, w, 0.07, color)
        caja(s, X + 0.3, y0 + 0.25, w - 0.6, 0.4, [[(cab, SANSB, 17, TXT)]])
        caja(s, X + 0.3, y0 + 0.62, 2.6, 0.6, [[(f"r = {'+' if r > 0 else ''}{num(r)}", SERIF, 26, color)]])
        caja(s, X + 2.6, y0 + 0.74, w - 2.9, 0.45, [[(tipo, SANSB, 14, color)]], align=PP_ALIGN.RIGHT)
        cd = XyChartData(); se = cd.add_series('d')
        for a, b in zip(x, y): se.add_data_point(float(a), float(b))
        b1, b0 = np.polyfit(x, y, 1); xs = np.array([x.min(), x.max()])
        ln = cd.add_series('l')
        for a in xs: ln.add_data_point(float(a), float(b0 + b1 * a))
        gf = s.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER, Inches(X + 0.05), Inches(y0 + 1.25), Inches(w - 0.15), Inches(3.0), cd)
        ch = gf.chart; ch.has_legend = False
        lim = float(np.ceil(np.abs(x).max() / 25) * 25)
        estilo_ejes(ch, -lim, lim, -6, 2, lim, 2, xfmt='0;−0;0', yfmt='0;−0;0')
        puntos(ch.series[0], color, 8); recta(ch.series[1], 'CBD5E1', 1.5)
        caja(s, X + 0.2, y0 + 4.2, w - 0.4, 0.3, [[(eje, SANS, 12, SRC), ('  ·  vertical: rendimiento (t/ha)', SANS, 12, SRC)]], align=PP_ALIGN.CENTER)
        caja(s, X + 0.3, y0 + h + 0.12, w - 0.6, 0.4, [[(frase, SANSB, 16, color if color != GRIS else TXT2)]], align=PP_ALIGN.CENTER)
    # regla de −1 a +1
    yr, xa, xb = 8.9, 3.0, 17.0
    rect(s, xa, yr, xb - xa, 0.05, '334155')
    for v, et in [(-1, '−1'), (-.33, '−0,33'), (0, '0'), (.33, '+0,33'), (1, '+1')]:
        xx = xa + (v + 1) / 2 * (xb - xa)
        rect(s, xx - 0.01, yr - 0.1, 0.02, 0.25, '64748B')
        caja(s, xx - 0.5, yr + 0.18, 1.0, 0.3, [[(et, SANS, 12, SRC)]], align=PP_ALIGN.CENTER)
    for (col, cab, eje, frase, color, tipo), (x, r, p) in zip(EJEMPLOS, res):
        xx = xa + (r + 1) / 2 * (xb - xa)
        c = s.shapes.add_shape(9, Inches(xx - 0.13), Inches(yr - 0.11), Inches(0.26), Inches(0.26))
        c.fill.solid(); c.fill.fore_color.rgb = rgb(color); c.line.fill.background(); c.shadow.inherit = False
    caja(s, 1.98, yr - 0.15, 1.0, 0.35, [[('r', SERIF, 20, TXT)]])
    caja(s, xa, yr - 0.42, 4, 0.3, [[('← negativa', SANSB, 13, AZUL)]])
    caja(s, xb - 4, yr - 0.42, 4, 0.3, [[('positiva →', SANSB, 13, ROJO)]], align=PP_ALIGN.RIGHT)
    caja(s, 1.98, 9.5, 16.04, 0.5, [[('El signo dice la dirección; el tamaño, qué tan juntos están los puntos. ', SANSB, 16, TXT),
                                       ('Entre −0,33 y +0,33 no se distingue del azar con 36 años. Correlación no es causa.', SANS, 16, TXT2)]])
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--tendencia', required=True)
    ap.add_argument('--salida', default=str(PPT))
    a = ap.parse_args()
    serie = pd.read_excel(Path(a.tendencia) / 'tendencia.xlsx', 'serie_pixel')
    prs = Presentation(PPT)
    s = construir(prs, serie)
    destino = por_titulo(prs, 'Un primer intento: el mar y el rendimiento')
    pos = [prs.slides.index(sl) for sl in prs.slides if sl is destino][0]
    mover(prs, s, pos)
    renumerar(prs)
    prs.save(a.salida); print('guardado', a.salida)


if __name__ == '__main__':
    main()
