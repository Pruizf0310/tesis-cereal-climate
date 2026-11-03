"""Bloque «lo que construimos»: diapositivas 9 (cadena), 10 (calendario), 11 (fases), 12 (homologación),
14 (calendario del píxel) y 15 (exploración SST). Todo con el píxel de Nebraska (191325).

Busca cada diapositiva por su título (viejo o nuevo), cambia el título, conserva subrayado y número, y redibuja.
Datos: calendario_seis_fases_secano.csv, Catálogo fases (tabla_maestra_fenologia_global_v1.xlsx) y pixel_tipico/sst_<fecha>.
Uso (con el .venv del pipeline):  python slides_calendario.py --sst <carpeta sst_...> [--salida ruta.pptx]
"""
import argparse, json
from pathlib import Path

import numpy as np
import pandas as pd
from pptx import Presentation
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches

from slides_pixel_tipico import (PPT, BG, TXT, TXT2, SRC, LINE, CIAN, MAG, PANEL, SERIF, SANS, SANSB, FASE_COLOR,
                                 caja, rect, fuente_run, renumerar, rgb)
from slide_tesis import AMARILLO
from slides_inicio import por_titulo, poner_titulo, limpiar, nombrar

REPO = Path(__file__).resolve().parents[2]
CAL = Path('C:/Users/paola/Tesis/03_Resultados/Agroclima/vigente/calendario/calendario_seis_fases_secano.csv')
CATALOGO = REPO / 'outputs/fenologia_v1/tabla_maestra_fenologia_global_v1.xlsx'
PIXEL = dict(lat=42.75, lon=-97.25)
CULTIVOS = [('maize', 'Maíz', 'Escala V/R'), ('rice', 'Arroz', 'BBCH'), ('soybean', 'Soya', 'Fehr–Caviness'), ('wheat', 'Trigo', 'Zadoks')]
GRIS = ['1E293B', '2A3850']


def enlaces(s, y, lista, prefijo='Fuentes: '):
    tb = caja(s, 1.98, y, 15.8, 0.35, [[(prefijo, SANS, 13, SRC)]])
    p = tb.text_frame.paragraphs[0]
    for i, (texto, url) in enumerate(lista):
        r = p.add_run(); r.text = texto; fuente_run(r, SANS, 13, CIAN)
        if url: r.hyperlink.address = url
        if i < len(lista) - 1:
            r = p.add_run(); r.text = '  ·  '; fuente_run(r, SANS, 13, SRC)


def preparar(prs, titulos, nuevo):
    s = por_titulo(prs, *titulos, nuevo)
    poner_titulo(s, nuevo)
    return s, limpiar(s)


def etiqueta_codigo(c):
    return (c.replace('BBCH_', '').replace('WHEAT_', '').replace('_', '–').replace('Z', '')
            if not c.startswith(('V', 'R')) else c.replace('_', '–').replace('VN', 'Vn'))


