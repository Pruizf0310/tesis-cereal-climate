"""Bloque de amenazas (diapositivas 17–21): de la literatura a las reglas, tipos de evidencia, matriz de los cuatro cultivos,
amenazas del píxel de Nebraska y sustento de los umbrales de maíz.

Busca cada diapositiva por su título (viejo o nuevo), cambia el título, conserva subrayado y número, y redibuja.
Datos: reglas_24_fases_vigentes.csv, tabla_maestra_v2_maiz.xlsx, REVISION_HUMANA_…xlsx (hoja «Auditoría web»),
calendario_seis_fases_secano.csv. Uso (con el .venv del pipeline):  python slides_amenazas.py [--salida ruta.pptx]
"""
import argparse
from pathlib import Path

import pandas as pd
from pptx import Presentation
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches

from slides_pixel_tipico import (PPT, BG, TXT, TXT2, SRC, LINE, CIAN, MAG, PANEL, SERIF, SANS, SANSB, FASE_COLOR,
                                 caja, rect, renumerar, rgb)
from slide_tesis import AMARILLO
from slides_inicio import limpiar, nombrar
from slides_calendario import preparar, enlaces, REP_COLOR

REPO = Path(__file__).resolve().parents[2]
AUDIT = REPO / 'metadata/reviewed_sources/REVISION_HUMANA_fases_macro_completada_SOLO_3_COLUMNAS.xlsx'
CALOR, FRIO, AGUA = 'E5484D', '818CF8', CIAN
FAMILIAS = [  # (nombre, color, categorías de la hoja «Auditoría web», ejemplo, cómo se usa)
    ('Umbral verificado', AMARILLO,
     ['Verified duration-response threshold', 'Verified physiological threshold', 'Verified operational threshold',
      'Verified experimental threshold', 'Genotype-dependent operational threshold'],
     'Li et al. (2025): Tmax de 32,9 a 34,8 °C según la etapa, estimada con daños reales.', 'Entra como umbral'),
    ('Modelo o parámetro', CIAN, ['Modeled threshold', 'Modeled threshold — provisional duration', 'Modeled cardinal parameter'],
     'Deryng et al. (2014): Teff > 35 °C, límite del modelo de cultivo.', 'Punto de partida'),
    ('Tratamiento experimental', MAG,
     ['Damaging experimental treatment', 'Damaging field treatment', 'Damaging two-year experimental treatment',
      'Damaging experimental treatment with temperature gradient', 'Tratamiento perjudicial; umbral no establecido',
      'Secondary-source treatment'],
     'Barber et al. (2017): 35/30 °C en embuche bajó la semilla, pero no es el límite de tolerancia.', 'Con cautela'),
    ('Asociación o indicador regional', '94A3B8', ['Seasonal observational association', 'Regional indicator'],
     'Schauberger et al. (2017): cada día > 30 °C se asocia a menos rendimiento en EE. UU.', 'Indicador; transferir con cuidado'),
    ('Transferido o tentativo', '64748B', ['Transferred frost-damage threshold', 'Transferred candidate', 'Review-derived tentative HNT threshold'],
     'Umbrales de helada tomados de otra región o cultivo.', 'Solo sensibilidad')]


