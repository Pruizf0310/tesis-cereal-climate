"""Inserta en la PPT oficial el bloque «píxel típico» (cierre de la primera ronda + tendencia), con el diseño de la PPT.

Reejecutable: borra primero las diapositivas con la forma PT_numero y vuelve a crear las tres de tendencia después de
«El mar y el rendimiento» (orden del 2 nov 2026; «Un píxel típico: Nebraska» y «Cerramos la primera ronda» ya no se insertan). Luego renumera los pies de página. Gráficos nativos de PowerPoint (editables) con los datos de
pixel_tipico/tendencia_<fecha>/tendencia.xlsx.
Uso (con el .venv del pipeline):
  python slides_pixel_tipico.py --tendencia <carpeta tendencia_...>
"""
import argparse, copy, re
from pathlib import Path

import pandas as pd
from lxml import etree
from pptx import Presentation
from pptx.chart.data import XyChartData, CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_MARKER_STYLE, XL_LABEL_POSITION, XL_TICK_LABEL_POSITION
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt, Emu

PPT = Path('C:/Users/paola/Tesis/Avance_tesis_oficial.pptx')
BG, TXT, TXT2, SRC, LINE = '050B1A', 'F8FAFC', 'CBD5E1', '94A3B8', '0B1730'
CIAN, MAG, PANEL = '22D3EE', 'E91E8C', '0B1730'
FASE_COLOR = dict(EST='A3E635', VEG='4ADE80', FLO='22D3EE', REP='3B82F6', FIL='A78BFA', MAT='E91E8C')
SERIF, SANS, SANSB = 'Fraunces Bold', 'DM Sans', 'DM Sans Bold'


def rgb(h): return RGBColor.from_string(h)


def num(x, d=2):
    return f'{x:,.{d}f}'.replace(',', 'X').replace('.', ',').replace('X', '.').replace('-', '−')


# ---------- primitivas con el estilo de la PPT ----------
def caja(s, x, y, w, h, partes, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, nombre=None):
    """partes: lista de párrafos; cada párrafo es lista de (texto, fuente, tamaño, color)."""
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if nombre: tb.name = nombre
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    for m in ('margin_left', 'margin_right', 'margin_top', 'margin_bottom'): setattr(tf, m, 0)
    for i, par in enumerate(partes):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        for texto, fuente, tam, color in par:
            r = p.add_run(); r.text = texto; fuente_run(r, fuente, tam, color)
    return tb


def fuente_run(r, fuente, tam, color):
    """Igual que las diapositivas originales: latin+ea+cs y b=1 en las familias «Bold» embebidas."""
    r.font.size = Pt(tam); r.font.color.rgb = rgb(color); r.font.name = fuente
    r.font.bold = fuente in (SERIF, SANSB)
    rpr = r._r.get_or_add_rPr()
    for tag in ('ea', 'cs'):
        el = rpr.find(qn(f'a:{tag}'))
        if el is None: el = etree.SubElement(rpr, qn(f'a:{tag}'))
        el.set('typeface', fuente)


def rect(s, x, y, w, h, color, linea=None, nombre=None):
    sh = s.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
    if nombre: sh.name = nombre
    if color: sh.fill.solid(); sh.fill.fore_color.rgb = rgb(color)
    else: sh.fill.background()
    if linea: sh.line.color.rgb = rgb(linea); sh.line.width = Pt(1)
    else: sh.line.fill.background()
    sh.shadow.inherit = False
    return sh


def base(prs, titulo, subtitulo, fuente, notas):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid(); s.background.fill.fore_color.rgb = rgb(BG)
    caja(s, 1.98, 0.82, 16.04, 0.7, [[(titulo, SERIF, 48, TXT)]])
    rect(s, 1.98, 1.667, 1.25, 0.052, MAG)
    if subtitulo: caja(s, 1.98, 2.28, 16.0, 0.4, [[(subtitulo, SANS, 19.5, TXT2)]])
    caja(s, 18.12, 10.48, 0.94, 0.29, [[('0', SANS, 15, TXT2)]], align=PP_ALIGN.RIGHT, nombre='PT_numero')
    if fuente: caja(s, 1.98, 10.05, 15.6, 0.4, [[(fuente, SANS, 13.5, SRC)]])
    s.notes_slide.notes_text_frame.text = notas
    return s