# ---------- 9 ----------
def s09(prs):
    s, n0 = preparar(prs, ('Cómo evolucionó el método',), 'Lo que construimos para analizar')
    caja(s, 1.98, 2.28, 16, 0.4, [[('Cinco piezas en cadena. Cada una se muestra con el mismo píxel: maíz de secano en Nebraska.', SANS, 19.5, TXT2)]])
    piezas = [('01 · CALENDARIO', 'Cuándo ocurre cada fase del cultivo', '26 abr – 20 sep, 148 días, seis fases', 'Hecho', AMARILLO),
              ('02 · AMENAZAS', 'Qué puede dañar al cultivo en cada fase', 'Calor de EST a FIL, sequía y lluvia en MAT', 'Hecho', CIAN),
              ('03 · UMBRALES', 'Desde qué valor se considera daño', 'Tmax ≥ 32,9–34,6 °C por ≥ 2 días; P − ETP < Q1', 'FLO por decidir', CIAN),
              ('04 · CONTEO', 'Cuántos eventos, de qué duración e intensidad', 'Por fase y por año, 1981–2016', 'En curso', CIAN),
              ('05 · CORRELACIONES', 'Qué se asocia con el rendimiento', '36 cosechas, todo sin tendencia', 'Segunda ronda', AMARILLO)]
    x0, w, gap, y0, h = 1.98, 2.95, 0.322, 3.15, 4.9
    for i, (eti, que, ej, estado, color) in enumerate(piezas):
        x = x0 + i * (w + gap)
        rect(s, x, y0, w, h, PANEL); rect(s, x, y0, w, 0.07, color)
        caja(s, x + 0.25, y0 + 0.32, w - 0.4, 0.35, [[(eti, SANSB, 13.5, color)]])
        caja(s, x + 0.25, y0 + 0.8, w - 0.45, 1.5, [[(que, SANSB, 19, TXT)]])
        rect(s, x + 0.25, y0 + 2.55, w - 0.5, 0.012, '334155')
        caja(s, x + 0.25, y0 + 2.7, w - 0.45, 0.35, [[('En Nebraska', SANSB, 13, SRC)]])
        caja(s, x + 0.25, y0 + 3.05, w - 0.45, 1.1, [[(ej, SANS, 15, TXT2)]])
        rect(s, x + 0.25, y0 + h - 0.62, w - 0.5, 0.38, BG, linea=color)
        caja(s, x + 0.25, y0 + h - 0.62, w - 0.5, 0.38, [[(estado, SANSB, 12.5, color)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        if i < 4:
            caja(s, x + w - 0.02, y0 + h / 2 - 0.3, gap + 0.04, 0.6, [[('→', SANS, 24, CIAN)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    caja(s, 1.98, 8.5, 16, 0.5, [[('Orden de lo que sigue: ', SANSB, 20, TXT),
                                  ('primero el calendario y sus fases, luego una exploración con el mar, después amenazas, umbrales, conteo y correlaciones.', SANS, 20, TXT2)]])
    s.notes_slide.notes_text_frame.text = (
        'Cadena de construcción del análisis, con el píxel 191325 (Nebraska, 42,75° N, 97,25° O) como hilo de toda la presentación.\n'
        'Estado al 1 nov 2026: calendario v4 hecho; amenazas y umbrales en la tabla maestra v2 (FLO 33,7 °C vs 34,8 °C por decidir); '
        'conteo por tipo de evento (duración, intensidad) en curso, por sugerencia del director de tesis; correlaciones: primera ronda cerrada, '
        'segunda ronda con clima y rendimiento sin tendencia.')
    nombrar(s, n0)


# ---------- 10 ----------
def s10(prs):
    s, n0 = preparar(prs, ('Las fuentes del calendario',), 'Cómo construimos el calendario')
    caja(s, 1.98, 2.28, 16, 0.4, [[('Una fuente da el inicio y el final del ciclo; la literatura de cada cultivo llena lo que pasa en medio.', SANS, 19.5, TXT2)]])
    # fuente principal
    rect(s, 1.98, 3.0, 6.4, 6.55, PANEL); rect(s, 1.98, 3.0, 6.4, 0.07, AMARILLO)
    caja(s, 2.3, 3.3, 5.9, 0.35, [[('FUENTE PRINCIPAL', SANSB, 13.5, SRC)]])
    caja(s, 2.3, 3.7, 5.9, 0.6, [[('GGCMI Phase 3', SERIF, 28, AMARILLO)]])
    caja(s, 2.3, 4.35, 5.9, 0.4, [[('v1.01 · Jägermeyr et al. (2021)', SANS, 15, TXT2)]])
    caja(s, 2.3, 5.0, 5.9, 0.35, [[('Contiene', SANSB, 16, TXT)]])
    caja(s, 2.3, 5.4, 5.9, 1.6, [[('+ ', SANSB, 15, CIAN), ('Fecha típica de siembra y de madurez', SANS, 15, TXT2)],
                                 [('+ ', SANSB, 15, CIAN), ('Cada celda de 0,5° del mundo', SANS, 15, TXT2)],
                                 [('+ ', SANSB, 15, CIAN), ('Por temporada y por riego o secano', SANS, 15, TXT2)]])
    caja(s, 2.3, 7.15, 5.9, 0.35, [[('No contiene', SANSB, 16, TXT)]])
    caja(s, 2.3, 7.55, 5.9, 1.8, [[('− ', SANSB, 15, MAG), ('Fechas de las fases intermedias', SANS, 15, TXT2)],
                                  [('− ', SANSB, 15, MAG), ('Cambios de un año a otro: es un calendario típico', SANS, 15, TXT2)],
                                  [('− ', SANSB, 15, MAG), ('Observación de campo en cada celda', SANS, 15, TXT2)]])
    # evolución
    pasos = [('GEOGLAM CM4EW', 'Ventanas mensuales amplias por región y sin soya: no alcanzaba para fases.'),
             ('GGCMI Phase 3', 'Siembra y madurez por píxel. SAGE y MIRCA-OS solo para comparar, sin promediar.'),
             ('Escala de cada cultivo', 'V/R, BBCH, Fehr–Caviness y Zadoks: ocho etapas con su fracción del ciclo.'),
             ('Calendario completo', 'Fecha de cada etapa = siembra + fracción × duración del píxel. 85.916 calendarios.')]
    xr = 9.0
    caja(s, xr, 3.05, 9, 0.35, [[('CÓMO EVOLUCIONÓ', SANSB, 13.5, SRC)]])
    rect(s, xr + 0.27, 3.75, 0.02, 5.1, '334155')
    for i, (cab, txt) in enumerate(pasos):
        y = 3.55 + i * 1.47
        c = s.shapes.add_shape(9, Inches(xr), Inches(y), Inches(0.56), Inches(0.56))
        c.fill.solid(); c.fill.fore_color.rgb = rgb(BG)
        c.line.color.rgb = rgb(AMARILLO if i == 3 else CIAN); c.shadow.inherit = False
        caja(s, xr, y, 0.56, 0.56, [[(str(i + 1), SANSB, 15, TXT)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        caja(s, xr + 0.85, y + 0.02, 8.1, 0.4, [[(cab, SANSB, 18, AMARILLO if i == 3 else TXT)]])
        caja(s, xr + 0.85, y + 0.45, 8.1, 0.8, [[(txt, SANS, 15.5, TXT2)]])
    caja(s, 1.98, 9.68, 16, 0.4, [[('Cada píxel tiene su propia siembra y duración. Las fechas intermedias son estimadas, no observadas.', SANSB, 15, TXT)]])
    enlaces(s, 10.12, [('GGCMI Phase 3', 'https://doi.org/10.5281/zenodo.5062513'), ('SAGE (Sacks et al., 2010)', 'https://doi.org/10.1111/j.1466-8238.2010.00551.x'),
                       ('MIRCA-OS', 'https://doi.org/10.1038/s41597-024-04313-w'), ('GEOGLAM CM4EW', 'https://cropmonitor.org/index.php/eodatatools/baseline-data/')])
    s.notes_slide.notes_text_frame.text = (
        'GGCMI Phase 3 v1.01 (Jägermeyr et al., 2021; Zenodo 10.5281/zenodo.5062513): fechas representativas de siembra y madurez en malla de 0,5°, '
        'por temporada y sistema hídrico. No es un registro anual observado.\n'
        'Evolución: (1) GEOGLAM CM4EW v1.3 daba ventanas mensuales por región y no traía soya; agregarlas por latitud mostraba fragmentos sueltos de fase. '
        '(2) Se pasó a GGCMI por píxel; SAGE (Sacks et al., 2010) y MIRCA-OS se usaron como comparación, no como sustitución. '
        '(3) Plantilla de ocho etapas por cultivo con fracciones normalizadas del ciclo (Catálogo fases, tabla_maestra_fenologia_global_v1.xlsx). '
        '(4) Fecha de frontera = siembra + fracción × duración local; se verifica que no haya huecos ni solapes y que el ciclo sume completo. '
        'Resultado: 85.916 calendarios y 687.328 registros de etapa (inventario general, más amplio que los píxeles con rendimiento).\n'
        'Limitación: no hay una calibración bibliográfica de cada fracción por cultivo y lugar; las fechas intermedias son estimadas.')
    nombrar(s, n0)


def barra(s, x, y, w, h, segs, texto_color=TXT, alto_txt=14):
    """segs: lista (ancho_relativo, color, etiqueta)."""
    tot = sum(a for a, _, _ in segs); xx = x
    for a, color, et in segs:
        ww = w * a / tot
        rect(s, xx, y, ww - 0.03, h, color)
        if et:
            caja(s, xx - 0.05, y, ww + 0.07, h, [[(et, SANSB, alto_txt if ww > 0.75 else (alto_txt - 3 if len(et) <= 4 else alto_txt - 5), texto_color)]],
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        xx += ww


# ---------- 11 ----------
def s11(prs, cat, cic):
    s, n0 = preparar(prs, ('Cómo estimamos las fechas intermedias',), 'Las fases según la literatura')
    caja(s, 1.98, 2.28, 16, 0.4, [[('Cada cultivo tiene su escala de desarrollo: ocho etapas y el peso de cada una en el ciclo.', SANS, 19.5, TXT2)]])
    caja(s, 1.98, 2.95, 2.6, 0.35, [[('Cultivo', SANSB, 14, SRC)]])
    caja(s, 4.6, 2.95, 10, 0.35, [[('Ocho etapas, en proporción al ciclo', SANSB, 14, SRC)]])
    caja(s, 15.4, 2.95, 2.6, 0.35, [[('Ciclo típico', SANSB, 14, SRC)]], align=PP_ALIGN.RIGHT)
    for i, (crop, nombre, escala) in enumerate(CULTIVOS):
        y = 3.5 + i * 1.45
        g = cat[cat.crop == crop].sort_values('phase_order')
        caja(s, 1.98, y + 0.05, 2.6, 0.4, [[(nombre, SANSB, 19, AMARILLO)]])
        caja(s, 1.98, y + 0.5, 2.6, 0.4, [[(escala, SANS, 14, TXT2)]])
        barra(s, 4.6, y, 10.5, 0.95, [(r.nominal_cycle_pct, GRIS[k % 2], etiqueta_codigo(r.phase_code)) for k, r in enumerate(g.itertuples())])
        q = cic[crop]
        caja(s, 15.4, y + 0.02, 2.6, 0.5, [[(f'{q[1]:.0f} días', SERIF, 22, TXT)]], align=PP_ALIGN.RIGHT)
        caja(s, 15.4, y + 0.52, 2.6, 0.4, [[(f'{q[0]:.0f}–{q[2]:.0f} según el píxel', SANS, 13, SRC)]], align=PP_ALIGN.RIGHT)
    caja(s, 1.98, 9.35, 16, 0.6, [[('Las fracciones ordenan las etapas y reparten el ciclo de cada píxel; ', SANSB, 15, TXT),
                                   ('no son fechas observadas. Ciclo: mediana y percentiles 10–90 de los píxeles de secano.', SANS, 15, TXT2)]])
    enlaces(s, 10.12, [('Maíz V/R (U. Minnesota)', 'https://ipmworld.umn.edu/maize-insect-pests-maize-growth-development'),
                       ('Arroz BBCH (IRRI)', 'https://www.knowledgebank.irri.org/ericeproduction/0.2._Growth_stages_of_the_rice_plant.htm'),
                       ('Soya (Mississippi State)', 'https://www.extension.msstate.edu/publications/guide-soybean-growth-stages'),
                       ('Catálogo de fases', None)])
    s.notes_slide.notes_text_frame.text = (
        'Plantillas de ocho etapas por cultivo (hoja «Catálogo fases» de outputs/fenologia_v1/tabla_maestra_fenologia_global_v1.xlsx), con su porcentaje nominal del ciclo:\n'
        '- Maíz (Hanway/USDA, V/R): VE 7 %, V1–V6 21 %, V7–VT 22 %, R1 6 %, R2 7 %, R3 9 %, R4–R5 18 %, R6 10 %.\n'
        '- Arroz (BBCH): 00–09 8 %, 10–19 9 %, 20–29 21 %, 30–39 14 %, 40–59 12 %, 60–69 6 %, 70–79 20 %, 80–99 10 %.\n'
        '- Soya (Fehr–Caviness): VE–VC 8 %, V1–Vn 30 %, R1–R2 12 %, R3 8 %, R4 9 %, R5 11 %, R6–R7 15 %, R8 7 %.\n'
        '- Trigo (Zadoks/BBCH): 00–09 7 %, 10–29 28 %, 30–39 15 %, 40–49 10 %, 50–59 8 %, 60–69 6 %, 70–89 19 %, 90–99 7 %.\n'
        'Duración del ciclo por píxel (calendario_seis_fases_secano.csv, secano): maíz mediana 132 d (p10 90, p90 180); arroz 140 (111–170); soya 131 (102–160); trigo 117 (107–184).\n'
        'Las escalas sustentan nombres y orden biológico, no fracciones temporales específicas: esa calibración por cultivo y lugar no existe en el material archivado.')
    nombrar(s, n0)


# ---------- 12 ----------
MAPA = {'maize': {'VE': 'EST', 'V1_V6': 'VEG', 'V7_VT': 'VEG', 'R1': 'FLO', 'R2': 'REP', 'R3': 'FIL', 'R4_R5': 'FIL', 'R6': 'MAT'},
        'rice': {'BBCH_00_09': 'EST', 'BBCH_10_19': 'VEG', 'BBCH_20_29': 'VEG', 'BBCH_30_39': 'REP', 'BBCH_40_59': 'REP',
                 'BBCH_60_69': 'FLO', 'BBCH_70_79': 'FIL', 'BBCH_80_99': 'MAT'},
        'soybean': {'VE_VC': 'EST', 'V1_VN': 'VEG', 'R1_R2': 'FLO', 'R3': 'REP', 'R4': 'REP', 'R5': 'FIL', 'R6_R7': 'FIL', 'R8': 'MAT'},
        'wheat': {'Z00_09': 'EST', 'Z10_29': 'VEG', 'Z30_39': 'VEG', 'Z40_49': 'REP', 'Z50_59': 'REP', 'Z60_69': 'FLO',
                  'Z70_89': 'FIL', 'Z90_99': 'MAT'}}
DECISION = {'maize': 'REP-pos = R2, grano en ampolla: el grano cuaja después de la floración.',
            'rice': 'REP-pre = iniciación de panícula, embuche y espigamiento, antes de la antesis.',
            'soybean': 'REP-pos = R3–R4: se forman las vainas después de la floración.',
            'wheat': 'REP-pre = embuche y espigamiento (Zadoks 40–59), antes de la antesis.'}
# Nomenclatura (decisión del 1 nov 2026): la fase REP se nombra según su momento frente a la floración.
REP_NOMBRE = {'maize': 'REP-pos', 'soybean': 'REP-pos', 'rice': 'REP-pre', 'wheat': 'REP-pre'}
REP_COLOR = {'REP-pos': FASE_COLOR['REP'], 'REP-pre': '7DB3FF'}


def s12(prs, cat):
    s, n0 = preparar(prs, ('La homologación en seis fases',), 'De ocho etapas a seis fases')
    caja(s, 1.98, 2.28, 16, 0.4, [[('Las mismas etapas, ahora agrupadas en seis fases comunes a los cuatro cultivos.', SANS, 19.5, TXT2)]])
    for i, (crop, nombre, _) in enumerate(CULTIVOS):
        y = 2.95 + i * 1.12
        g = cat[cat.crop == crop].sort_values('phase_order')
        segs = []
        for r in g.itertuples():
            f = MAPA[crop][r.phase_code]
            if segs and segs[-1][2] in (f, REP_NOMBRE[crop] if f == 'REP' else None): segs[-1][0] += r.nominal_cycle_pct
            else:
                et = REP_NOMBRE[crop] if f == 'REP' else f
                segs.append([r.nominal_cycle_pct, REP_COLOR.get(et, FASE_COLOR[f]), et])
        caja(s, 1.98, y + 0.15, 2.0, 0.45, [[(nombre, SANSB, 19, AMARILLO)]])
        barra(s, 4.0, y, 8.6, 0.75, [tuple(x) for x in segs], texto_color=BG, alto_txt=14)
        caja(s, 12.95, y + 0.0, 5.1, 0.8, [[(DECISION[crop], SANS, 14, TXT2)]])
    y0 = 7.45
    rect(s, 1.98, y0, 16.04, 1.6, PANEL); rect(s, 1.98, y0, 0.07, 1.6, FASE_COLOR['REP'])
    caja(s, 2.35, y0 + 0.18, 15.4, 0.4, [[('Dos REP: la misma fase reproductiva, en distinto momento', SANSB, 18, TXT)]])
    caja(s, 2.35, y0 + 0.65, 15.4, 0.9, [[('REP-pre', SANSB, 15.5, REP_COLOR['REP-pre']), (' (arroz, trigo): se forma la panícula o la espiga, antes de florecer.   ', SANS, 15.5, TXT2),
                                          ('REP-pos', SANSB, 15.5, REP_COLOR['REP-pos']), (' (maíz, soya): cuaja el grano o la vaina, después de florecer. ', SANS, 15.5, TXT2),
                                          ('Son equivalentes como fase, no como proceso: no se comparan cultivos por REP sin decir cuál.', SANSB, 15.5, TXT)]])
    caja(s, 1.98, 9.55, 16, 0.45, [[('Cada día del ciclo queda en una sola fase, sin huecos ni solapes. ', SANSB, 14, TXT),
                                    ('Las seis fases son una convención del proyecto, no una escala botánica nueva.', SANS, 14, TXT2)]])
    enlaces(s, 10.12, [('Maíz (U. Delaware)', 'https://www.udel.edu/academics/colleges/canr/cooperative-extension/fact-sheets/corn-growth-stages-and-management/'),
                       ('Arroz (IRRI)', 'https://www.knowledgebank.irri.org/ericeproduction/0.2._Growth_stages_of_the_rice_plant.htm'),
                       ('Soya (UNL CropWatch)', 'https://cropwatch.unl.edu/setting-yield-soybean-and-avoiding-end-season-plant-stress-unl-cropwatch-aug-23-2013/')])
    s.notes_slide.notes_text_frame.text = (
        'Correspondencia regional-v4 (16 sep 2026; six_phase_correspondence_v4.json), verificada en calendario_seis_fases_secano.csv:\n'
        '- Maíz: VE→EST; V1–V6 y V7–VT→VEG; R1→FLO; R2→REP; R3 y R4–R5→FIL; R6→MAT.\n'
        '- Arroz: 00–09→EST; 10–19 y 20–29→VEG; 30–39 y 40–59→REP; 60–69→FLO; 70–79→FIL; 80–99→MAT.\n'
        '- Soya: VE–VC→EST; V1–Vn→VEG; R1–R2→FLO; R3 y R4→REP; R5 y R6–R7→FIL; R8→MAT.\n'
        '- Trigo: 00–09→EST; 10–29 y 30–39→VEG; 40–49 y 50–59→REP; 60–69→FLO; 70–89→FIL; 90–99→MAT.\n'
        'Por qué REP precede a FLO en arroz y trigo: en los cereales de grano pequeño la fase reproductiva empieza con la iniciación de la panícula o espiga, '
        'dentro del tallo, y sigue con embuche y espigamiento; la antesis (FLO) viene después (IRRI: fase reproductiva = iniciación de panícula a espigamiento; '
        'Zadoks: 40–49 embuche, 50–59 espigamiento, 60–69 antesis). En maíz y soya la floración (R1; R1–R2) es la primera etapa reproductiva y REP se usó para el '
        'cuajado posterior (R2; R3–R4). No es un error de cálculo: calendario_seis_fases_secano.csv tiene REP antes de FLO en el 100 % de los calendarios de arroz y trigo '
        'y después en el 100 % de maíz y soya, como la revisión humana (Hoja1). Sí es una inconsistencia de definición: la Hoja1 define REP con procesos posteriores '
        'a la floración (pod set, fruit set, grain set, early reproductive stage), pero para arroz y trigo le asigna etapas previas a la floración. Las amenazas de esas '
        'etapas (frío o calor en embuche, Barber et al. 2017; iniciación de panícula, Sun et al. 2025) son las que justificaron esa ventana. '
        'Opción pendiente: renombrar por cultivo (p. ej., «formación de panícula/espiga» frente a «cuajado») para no sugerir equivalencia.\n'
        'Antes (v3) se unían ventanas compartidas (FLO+REP en maíz, VEG+REP en arroz, FIL+MAT en soya); v4 asigna bloques enteros y no corta ninguno en una fecha inventada. '
        'Es una partición analítica de procesos biológicos que pueden solaparse.')
    nombrar(s, n0)


# ---------- 14 ----------
def s14(prs, cal):
    s, n0 = preparar(prs, ('El calendario final en una celda',), 'El calendario de nuestro píxel')
    g = cal[(cal.crop == 'maize') & (cal.lat == PIXEL['lat']) & (cal.lon == PIXEL['lon'])].copy()
    fecha = lambda doy: (pd.Timestamp('2001-01-01') + pd.Timedelta(days=int(doy) - 1))
    mes = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
    f = lambda doy: f'{fecha(doy).day} {mes[fecha(doy).month - 1]}'
    ciclo = int(g.cycle_days.iloc[0])
    caja(s, 1.98, 2.28, 16, 0.4, [[(f'Maíz de secano · Nebraska, 42,75° N, 97,25° O · siembra {f(g.start_doy.min())} · madurez {f(g.end_doy.max())} · {ciclo} días · igual los 36 años', SANS, 19.5, TXT2)]])
    x0, w, y, h = 1.98, 16.04, 3.25, 1.3
    xx = x0
    for r in g.itertuples():
        ww = w * r.duration_days / ciclo
        rect(s, xx, y, ww - 0.04, h, FASE_COLOR[r.phase])
        if ww > 0.9:
            caja(s, xx, y, ww - 0.04, h, [[('REP-pos' if r.phase == 'REP' else r.phase, SANSB, 18 if r.phase != 'REP' else 15, BG)], [(f'{r.duration_days} d', SANS, 15, BG)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        caja(s, xx, y + h + 0.1, max(ww, 1.6) if r.phase != 'MAT' else ww, 0.6,
             [[(f'{f(r.start_doy)} –', SANS, 13, TXT2)], [(f(r.end_doy), SANS, 13, TXT2)]])
        if r.phase == 'VEG':
            xv, wv = xx, ww
        xx += ww
    # VEG por dentro
    v1 = w * 31 / ciclo
    yb = y + h + 0.95
    rect(s, xv, yb, v1 - 0.04, 0.45, None, linea='64748B')
    caja(s, xv, yb, v1 - 0.04, 0.45, [[('V1–V6 · 31 d', SANS, 13, SRC)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    rect(s, xv + v1, yb, wv - v1 - 0.04, 0.45, None, linea=FASE_COLOR['VEG'])
    caja(s, xv + v1, yb, wv - v1 - 0.04, 0.45, [[('V7–VT · 33 d', SANS, 13, FASE_COLOR['VEG'])]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    rect(s, 1.98, 6.55, 16.04, 1.75, PANEL); rect(s, 1.98, 6.55, 0.07, 1.75, MAG)
    caja(s, 2.35, 6.75, 15.4, 0.4, [[('Una diferencia que hay que resolver', SANSB, 18, TXT)]])
    caja(s, 2.35, 7.25, 15.4, 1.4, [[('El calendario pone 64 días en VEG (6 may – 8 jul). El conteo de calor de VEG solo usó V7–VT (6 jun – 8 jul): ', SANS, 16, TXT2),
                                     ('los 31 días de V1–V6 quedaron por fuera. ', SANSB, 16, TXT),
                                     ('Decisión pendiente: sumarlos a VEG o declararlos fuera del análisis.', SANS, 16, TXT2)]])
    caja(s, 1.98, 8.95, 16, 0.75, [[('Por qué este píxel: ', SANSB, 15, TXT),
                                    ('el 32 % de su área es maíz (más que el 97 % de los píxeles) y su rendimiento varía más que en el 96 % de las zonas maiceras con datos creíbles. 36 cosechas, media 7,9 t/ha.', SANS, 15, TXT2)]])
    enlaces(s, 10.12, [('GGCMI Phase 3', 'https://doi.org/10.5281/zenodo.5062513'), ('calendario_seis_fases_secano.csv', None)], prefijo='Calendario: ')
    s.notes_slide.notes_text_frame.text = (
        'Píxel 191325, maíz de secano (calendario_seis_fases_secano.csv, versión regional-v4-2026-09-16): siembra día 116 (26 abr), ciclo 148 días, fin día 263 (20 sep). '
        'EST 26 abr–5 may (10 d, VE); VEG 6 may–8 jul (64 d, V1–V6 + V7–VT); FLO 9–17 jul (9 d, R1); REP 18–27 jul (10 d, R2); FIL 28 jul–5 sep (40 d, R3 + R4–R5); MAT 6–20 sep (15 d, R6). '
        'Incertidumbre registrada ±15 días (etiqueta del modelo, no IC).\n'
        'Inconsistencia: el pipeline de amenazas (maize_seis_fases.py, STAGES) define VEG = V7–VT, así que las ventanas de VEG en pares_v2 empiezan el 6 jun. '
        'Las demás fases coinciden.\n'
        'Criterio de elección (1 nov 2026): área con maíz (GEOGLAM BACS Percent_Maize.tif, promedio en la celda de 0,5°) = 32,2 %, percentil 97 de los 10.923 píxeles; '
        'desviación estándar del rendimiento sin tendencia = 1,07 t/ha, percentil 96 entre los 218 píxeles con ≥ 20 % de maíz, 36 años y rendimiento ≤ 15 t/ha. '
        'Los píxeles de mayor variabilidad absoluta (Irak, Irán, Uzbekistán) se descartaron: zonas desérticas etiquetadas como secano. '
        'El ejemplo anterior de esta diapositiva (Chile, 40,25° S) va de 8,6 a 27,9 t/ha: inverosímil.')
    nombrar(s, n0)


# ---------- 15 ----------
FIG12 = Path('C:/Users/paola/Tesis/03_Resultados/Agroclima/vigente/pixel_tipico/mapas_sst_12meses_191325.png')


def s15(prs, sst):
    s, n0 = preparar(prs, ('Un primer intento y el giro', 'Un primer intento: el mar y el rendimiento'), 'Un primer intento: el mar y el rendimiento')
    caja(s, 1.98, 2.28, 16, 0.4, [[('SST de cada mes frente al rendimiento de Nebraska, 1981–2016, ambos sin tendencia. En amarillo, los meses del ciclo del cultivo.', SANS, 18, TXT2)]])
    s.shapes.add_picture(str(FIG12), Inches(1.98), Inches(2.8), width=Inches(16.04))
    caja(s, 1.98, 9.5, 16, 0.5, [[('Indicios, no mecanismo: ', SANSB, 18, TXT),
                                  ('una mancha roja persistente en el Pacífico nororiental, pero sin decir qué le pasó al cultivo ni en qué fase.', SANS, 18, TXT2)]])
    enlaces(s, 10.12, [('NOAA OISST v2.1', 'https://www.psl.noaa.gov/data/gridded/data.noaa.oisst.v2.highres.html'),
                       ('GDHY (Iizumi y Sakai, 2020)', 'https://doi.org/10.1038/s41597-020-0433-7'), ('maize_correlacion_vectorizada.h5', None)])
    s.notes_slide.notes_text_frame.text = (
        'Exploración inicial (antecedente). Fuente de los mapas: D:/maize_correlacion_vectorizada.h5, fila 9430 (píxel 191325). '
        'Cada panel es un mes calendario del mismo año de la cosecha; SST NOAA OISST v2.1 mensual sin tendencia; rendimiento GDHY sin tendencia. '
        'Figura: scripts/presentacion/figura_sst_12meses.py. Rojo: SST más cálida con mayor rendimiento; azul: lo contrario.\n'
        'Lectura: mancha roja persistente en el Pacífico nororiental (frente a California y México) de abril a diciembre; la caja Niño 3.4 casi no aparece. '
        'Octubre a diciembre son posteriores a la cosecha (septiembre): no pueden causar el rendimiento.\n'
        'PRECAUCIÓN sobre las magnitudes: en el H5 la desviación estándar de r es 0,08–0,11, cuando una correlación de Pearson con 36 años debería '
        'rondar 0,17 por puro azar. Al recalcular con el archivo de SST disponible (pixel_tipico_sst.py, sst_20261101_111241) el patrón coincide '
        '(r entre mapas 0,86–0,90), pero el H5 tiene aproximadamente la mitad de la magnitud (H5 ≈ 0,43–0,53 × r recalculado). Por eso no se usa '
        'el umbral |r| ≥ 0,33 sobre estos mapas. Antes de citar valores del H5 hay que entender cómo se calculó (correlacion_masiva.py usaba un archivo '
        '…_fixed.nc que ya no está; posible suavizado o agregación). El patrón se puede usar como indicio; las magnitudes, no.')
    nombrar(s, n0)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sst', required=True)
    ap.add_argument('--salida', default=str(PPT))
    a = ap.parse_args()
    cal = pd.read_csv(CAL)
    cat = pd.read_excel(CATALOGO, sheet_name='Catálogo fases')
    cic = {c: cal[cal.crop == c].drop_duplicates(['lat', 'lon']).cycle_days.quantile([.1, .5, .9]).values for c, _, _ in CULTIVOS}
    prs = Presentation(PPT)
    s09(prs); s10(prs); s11(prs, cat, cic); s12(prs, cat); s14(prs, cal); s15(prs, a.sst)
    renumerar(prs)
    prs.save(a.salida); print('guardado', a.salida)


if __name__ == '__main__':
    main()