# ---------- 17 ----------
def s17(prs):
    s, n0 = preparar(prs, ('Cómo construimos las reglas de amenaza',), 'De la literatura a las amenazas')
    caja(s, 1.98, 2.28, 16, 0.4, [[('Una búsqueda dirigida por cultivo y fase, en varias rondas, que fue dejando por fuera lo que no se podía medir.', SANS, 19.5, TXT2)]])
    # izquierda: cómo se buscó
    rect(s, 1.98, 3.0, 6.6, 5.9, PANEL); rect(s, 1.98, 3.0, 0.07, 5.9, CIAN)
    caja(s, 2.35, 3.2, 6.0, 0.45, [[('Cómo se buscó', SANSB, 18, TXT)]])
    piezas = [('cultivo', AMARILLO), ('fase', AMARILLO), ('amenaza', CIAN), ('umbral', CIAN), ('impacto', AMARILLO)]
    linea = []
    for k, (p, c) in enumerate(piezas):
        linea += [(p, SANSB, 17, c)] + ([(' + ', SANS, 17, SRC)] if k < len(piezas) - 1 else [])
    caja(s, 2.35, 3.8, 6.0, 0.5, [linea])
    caja(s, 2.35, 4.45, 6.0, 0.4, [[('Por ejemplo:', SANS, 14, SRC)]])
    caja(s, 2.35, 4.8, 6.0, 0.5, [[('maize pre-silking heat stress threshold temperature', SANS, 15, TXT)]])
    pasos = [('Primera ronda: ', 'calor, frío, sequía y lluvia excesiva en los cuatro cultivos.'),
             ('Rondas siguientes: ', 'solo los vacíos de cada cultivo y fase.'),
             ('Cada valor quedó ', 'con su fase, exposición, impacto y página del artículo.')]
    for k, (cab, txt) in enumerate(pasos):
        caja(s, 2.35, 5.65 + k * 1.0, 6.0, 0.9, [[(f'{k + 1}. ', SANSB, 15, CIAN), (cab, SANSB, 15, TXT), (txt, SANS, 15, TXT2)]])
    # derecha: embudo
    etapas = [('63', 'filas de evidencia', '27 fuentes de la primera matriz'),
              ('35', 'reglas con definición exacta', 'cada fragmento verificado contra el PDF'),
              ('25', 'medibles con datos diarios', '10 piden datos sin serie global'),
              ('24', 'reglas v1', 'una por cultivo y fase'),
              ('12', 'reglas de maíz v2', 'se suman sequía y calor continuo')]
    x0, y0, alto = 8.95, 3.0, 1.02
    for i, (n, cab, txt) in enumerate(etapas):
        w = 9.07 - i * 0.5; x = x0 + i * 0.25; y = y0 + i * 1.22
        ult = i == 4
        rect(s, x, y, w, alto, '3A3410' if ult else PANEL); rect(s, x, y, 0.07, alto, AMARILLO if ult else CIAN)
        caja(s, x + 0.25, y, 1.25, alto, [[(n, SERIF, 30, AMARILLO if ult else CIAN)]], anchor=MSO_ANCHOR.MIDDLE)
        caja(s, x + 1.55, y, w - 1.7, alto, [[(cab, SANSB, 16, TXT)], [(txt, SANS, 14, TXT2)]], anchor=MSO_ANCHOR.MIDDLE)
    caja(s, 1.98, 9.2, 16, 0.75, [[('No es una revisión sistemática: ', SANSB, 15, MAG),
                                   ('no hubo una ecuación única ni un conteo de resultados por base. Lo que sí hay es trazabilidad de cada valor hasta su página.', SANS, 15, TXT2)]])
    enlaces(s, 10.12, [('Auditoría de fuentes (Excel)', None), ('reglas_24_fases_vigentes.csv', None), ('tabla_maestra_v2_maiz.xlsx', None)], prefijo='Trazabilidad: ')
    s.notes_slide.notes_text_frame.text = (
        'Cómo se buscó (reconstrucción del 2 nov 2026: Documents/ChatGPT/Tesis/BUSQUEDA_LITERATURA_AMENAZAS_Y_UMBRALES.md):\n'
        '- Encargo inicial: umbrales críticos de estrés abiótico en arroz, trigo, maíz y soya; calor diurno y nocturno, frío y helada, sequía y lluvia excesiva; '
        'fase real (BBCH, Zadoks), umbral numérico, duración, impacto y trazabilidad. Fases prioritarias: antesis, llenado y emergencia.\n'
        '- Lógica de búsqueda: cultivo + fase + amenaza + umbral + impacto. Términos: threshold, critical temperature, breakpoint, heat stress, high night temperature, '
        'cold, frost, drought, soil moisture, excess rainfall, waterlogging, yield, seed set, germination, emergence, anthesis, grain filling.\n'
        '- Las cadenas por cultivo y fase (p. ej., «maize pre-silking heat stress threshold temperature») se documentaron como PROPUESTAS para llenar vacíos; '
        'no está confirmado que todas se ejecutaran literalmente.\n'
        '- Límite que hay que declarar: no hay registro de bases consultadas, fechas, filtros, ecuación booleana única ni conteos de resultados y exclusiones. '
        'Es una revisión dirigida e iterativa, no sistemática.\n'
        'Embudo con conteos verificados:\n'
        '- 27 fuentes y 63 filas en la hoja «Auditoría web» de metadata/reviewed_sources/REVISION_HUMANA_fases_macro_completada_SOLO_3_COLUMNAS.xlsx. '
        '63 es una etapa del archivo, no el total: hubo ampliaciones posteriores para vacíos (de ahí fuentes como Yoshida 1981, Deryng et al. 2014 o Shroyer et al. 1995).\n'
        '- 11 filas en naranja no entraron como asignación activa; quedaron 47 asignaciones cultivo–fase y 35 reglas distintas (docs/regional_workflow_v4.md).\n'
        '- De esas 35, 25 se calculan con ERA5-Land y 10 requieren una variable externa: potencial matricial del suelo, sumersión, inundación, profundidad de lámina, '
        'humedad frente a un control, temperatura mínima del dosel y diferencia nocturna frente a control.\n'
        '- v1: 24 reglas, una por cultivo y fase (03_Resultados/Agroclima/vigente/amenazas/reglas_24_fases_vigentes.csv).\n'
        '- Maíz v2 (23 oct 2026): 12 reglas, 8 principales y 4 de sensibilidad. Se sumaron la sequía (P − ETP < Q1) en EST, VEG, FLO y FIL, el calor continuo EDD29 '
        'en FLO, REP y FIL, y el evento seco-cálido compuesto como sensibilidad. Desde v2 una fase de maíz tiene de una a tres reglas (cuatro con el evento compuesto de sensibilidad); '
        'arroz, soya y trigo siguen en v1 (una por fase).')
    nombrar(s, n0)