def item(s, y, n, cabeza, cuerpo, color=CIAN, linea=True):
    caja(s, 2.19, y - 0.14, 1.56, 0.99, [[(n, SERIF, 51, color)]])
    caja(s, 4.38, y, 12.6, 0.82, [[(cabeza, SANSB, 25.5, TXT)], [(cuerpo, SANS, 22, TXT2)]])
    if linea: rect(s, 4.38, y + 0.92, 12.81, 0.012, LINE)


def estilo_ejes(ch, xmin, xmax, ymin, ymax, xmaj, ymaj, xfmt='0', yfmt='0'):
    ch.font.name = SANS; ch.font.size = Pt(14); ch.font.color.rgb = rgb(SRC)
    for ax, lo, hi, mj, fmt in [(ch.category_axis, xmin, xmax, xmaj, xfmt), (ch.value_axis, ymin, ymax, ymaj, yfmt)]:
        ax.minimum_scale, ax.maximum_scale, ax.major_unit = lo, hi, mj
        ax.tick_labels.number_format = fmt; ax.tick_labels.number_format_is_linked = False
        ax.format.line.color.rgb = rgb('1E293B'); ax.has_major_gridlines = False
        ax.tick_label_position = XL_TICK_LABEL_POSITION.LOW
    ch.value_axis.has_major_gridlines = True
    ch.value_axis.major_gridlines.format.line.color.rgb = rgb('131E36')


def puntos(serie, color, tam=11):
    serie.marker.style = XL_MARKER_STYLE.CIRCLE; serie.marker.size = tam
    serie.marker.format.fill.solid(); serie.marker.format.fill.fore_color.rgb = rgb(color)
    serie.marker.format.line.fill.background(); serie.format.line.fill.background()


def recta(serie, color, ancho=2.5):
    serie.marker.style = XL_MARKER_STYLE.NONE
    serie.format.line.color.rgb = rgb(color); serie.format.line.width = Pt(ancho); serie.smooth = False


def etiqueta(serie, i, texto, color=MAG, pos=XL_LABEL_POSITION.RIGHT):
    dl = serie.points[i].data_label; dl.has_text_frame = True; dl.text_frame.text = texto; dl.position = pos
    fuente_run(dl.text_frame.paragraphs[0].runs[0], SANSB, 15, color)


# ---------- diapositivas ----------
def s_cierre(prs):
    s = base(prs, 'Cerramos la primera ronda',
             'Correlacionamos todo con todo: 10.923 píxeles de maíz de secano, 36 cosechas (1981–2016), seis fases.',
             'Corridas: correlaciones_v2_20261024_185040 y correlaciones_calendario_20261027_150249 (auditada). Alineación maturity-year (Iizumi y Sakai, 2020).',
             'Cierre de la primera ronda de correlaciones (oct. 2026).\n'
             '- Calor y sequía por fase muestran señal: con Bonferroni sobreviven 14 celdas grupo×fase de calor, 11 de EDD29 y 9 de sequía.\n'
             '- ONI (12 meses antes de la cosecha) y MJO (fracción de días por fase 1–8): 0 celdas tras Bonferroni; ONI→rendimiento por píxel sin significancia de campo.\n'
             '- Límites: conteo de episodios sin duración; fases colineales; calendario fijo por píxel; clima sin quitar tendencia (se cuantifica en las diapositivas siguientes).\n'
             'Sugerencia del director de tesis (29 oct 2026): 10 eventos no equivalen a 10 eventos si sus duraciones difieren; reiniciar con un píxel, evento por evento.')
    item(s, 3.05, '01', 'Lo que encontramos', 'Calor y sequía por fase sí se asocian al rendimiento: 34 celdas sobreviven a Bonferroni.')
    item(s, 4.75, '02', 'Lo que no apareció', 'ONI y MJO no muestran señal robusta: 0 celdas tras Bonferroni.')
    item(s, 6.45, '03', 'Por qué no basta', 'Contamos episodios sin su duración: 2 rachas de 8 días no equivalen a 2 de 2 días.')
    item(s, 8.15, '04', 'La nueva ruta', 'Un píxel, evento por evento, con clima y rendimiento sin tendencia.', color=MAG, linea=False)
    return s


def s_pixel(prs, cal, info):
    s = base(prs, 'Un píxel típico: Nebraska',
             f'Maíz de secano · {num(info["lat"])}° N, {num(abs(info["lon"]))}° O · celda GDHY de 0,5° (≈ 55 × 41 km) en el cinturón maicero de EE. UU.',
             'Calendario: GGCMI Phase 3 v1.01 + plantilla del proyecto v4 (fechas intermedias estimadas, iguales todos los años). Reglas: tabla maestra v2 de maíz (23 oct 2026).',
             'Píxel 191325. Elegido como referencia: 36 cosechas GDHY completas, rendimiento medio 7,9 t/ha (plausible), región productora principal.\n'
             'Calendario típico fijo: siembra día 116 (26 abr), ciclo de 148 días hasta el 20 sep. Bloques: VE 0–10 d, V1–V6 10–41 d, V7–VT 41–74 d, R1 74–83, R2 83–93, R3+R4–R5 93–133, R6 133–148.\n'
             'V1–V6 (31 días) no tiene ventana propia en el cálculo: la fase VEG del pipeline solo usa V7–VT. La diapositiva «El calendario del maíz» dice «seis ventanas continuas»; para este píxel no lo son. Decisión pendiente: incluir V1–V6 en VEG o declararlo hueco.\n'
             'FLO: la tabla v2 deja 33,7 °C (R1–R3) y anota 34,8 °C (VT–R1) como alternativa por decidir. FIL: 32,9 °C en v2 (32,7 °C en v1).')
    total = 148; x0, ancho = 1.98, 16.0; y = 3.35; h = 1.25
    bloques = [('EST', 0, 10), ('V1–V6', 10, 41), ('VEG', 41, 74), ('FLO', 74, 83), ('REP', 83, 93), ('FIL', 93, 133), ('MAT', 133, 148)]
    for nombre, a, b in bloques:
        x = x0 + ancho * a / total; w = ancho * (b - a) / total - 0.04
        if nombre == 'V1–V6':
            rect(s, x, y, w, h, None, linea='334155')
            caja(s, x, y, w, h, [[('V1–V6', SANSB, 17, SRC)], [('31 d · sin regla', SANS, 14, SRC)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
            continue
        rect(s, x, y, w, h, FASE_COLOR[nombre])
        if w > 0.9:
            caja(s, x, y, w, h, [[(nombre, SANSB, 17, BG)], [(f'{b - a} d', SANS, 15, BG)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        else:
            caja(s, x - 0.1, y, w + 0.2, h, [[(nombre, SANSB, 13, BG)], [(f'{b - a}', SANS, 13, BG)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    caja(s, x0, y + h + 0.12, 3, 0.35, [[('26 abr · siembra', SANS, 15, TXT2)]])
    caja(s, x0 + ancho - 3, y + h + 0.12, 3, 0.35, [[('20 sep · madurez', SANS, 15, TXT2)]], align=PP_ALIGN.RIGHT)
    # tabla de amenazas por fase
    filas = [('EST', '26 abr – 5 may', 'Tmax ≥ 34,0 °C, ≥ 2 días', 'P − ETP < Q1'),
             ('VEG', '6 jun – 8 jul', 'Tmax ≥ 34,6 °C, ≥ 2 días', 'P − ETP < Q1'),
             ('FLO', '9 – 17 jul', 'Tmax ≥ 33,7 °C, ≥ 2 días *', 'P − ETP < Q1'),
             ('REP', '18 – 27 jul', 'Tmax ≥ 33,7 °C, ≥ 2 días', '—'),
             ('FIL', '28 jul – 5 sep', 'Tmax ≥ 32,9 °C, ≥ 2 días', 'P − ETP < Q1'),
             ('MAT', '6 – 20 sep', '—', 'Lluvia: días con P > 10 mm')]
    yt = 5.55
    for j, cab in enumerate(['Fase', 'Ventana', 'Calor', 'Agua']):
        caja(s, [1.98, 3.6, 7.0, 12.0][j], yt, 4.5, 0.35, [[(cab, SANSB, 15, SRC)]])
    for i, (f, v, c, a) in enumerate(filas):
        yy = yt + 0.5 + i * 0.56
        rect(s, 1.98, yy + 0.08, 0.22, 0.22, FASE_COLOR[f])
        caja(s, 2.35, yy, 1.2, 0.4, [[(f, SANSB, 18, TXT)]])
        caja(s, 3.6, yy, 3.3, 0.4, [[(v, SANS, 18, TXT2)]])
        caja(s, 7.0, yy, 4.9, 0.4, [[(c, SANS, 18, TXT)]])
        caja(s, 12.0, yy, 5.9, 0.4, [[(a, SANS, 18, TXT)]])
        rect(s, 1.98, yy + 0.47, 16.0, 0.01, LINE)
    caja(s, 1.98, 9.5, 16, 0.4, [[('* FLO: 34,8 °C (VT–R1) sigue por decidir.  Q1 = primer cuartil 1981–2016 del propio píxel.  Mismo calendario todos los años.', SANS, 14, SRC)]])
    return s


def s_tendencia(prs, serie, info):
    s = base(prs, 'Qué tendencia le quitamos al rendimiento',
             'Rendimiento GDHY del píxel de Nebraska, 1981–2016 (t/ha). Una recta por mínimos cuadrados contra el año.',
             'Rendimiento: GDHY v1.2+v1.3 (Iizumi y Sakai, 2020), año de cosecha. Recta y residuo: mismo cálculo de TendRemove.ipynb, verificado (dif. < 10⁻⁷ t/ha).',
             'La tendencia es la recta rendimiento = a + b·año ajustada con las 36 cosechas del píxel. Pendiente b = +0,138 t/ha por año (p < 10⁻⁸); el año explica 65 % de la varianza.\n'
             'Esa subida sostenida se atribuye sobre todo a tecnología y manejo (híbridos, fertilización, densidad). No es clima de un año.\n'
             'Lo que se correlaciona con el clima es el residuo (punto menos recta). 2012: sequía y calor en el Medio Oeste, 5,6 t/ha, 4,1 t/ha por debajo de la recta.\n'
             'Límite: si el clima también cambió gradualmente, una parte de su efecto queda dentro de la recta y no en el residuo.')
    cd = XyChartData()
    a = cd.add_series('Rendimiento')
    for _, r in serie.iterrows(): a.add_data_point(r.anio_cosecha, r.rendimiento_crudo_t_ha)
    t = cd.add_series('Tendencia')
    for yy in (1981, 2016): t.add_data_point(yy, float(serie.set_index('anio_cosecha').tendencia_t_ha[yy]))
    gf = s.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER, Inches(1.7), Inches(2.95), Inches(10.6), Inches(6.9), cd)
    ch = gf.chart; ch.has_legend = False
    estilo_ejes(ch, 1980, 2017, 3, 12, 5, 3)
    puntos(ch.series[0], CIAN, 12); recta(ch.series[1], MAG, 3)
    i12 = int((serie.anio_cosecha == 2012).idxmax()); etiqueta(ch.series[0], i12, '2012 · sequía', MAG, XL_LABEL_POSITION.BELOW)
    pm = ch.series[0].points[i12].marker; pm.style = XL_MARKER_STYLE.CIRCLE; pm.size = 14
    pm.format.fill.solid(); pm.format.fill.fore_color.rgb = rgb(MAG); pm.format.line.fill.background()
    caja(s, 2.25, 2.62, 3, 0.35, [[('Rendimiento (t/ha)', SANSB, 15, TXT2)]])
    # lectura a la derecha
    xr = 13.1
    caja(s, xr, 3.1, 5.2, 1.0, [[('+0,14', SERIF, 60, MAG)]])
    caja(s, xr, 4.15, 5.2, 0.5, [[('t/ha por año: la recta', SANS, 19, TXT2)]])
    caja(s, xr, 5.0, 5.2, 1.0, [[(f'{num(info["tendencia_1981"], 1)} → {num(info["tendencia_2016"], 1)}', SERIF, 44, TXT)]])
    caja(s, xr, 5.85, 5.2, 0.5, [[('t/ha esperadas en 1981 y en 2016', SANS, 19, TXT2)]])
    caja(s, xr, 6.75, 5.2, 2.6, [[('La recta es tecnología y manejo. ', SANSB, 19, TXT),
                                  ('Lo que comparamos con el clima es la distancia de cada punto a la recta: el residuo.', SANS, 19, TXT2)]])
    return s


def s_scatter(prs, serie, corr):
    s = base(prs, 'Sin quitarla, la tecnología tapa al clima',
             'Calor extremo en llenado de grano (EDD29, °C·día) frente al rendimiento. Cada punto es una cosecha.',
             'EDD29 = Σ max(0, Tmax − 29 °C) en la ventana FIL (28 jul – 5 sep), ERA5-Land, promedio de celdas nativas. Pares de cruce_v2_20261024_184932, maturity-year.',
             'Izquierda: rendimiento crudo. Los años recientes están más arriba por tecnología, no por menos calor: la tendencia mezcla dos cosas. r = −0,46.\n'
             'Derecha: residuo (sin tendencia), con EDD29 también sin tendencia. La relación con el calor se ve limpia: r = −0,72 (p < 0,001, n = 36). Con EDD29 crudo: −0,71.\n'
             'Sin 2012 (n = 35, EDD29 crudo): r = −0,63 (p < 0,001). La relación no depende solo de la sequía de 2012.\n'
             'Asociación, no causalidad demostrada.')
    f = serie.set_index('anio_cosecha'); x = f['FIL_edd29']
    rc = corr.set_index(['fase', 'variable']).loc[('FIL', 'edd29')]
    for k, (col, titulo, rr, ymin, ymax, ymaj) in enumerate([
            ('rendimiento_crudo_t_ha', 'Rendimiento crudo (t/ha)', rc.r_crudo, 3, 12, 3),
            ('rendimiento_sin_tendencia_t_ha', 'Rendimiento sin tendencia (t/ha)', rc.r_ambos, -5, 2, 1)]):
        cd = XyChartData()
        for nombre, mask in [('1981–1998', f.index <= 1998), ('1999–2016', (f.index >= 1999) & (f.index != 2012)), ('2012', f.index == 2012)]:
            se = cd.add_series(nombre)
            for yy in f.index[mask]: se.add_data_point(float(x[yy]), float(f.loc[yy, col]))
        X0 = 1.7 + k * 8.4
        gf = s.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER, Inches(X0), Inches(3.35), Inches(7.9), Inches(5.9), cd)
        ch = gf.chart; ch.has_legend = False
        estilo_ejes(ch, 0, 160, ymin, ymax, 40, ymaj)
        puntos(ch.series[0], '64748B', 11); puntos(ch.series[1], CIAN, 11); puntos(ch.series[2], MAG, 13)
        caja(s, X0 + 0.1, 2.85, 5.8, 0.4, [[(titulo, SANSB, 17, TXT)]])
        caja(s, X0 + 5.2, 2.78, 2.6, 0.6, [[('r = ' + num(rr), SERIF, 30, MAG if k else TXT2)]], align=PP_ALIGN.RIGHT)
        caja(s, X0 + 0.1, 9.2, 7.6, 0.35, [[('EDD29 en llenado (°C·día)', SANS, 14, SRC)]], align=PP_ALIGN.CENTER)
    caja(s, 1.98, 9.6, 16, 0.4, [[('●', SANS, 15, '64748B'), (' 1981–1998    ', SANS, 15, TXT2), ('●', SANS, 15, CIAN),
                                  (' 1999–2016    ', SANS, 15, TXT2), ('●', SANS, 15, MAG), (' 2012', SANS, 15, TXT2)]])
    return s


def s_clima(prs, corr, glob):
    s = base(prs, '¿Y el clima? También puede tener tendencia',
             'Lo revisamos en los 10.923 píxeles: tendencia lineal 1981–2016 de cada variable, por fase.',
             'Fuente: pixel_tipico/tendencia_20261029_175706/tendencia.xlsx, hoja efecto_global. Píxeles con ≥ 20 años válidos; p de la pendiente con prueba t.',
             'Pregunta: qué tendencia se quita al clima y por qué. Respuesta: la misma recta contra el año, ahora sobre la variable climática de cada fase (EDD29, P − ETP, episodios).\n'
             'Por qué: el rendimiento ya no tiene tendencia; si el clima sí la tiene, esa parte no puede explicar el residuo y solo agrega ruido. Quitarla en ambos equivale a la correlación parcial controlando el año.\n'
             'Identidad: r(clima crudo, rendimiento sin tendencia) = r(ambos sin tendencia) · √(1 − R²), con R² la fracción de la variable climática explicada por el año. Nunca cambia el signo; solo la magnitud.\n'
             'Resultado: EDD29 en FIL tiene tendencia (p < 0,05) en 29 % de los píxeles (mediana +2,3 °C·día por década); por azar se esperaría 5 %. Aun así el cambio de r es mediana 0,004 y percentil 95 = 0,04 → las conclusiones de la primera ronda se mantienen. Se recalculará todo con ambos sin tendencia por consistencia.')
    FASES6 = ['EST', 'VEG', 'FLO', 'REP', 'FIL', 'MAT']
    cd = CategoryChartData(); cd.categories = FASES6
    g = glob.set_index(['variable', 'fase'])
    for v, nombre in [('edd29', 'EDD29'), ('p_menos_et0', 'P − ETP')]:
        cd.add_series(nombre, [round(float(g.loc[(v, f), 'pct_pixeles_tendencia_p05']), 1) for f in FASES6])
    gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(1.7), Inches(3.4), Inches(9.9), Inches(5.6), cd)
    ch = gf.chart; ch.has_legend = False
    ch.font.name = SANS; ch.font.size = Pt(15); ch.font.color.rgb = rgb(SRC)
    va = ch.value_axis; va.minimum_scale, va.maximum_scale, va.major_unit = 0, 35, 5
    va.major_gridlines.format.line.color.rgb = rgb('131E36'); va.format.line.fill.background()
    va.tick_labels.number_format = '0"%"'; va.tick_labels.number_format_is_linked = False
    ch.category_axis.format.line.color.rgb = rgb('1E293B')
    for i, c in enumerate([MAG, CIAN]):
        se = ch.plots[0].series[i]; se.format.fill.solid(); se.format.fill.fore_color.rgb = rgb(c)
    ch.plots[0].gap_width = 60; ch.plots[0].overlap = -10
    caja(s, 1.85, 2.9, 9.6, 0.4, [[('% de píxeles con tendencia significativa (p < 0,05)', SANSB, 17, TXT)]])
    caja(s, 1.85, 9.1, 9.6, 0.4, [[('■', SANS, 15, MAG), (' EDD29   ', SANS, 15, TXT2), ('■', SANS, 15, CIAN),
                                   (' P − ETP     por azar se esperaría 5 %', SANS, 15, TXT2)]])
    xr = 12.6
    caja(s, xr, 3.2, 5.6, 0.5, [[('Cuánto cambia r al quitarla', SANSB, 19, TXT)]])
    caja(s, xr, 3.85, 5.6, 1.0, [[('0,004', SERIF, 60, CIAN)]])
    caja(s, xr, 4.95, 5.6, 0.5, [[('mediana del cambio, peor fase', SANS, 18, TXT2)]])
    caja(s, xr, 5.75, 5.6, 1.0, [[('< 0,04', SERIF, 44, TXT)]])
    caja(s, xr, 6.6, 5.6, 0.5, [[('en el 95 % de los píxeles', SANS, 18, TXT2)]])
    caja(s, xr, 7.45, 5.6, 1.9, [[('Por qué tan poco: ', SANSB, 18, TXT),
                                  ('el año explica una parte pequeña del clima de cada fase. El signo nunca cambia; solo la magnitud.', SANS, 18, TXT2)]])
    return s


# ---------- ensamblaje ----------
def mover(prs, slide, pos):
    lst = prs.slides._sldIdLst; el = [e for e in lst if prs.slides.part.related_part(e.rId) is slide.part][0]
    lst.remove(el); lst.insert(pos, el)


def borrar_previas(prs):
    lst = prs.slides._sldIdLst
    for e in list(lst):
        part = prs.slides.part.related_part(e.rId)
        if any(sh.name == 'PT_numero' for sh in part.slide.shapes):
            prs.part.drop_rel(e.rId); lst.remove(e)
    prs.part.rename_slide_parts([e.rId for e in lst])  # evita nombres slideN.xml duplicados al volver a crear


def renumerar(prs):
    for i, s in enumerate(prs.slides, 1):
        for sh in s.shapes:
            if sh.has_text_frame and abs(sh.left / 914400 - 18.12) < .05 and abs(sh.top / 914400 - 10.48) < .05 \
                    and re.fullmatch(r'\d+', sh.text_frame.text.strip() or 'x'):
                sh.text_frame.paragraphs[0].runs[0].text = str(i)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--tendencia', required=True)
    ap.add_argument('--entrada', default=str(PPT))
    ap.add_argument('--salida', default=str(PPT))
    a = ap.parse_args()
    x = Path(a.tendencia) / 'tendencia.xlsx'
    serie = pd.read_excel(x, 'serie_pixel'); corr = pd.read_excel(x, 'correlaciones_pixel')
    glob = pd.read_excel(x, 'efecto_global')
    import json; info = json.loads((Path(a.tendencia) / 'resumen.json').read_text(encoding='utf-8'))['pixel']
    prs = Presentation(a.entrada)
    borrar_previas(prs)

    def despues_de(*titulos):
        for k, s in enumerate(prs.slides):
            if any(sh.has_text_frame and abs(sh.top / 914400 - 0.82) < .06 and sh.text_frame.text.strip() in titulos for sh in s.shapes):
                return k + 1
        raise ValueError(f'No encontré {titulos}')
    # 2 nov 2026: s_pixel ya no se inserta (repetía el calendario de la 14 y las amenazas de la 20) y s_cierre tampoco
    # (el bloque de la primera ronda salió de la presentación). La tendencia va justo después del primer intento de correlación.
    tendencia = [s_tendencia(prs, serie, info), s_scatter(prs, serie, corr), s_clima(prs, corr, glob)]
    p = despues_de('El mar y el rendimiento', 'Un primer intento: el mar y el rendimiento')
    for k, s in enumerate(tendencia): mover(prs, s, p + k)
    renumerar(prs)
    prs.save(a.salida); print('guardado', a.salida, len(prs.slides), 'diapositivas')


if __name__ == '__main__':
    main()