# ---------- 18 ----------
def s18(prs):
    s, n0 = preparar(prs, ('La decisión: una amenaza por fase',), 'No todo valor publicado es un umbral')
    a = pd.read_excel(AUDIT, sheet_name='Auditoría web', header=3)
    cuenta = a['Categoría de evidencia'].value_counts()
    caja(s, 1.98, 2.28, 16, 0.4, [[('Muchos valores eran tratamientos u observaciones: hubo un resultado con ese valor, pero no es el punto de daño ni de tolerancia.', SANS, 18, TXT2)]])
    total = len(a); y = 3.05
    caja(s, 1.98, y, 4, 0.35, [[('Tipo de evidencia', SANSB, 14, SRC)]])
    caja(s, 5.5, y, 1.0, 0.35, [[(f'de {total}', SANSB, 14, SRC)]], align=PP_ALIGN.RIGHT)
    caja(s, 7.5, y, 7.4, 0.35, [[('Ejemplo', SANSB, 14, SRC)]])
    caja(s, 15.2, y, 2.8, 0.35, [[('Cómo se usa', SANSB, 14, SRC)]])
    for i, (nom, color, cats, ej, uso) in enumerate(FAMILIAS):
        n = int(sum(cuenta.get(c, 0) for c in cats)); yy = y + 0.5 + i * 0.98
        rect(s, 1.98, yy, 0.12, 0.85, color)
        caja(s, 2.3, yy, 3.8, 0.85, [[(nom, SANSB, 17, TXT)]], anchor=MSO_ANCHOR.MIDDLE)
        caja(s, 5.75, yy, 0.75, 0.85, [[(str(n), SERIF, 24, color)]], align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
        rect(s, 6.6, yy + 0.29, 0.75 * n / 19, 0.28, color)
        caja(s, 7.5, yy, 7.4, 0.85, [[(ej, SANS, 14.5, TXT2)]], anchor=MSO_ANCHOR.MIDDLE)
        caja(s, 15.2, yy, 2.8, 0.85, [[(uso, SANSB, 14.5, color if color not in ('64748B',) else TXT2)]], anchor=MSO_ANCHOR.MIDDLE)
        rect(s, 1.98, yy + 0.91, 16.04, 0.01, LINE)
    rect(s, 1.98, 8.6, 16.04, 1.3, PANEL); rect(s, 1.98, 8.6, 0.07, 1.3, MAG)
    caja(s, 2.35, 8.75, 15.5, 1.05, [[('Para entrar, una regla debe cumplir seis criterios: ', SANSB, 15, TXT),
                                      ('mecanismo en esa fase con cita y página; variable global equivalente (ERA5-Land); nivel de evidencia declarado; '
                                       'que varíe entre años; una principal por fase y familia (las demás, sensibilidad); unidad comparable.', SANS, 15, TXT2)]])
    s.notes_slide.notes_text_frame.text = (
        'Conteo sobre las 63 filas de la hoja «Auditoría web» (columna «Categoría de evidencia»), agrupadas en cinco familias para la exposición:\n'
        '- Umbral verificado (16): duración–respuesta 9, operativo dependiente del genotipo 4, fisiológico 1, operativo 1, experimental verificado 1.\n'
        '- Modelo o parámetro (6): umbral modelado 3, modelado con duración provisional 2, parámetro cardinal 1.\n'
        '- Tratamiento experimental (19): tratamiento perjudicial 10, de campo 3, de dos años 2, con gradiente 1, sin umbral establecido 1, de fuente secundaria 2.\n'
        '- Asociación o indicador regional (16): asociación observacional estacional 8, indicador regional 8.\n'
        '- Transferido o tentativo (6): umbral de helada transferido 3, candidato transferido 2, tentativo derivado de revisión 1.\n'
        'La agrupación en familias es de esta presentación; las categorías originales están en el Excel. Escala de la tabla v2 (criterio C3): '
        'a = umbral estimado con datos de campo o rendimiento; b = parámetro de modelo o índice; c = tratamiento experimental; d = índice estandarizado o percentil. '
        'Para b y c el valor es punto de partida, no verdad.\n'
        'Criterios C1–C6 (hoja «Criterios» de tabla_maestra_v2_maiz.xlsx): C1 mecanismo fisiológico con cita y página; C2 variable global, consultable y equivalente; '
        'C3 nivel de evidencia declarado; C4 variabilidad entre años; C5 una principal por fase y familia; C6 unidad comparable.\n'
        'Ejemplo de algo que no era amenaza: Alsajri (2018) da una temperatura cardinal de germinación, no un umbral de mortalidad o pérdida.')
    nombrar(s, n0)


# ---------- 19 ----------
SEQ, EDD = ('a', 'Sequía P − ETP < Q1'), ('c', 'EDD29 °C·día')
MATRIZ = {  # cultivo: [(fase, familia, texto)]; en maíz v2 una fase puede tener varias reglas: [(familia, texto), …]
    'Maíz': [('EST', [('c', 'Calor ≥ 34,0 °C ≥ 2 d'), SEQ]), ('VEG', [('c', 'Calor ≥ 34,6 °C ≥ 2 d'), SEQ]),
             ('FLO', [('c', 'Calor ≥ 33,7 °C ≥ 2 d'), SEQ, EDD]), ('REP-pos', [('c', 'Calor ≥ 33,7 °C ≥ 2 d'), EDD]),
             ('FIL', [('c', 'Calor ≥ 32,9 °C ≥ 2 d'), SEQ, EDD]), ('MAT', [('a', 'Lluvia P > 10 mm/día')])],
    'Arroz': [('EST', 'c', 'Calor Tmedia > 35 °C'), ('VEG', 'c', 'Calor Tmax > 36 °C ≥ 3 d'), ('FLO', 'c', 'Calor Tmedia ≥ 33 °C'),
              ('REP-pre', 'c', 'Calor Tmedia ≥ 33 °C'), ('FIL', 'c', 'Calor Tmedia ≥ 33 °C'), ('MAT', 'c', 'Calor Tmedia > 30 °C')],
    'Soya': [('EST', 'f', 'Helada Tmin < 0 °C'), ('VEG', 'c', 'Calor ≥ 45 °C 4 h/d × 7 d'), ('FLO', 'c', 'Calor Teff > 35 °C'),
             ('REP-pos', 'c', 'Calor Teff > 35 °C'), ('FIL', 'a', 'Lluvia > 100 mm (R6–R8)'), ('MAT', 'a', 'Lluvia > 100 mm (R6–R8)')],
    'Trigo': [('EST', 'f', 'Frío Tmedia < 2 °C ≥ 3 d'), ('VEG', 'f', 'Helada ≤ −4,4 °C 2 h'), ('FLO', 'f', 'Helada ≤ −1,1 °C 2 h'),
              ('REP-pre', 'f', 'Helada ≤ −1,1 °C 2 h'), ('FIL', 'f', 'Helada ≤ −2,2 °C 2 h'), ('MAT', 'a', 'Lluvia ≥ 25 mm/d 2 d')]}
FAM = {'c': CALOR, 'f': FRIO, 'a': AGUA}


def s19(prs):
    s, n0 = preparar(prs, ('De la literatura a reglas reproducibles',), 'Amenazas y umbrales por cultivo y fase')
    caja(s, 1.98, 2.28, 16, 0.4, [[('v1 dejó una regla por cultivo y fase. En maíz (v2) se sumaron la sequía y el calor continuo: una fase puede tener hasta tres.', SANS, 18, TXT2)]])
    cols = ['EST', 'VEG', 'FLO', 'REP', 'FIL', 'MAT']
    x0, wc, y0 = 3.75, 2.36, 3.0
    for j, f in enumerate(cols):
        x = x0 + j * wc
        rect(s, x, y0, wc - 0.06, 0.42, FASE_COLOR[f] if f != 'REP' else FASE_COLOR['REP'])
        caja(s, x, y0, wc - 0.06, 0.42, [[(f if f != 'REP' else 'REP (pre / pos)', SANSB, 14, BG)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    y = y0 + 0.6
    for cultivo, celdas in MATRIZ.items():
        maiz = cultivo == 'Maíz'; alto = 1.6 if maiz else 1.0
        caja(s, 1.98, y, 1.7, alto, [[(cultivo, SANSB, 19, AMARILLO)], [('v2' if maiz else 'v1', SANS, 12, SRC)]], anchor=MSO_ANCHOR.MIDDLE)
        orden = {c[0]: (c[1] if maiz else [(c[1], c[2])]) for c in celdas}
        for j, f in enumerate(cols):
            clave = next(k for k in orden if k.startswith(f))
            reglas = orden[clave]; x = x0 + j * wc
            rect(s, x, y, wc - 0.06, alto, PANEL)
            if len(reglas) == 1: rect(s, x, y, 0.06, alto, FAM[reglas[0][0]])
            partes = [[('▌' if len(reglas) > 1 else '', SANSB, 13.5, FAM[fam]), (txt, SANS, 13.5 if maiz else 13, TXT)] for fam, txt in reglas]
            if f == 'REP': partes.insert(0, [(clave, SANSB, 11, REP_COLOR[clave])])
            caja(s, x + 0.15, y + 0.05, wc - 0.3, alto - 0.1, partes, anchor=MSO_ANCHOR.MIDDLE)
        y += alto + 0.15
    caja(s, 1.98, 9.0, 16, 0.4, [[('▌', SANSB, 15, CALOR), (' calor   ', SANS, 14, TXT2), ('▌', SANSB, 15, FRIO), (' frío o helada   ', SANS, 14, TXT2),
                                  ('▌', SANSB, 15, AGUA), (' agua: lluvia o sequía', SANS, 14, TXT2), ('     d = días consecutivos; h = horas', SANS, 14, SRC)]])
    caja(s, 1.98, 9.5, 16, 0.45, [[('Arroz, soya y trigo siguen con una sola regla por fase: ', SANSB, 14, TXT),
                                   ('la sequía todavía no se ha llevado a esos cultivos.', SANS, 14, TXT2)]])
    enlaces(s, 10.12, [('reglas_24_fases_vigentes.csv', None), ('tabla_maestra_v2_maiz.xlsx', None)], prefijo='Tablas: ')
    s.notes_slide.notes_text_frame.text = (
        'Fuente: 03_Resultados/Agroclima/vigente/amenazas/reglas_24_fases_vigentes.csv (v1: 24 reglas, una por cultivo y fase) y, para maíz, la tabla v2 '
        '(12 reglas: FIL ajustado de 32,7 a 32,9 °C; sequía P − ETP < Q1 nueva en EST, VEG, FLO y FIL; EDD29 en FLO, REP y FIL). '
        'Reglas de maíz por fase: EST 2, VEG 2, FLO 3, REP-pos 2, FIL 3, MAT 1; además, el evento seco-cálido compuesto (sensibilidad) cubre FLO, REP y FIL, '
        'de modo que con él una fase llega a cuatro. El criterio C5 es una regla principal por fase Y por familia, no una por fase.\n'
        'Fuentes por cultivo: maíz Li et al. 2025 (calor), Le Roux et al. 2024 (sequía), Ortega Gómez et al. 2019 (lluvia en MAT); arroz Yoshida 1981, Jiang et al. 2023, '
        'Sun et al. 2025; soya Mourtzinis et al. 2019, Herritt y Fritschi 2020 (experimental), Deryng et al. 2014 (modelo), Weerasekara et al. 2021; '
        'trigo Le Roux et al. 2024, Shroyer et al. 1995 (K-State C646), Ellis y Yadav 2016 (experimental).\n'
        'Teff = (Tmedia + Tmax)/2. En arroz y trigo REP-pre va antes de FLO; en maíz y soya REP-pos va después (columna común por equivalencia).')
    nombrar(s, n0)


# ---------- 20 ----------
NEBRASKA = [('EST', '26 abr – 5 may', ('≥ 34,0 °C', False), (True,), False),
            ('VEG', '6 may – 8 jul *', ('≥ 34,6 °C', False), (True,), False),
            ('FLO', '9 – 17 jul', ('≥ 33,7 °C †', True), (True,), True),
            ('REP-pos', '18 – 27 jul', ('≥ 33,7 °C', True), None, True),
            ('FIL', '28 jul – 5 sep', ('≥ 32,9 °C', True), (True,), True),
            ('MAT', '6 – 20 sep', None, None, False)]


def s20(prs):
    s, n0 = preparar(prs, ('Qué estamos contando',), 'Las amenazas de nuestro píxel')
    caja(s, 1.98, 2.28, 16, 0.4, [[('Maíz de secano, Nebraska: de una a tres reglas por fase. Lleno = principal; contorno = sensibilidad.', SANS, 19.5, TXT2)]])
    hdr = [(1.98, 1.7, 'Fase'), (3.75, 2.6, 'Ventana'), (6.5, 3.4, 'Calor · Tmax ≥ 2 días'), (10.05, 3.2, 'Sequía · P − ETP < Q1'),
           (13.4, 2.4, 'Calor continuo · EDD29'), (15.95, 2.07, 'Lluvia · MAT')]
    for x, w, t in hdr:
        caja(s, x, 2.95, w, 0.35, [[(t, SANSB, 13.5, SRC)]])
    for i, (fase, ventana, calor, seq, edd) in enumerate(NEBRASKA):
        y = 3.45 + i * 0.86; color = REP_COLOR['REP-pos'] if fase == 'REP-pos' else FASE_COLOR[fase]
        rect(s, 1.98, y, 1.6, 0.66, color)
        caja(s, 1.98, y, 1.6, 0.66, [[(fase, SANSB, 15, BG)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        caja(s, 3.75, y, 2.6, 0.66, [[(ventana, SANS, 15, TXT2)]], anchor=MSO_ANCHOR.MIDDLE)

        def chip(x, w, texto, col, principal):
            rect(s, x, y + 0.08, w, 0.5, col if principal else None, linea=None if principal else col)
            caja(s, x, y + 0.08, w, 0.5, [[(texto, SANSB, 14, BG if principal else col)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        if calor: chip(6.5, 3.2, calor[0], CALOR, calor[1])
        if seq: chip(10.05, 3.1, 'bandera por temporada', AGUA, True)
        if edd: chip(13.4, 2.35, '°C·día sobre 29', 'F59E0B', True)
        if fase == 'MAT': chip(15.95, 2.07, 'P > 10 mm/día', AGUA, False)
    rect(s, 1.98, 8.75, 16.04, 0.012, '334155')
    caja(s, 1.98, 8.85, 16, 0.55, [[('Qué se cuenta: ', SANSB, 15, TXT),
                                    ('rachas de calor (episodios y % de días de la fase), una bandera de sequía por temporada, °C·día de calor continuo y días de lluvia. '
                                     'Lo siguiente: cada evento con su duración e intensidad.', SANS, 15, TXT2)]])
    caja(s, 1.98, 9.55, 16, 0.4, [[('* El conteo de calor de VEG usó solo V7–VT (6 jun – 8 jul).   † FLO: 34,8 °C (VT–R1) sigue por decidir.   '
                                    'También en sensibilidad: evento seco-cálido compuesto en FLO, REP-pos y FIL.', SANS, 13, SRC)]])
    enlaces(s, 10.12, [('tabla_maestra_v2_maiz.xlsx', None), ('calendario_seis_fases_secano.csv', None)], prefijo='Tablas: ')
    s.notes_slide.notes_text_frame.text = (
        'Reglas de maíz v2 aplicadas al píxel 191325 (Nebraska). Estado según la tabla v2: principales MAI-EST-SEQ, MAI-VEG-SEQ, MAI-FLO-CAL, MAI-FLO-SEQ, MAI-REP-CAL, '
        'MAI-FIL-CAL, MAI-FIL-SEQ y MAI-EDD-29 (FLO, REP, FIL); sensibilidad MAI-EST-CAL, MAI-VEG-CAL, MAI-MAT-LLU y MAI-TARDIA-SECA-CALIDA.\n'
        'Unidades (criterio C6): calor por umbral = % de días de la fase en rachas ≥ 2 d (episodios como unidad secundaria); EDD29 = Σ max(0, Tmax − 29 °C) en °C·día; '
        'sequía = P − ETP acumulado en la fase y bandera si cae bajo el primer cuartil 1981–2016 del propio píxel (ETP de Hargreaves en el cálculo ejecutado); '
        'MAT = días con P > 10 mm.\n'
        'Ventanas del calendario v4; la de VEG en el conteo de calor fue solo V7–VT (pendiente decidir). Esta diapositiva reemplaza a «Qué estamos contando».')
    nombrar(s, n0)


# ---------- 21 ----------
FUENTES_MAIZ = [
    ('Li et al. (2025)', 'European Journal of Agronomy', 'https://doi.org/10.1016/j.eja.2025.127729', 'Calor por etapa: Tmax 32,9–34,8 °C',
     'China, llanura Huang-Huai-Hai, 1980–2023; daños registrados', 'a', 'Verificar cifras en el PDF; FLO 33,7 o 34,8 °C'),
    ('Le Roux et al. (2024)', 'Scientific Reports', 'https://doi.org/10.1038/s41598-024-58826-w', 'Sequía: P − ETP bajo el primer cuartil',
     'Trigo de invierno, Francia', 'd', 'Se pasa a maíz y a Q1 por píxel: adaptación declarada'),
    ('Schlenker y Roberts (2009)', 'PNAS · y Anderson et al. (2020), GRL', 'https://doi.org/10.1073/pnas.0906865106', 'Calor continuo: EDD sobre 29 °C',
     'Condados de EE. UU., 1950–2005', 'a', 'Confirmar 29 °C en la versión final de PNAS'),
    ('Ortega Gómez et al. (2019)', 'Nova Scientia', 'https://doi.org/10.21640/ns.v11i22.1682', 'Lluvia en maduración: P > 10 mm/día',
     'Maíz de temporal, Bajo Balsas, México', 'b/d', 'La tabla dice > 10 y el resumen ≥ 10: fijar uno'),
    ('Wu et al. (2025)', 'Global and Planetary Change', 'https://doi.org/10.1016/j.gloplacha.2025.104828', 'Seco-cálido: P < p20 y T > p80',
     'China, 1961–2020', 'd', 'Sensibilidad; útil para ENSO')]


def s21(prs):
    s, n0 = preparar(prs, ('El sustento de los umbrales de maíz',), 'El sustento de los umbrales de maíz')
    caja(s, 1.98, 2.28, 16, 0.4, [[('Ninguna fuente es de Nebraska: todos los umbrales se transfieren y eso hay que decirlo.', SANS, 19.5, TXT2)]])
    hdr = [(1.98, 3.6, 'Fuente'), (5.7, 3.7, 'Qué aporta'), (9.5, 3.8, 'De dónde viene'), (13.4, 0.8, 'Nivel'), (14.35, 3.67, 'Qué falta')]
    for x, w, t in hdr:
        caja(s, x, 2.95, w, 0.35, [[(t, SANSB, 13.5, SRC)]])
    for i, (aut, rev, url, aporta, origen, nivel, falta) in enumerate(FUENTES_MAIZ):
        y = 3.45 + i * 1.08
        tb = caja(s, 1.98, y, 3.6, 0.95, [[(aut, SANSB, 16, TXT)], [(rev, SANS, 13, CIAN)]])
        tb.text_frame.paragraphs[1].runs[0].hyperlink.address = url
        caja(s, 5.7, y, 3.7, 0.95, [[(aporta, SANS, 14.5, TXT)]])
        caja(s, 9.5, y, 3.8, 0.95, [[(origen, SANS, 14, TXT2)]])
        caja(s, 13.4, y, 0.8, 0.95, [[(nivel, SERIF, 20, AMARILLO)]])
        caja(s, 14.35, y, 3.67, 0.95, [[(falta, SANS, 13.5, TXT2)]])
        rect(s, 1.98, y + 1.0, 16.04, 0.01, LINE)
    caja(s, 1.98, 9.0, 16, 0.85, [[('Nivel: ', SANSB, 14, TXT), ('a = umbral estimado con datos de campo o rendimiento · b = parámetro de modelo o índice · '
                                   'c = tratamiento experimental · d = índice estandarizado o percentil. Para b, c y d el valor es un punto de partida.', SANS, 14, TXT2)]])
    caja(s, 1.98, 10.12, 15.6, 0.35, [[('Los nombres de revista enlazan al artículo (DOI).', SANS, 13, SRC)]])
    s.notes_slide.notes_text_frame.text = (
        'Referencias completas (tabla_maestra_v2_maiz.xlsx, hoja «Maíz v2»):\n'
        '- Li, Y. et al. (2025). Identifying trigger thresholds for heat damage at different growth stages of summer maize: A case study of the Huang-Huai-Hai Plain, China. '
        'European Journal of Agronomy, 170, 127729. https://doi.org/10.1016/j.eja.2025.127729. Índice de Youden máximo en 34; 34,1; 34,6; 34,8; 33,7 y 32,9 °C para V0–VE, VE–V6, V6–VT, VT–R1, R1–R3 y R3–R6.\n'
        '- Le Roux, R. et al. (2024). Mapping the race between crop phenology and climate risks for wheat in France under climate change. Scientific Reports, 14, 8184. '
        'https://doi.org/10.1038/s41598-024-58826-w.\n'
        '- Schlenker, W. y Roberts, M. J. (2009). PNAS 106(37), 15594–15598. https://doi.org/10.1073/pnas.0906865106; Anderson, W. et al. (2020). GRL. https://doi.org/10.1029/2020GL087004.\n'
        '- Ortega Gómez, A. M. et al. (2019). Nova Scientia, 11(22), 26–52. https://doi.org/10.21640/ns.v11i22.1682.\n'
        '- Wu, X., Jiang, D. y Yang, Y. (2025). Global and Planetary Change, 251, 104828. https://doi.org/10.1016/j.gloplacha.2025.104828.\n'
        'Cambio frente a v1: FIL pasó de 32,7 a 32,9 °C (32,7 venía de una cita secundaria, Li 2025b).')
    nombrar(s, n0)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--salida', default=str(PPT))
    a = ap.parse_args()
    prs = Presentation(PPT)
    s17(prs); s18(prs); s19(prs); s20(prs); s21(prs)
    renumerar(prs)
    prs.save(a.salida); print('guardado', a.salida)


if __name__ == '__main__':
    main()
