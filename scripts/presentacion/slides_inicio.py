"""Diapositivas 3 (Objetivos), 4 (La pregunta) y 6 (Primero, los datos) con el código CMYK de la PPT.

Cian = clima, amarillo = cultivo, magenta = seguro, sobre fondo K. Conserva título, subrayado y número de página de cada
diapositiva y redibuja el resto (formas IN_*). Reejecutable.
Uso (con el .venv del pipeline):  python slides_inicio.py [--salida ruta.pptx]
"""
import argparse

from pptx import Presentation
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

from slides_pixel_tipico import PPT, TXT, TXT2, SRC, LINE, CIAN, MAG, PANEL, SERIF, SANS, SANSB, caja, rect
from slide_tesis import AMARILLO


def por_titulo(prs, *titulos):
    """Diapositiva cuyo cuadro de título (y≈0,82) coincide con alguno de los títulos dados."""
    for sl in prs.slides:
        for sh in sl.shapes:
            if sh.has_text_frame and abs(sh.top / 914400 - 0.82) < .06 and sh.text_frame.text.strip() in titulos:
                return sl
    raise ValueError(f'No encontré la diapositiva {titulos}')


def poner_titulo(s, texto):
    sh = next(sh for sh in s.shapes if sh.has_text_frame and abs(sh.top / 914400 - 0.82) < .06)
    runs = sh.text_frame.paragraphs[0].runs
    runs[0].text = texto
    for r in runs[1:]: r.text = ''


def limpiar(s):
    """Deja solo título (y≈0,82), subrayado (y≈1,64–1,67) y número de página (x≈18,12)."""
    n0 = 0
    for sh in list(s.shapes):
        x, y = sh.left / 914400, sh.top / 914400
        conservar = abs(y - 0.82) < .05 or (1.6 < y < 1.7 and sh.width / 914400 < 1.3) or abs(x - 18.12) < .05
        if not conservar:
            sh._element.getparent().remove(sh._element)
        else:
            n0 += 1
    return n0


def nombrar(s, n0):
    for k, sh in enumerate(list(s.shapes)[n0:]):
        sh.name = f'IN_{k:02d}'


def objetivos(s):
    n0 = limpiar(s)
    rect(s, 1.98, 2.3, 16.04, 2.25, PANEL)
    rect(s, 1.98, 2.3, 0.07, 2.25, TXT)
    caja(s, 2.4, 2.52, 15, 0.35, [[('OBJETIVO GENERAL', SANSB, 15, SRC)]])
    caja(s, 2.4, 2.95, 15.3, 1.5, [[('Caracterizar la relación entre la ', SANS, 23, TXT), ('variabilidad climática global', SANSB, 23, CIAN),
                                     (' y el ', SANS, 23, TXT), ('rendimiento de cereales', SANSB, 23, AMARILLO),
                                     (' para identificar umbrales climáticos aplicables al desarrollo de ', SANS, 23, TXT),
                                     ('seguros paramétricos', SANSB, 23, MAG), (' agrícolas orientados a fortalecer la seguridad alimentaria.', SANS, 23, TXT)]])
    especificos = [
        ('01', 'Clima: ENSO y MJO', CIAN,
         'Cuantificar la variabilidad espacio temporal asociada al ENSO y la MJO con relación al rendimiento de maíz, arroz, trigo y soya a escala global.'),
        ('02', 'Cultivo: calendario y fases', AMARILLO,
         'Integrar las variables climáticas críticas de los cultivos con un calendario fenológico global típico, segmentado por intervalos latitudinales, para identificar las fases del desarrollo más sensibles a las alteraciones asociadas al ENSO y la MJO.'),
        ('03', 'Seguro: umbrales', MAG,
         'Identificar umbrales climáticos asociados a ENSO/MJO y anomalías de rendimiento, como insumo para estructuración de seguros paramétricos agrícolas.')]
    caja(s, 1.98, 4.85, 15, 0.35, [[('OBJETIVOS ESPECÍFICOS', SANSB, 15, SRC)]])
    w, gap, y0, h = 5.08, 0.4, 5.35, 4.35
    for i, (n, tag, color, texto) in enumerate(especificos):
        x = 1.98 + i * (w + gap)
        rect(s, x, y0, w, h, PANEL); rect(s, x, y0, w, 0.07, color)
        caja(s, x + 0.35, y0 + 0.3, 1.3, 0.8, [[(n, SERIF, 40, color)]])
        caja(s, x + 1.45, y0 + 0.47, w - 1.7, 0.5, [[(tag, SANSB, 19, TXT)]])
        caja(s, x + 0.35, y0 + 1.3, w - 0.7, 2.9, [[(texto, SANS, 18, TXT2)]])
    nombrar(s, n0)


def pregunta(s):
    n0 = limpiar(s)
    caja(s, 1.98, 2.28, 16, 0.4, [[('Una pregunta, cuatro eslabones. Si uno se rompe, el seguro no tiene base.', SANS, 19.5, TXT2)]])
    caja(s, 1.98, 2.95, 16.04, 1.6, [[('¿', SERIF, 32, TXT), ('ONI y MJO', SERIF, 32, CIAN),
                                       (' informan sobre el calor y la sequía en las ', SERIF, 32, TXT),
                                       ('fases sensibles del cultivo', SERIF, 32, AMARILLO),
                                       (', y esas amenazas explican ', SERIF, 32, TXT), ('caídas del rendimiento', SERIF, 32, AMARILLO),
                                       ('?', SERIF, 32, TXT)]])
    pasos = [('01 · CLIMA → AMENAZA', '¿Un Niño o una Niña cambian la probabilidad de calor o sequía en una fase del cultivo?',
              'ONI · ERA5-Land · calendario', CIAN),
             ('02 · MJO', '¿La MJO agrega información a lo que ya dice ONI?', 'RMM diario · ONI', CIAN),
             ('03 · AMENAZA → RENDIMIENTO', '¿Más calor o sequía en esa fase coincide con menos rendimiento?',
              'Amenazas por fase · GDHY, ambos sin tendencia', AMARILLO),
             ('04 · SEGURO', '¿Ese vínculo sirve como disparador de pago, y con qué riesgo de base?',
              'Pagos simulados frente a pérdidas', MAG)]
    x0, w, gap, y0, h = 1.98, 3.6, 0.547, 4.85, 3.55
    for i, (eti, q, datos, color) in enumerate(pasos):
        x = x0 + i * (w + gap)
        rect(s, x, y0, w, h, PANEL); rect(s, x, y0, w, 0.07, color)
        caja(s, x + 0.3, y0 + 0.35, w - 0.5, 0.35, [[(eti, SANSB, 14, color)]])
        caja(s, x + 0.3, y0 + 0.85, w - 0.6, 1.9, [[(q, SANSB, 19, TXT)]])
        caja(s, x + 0.3, y0 + 2.75, w - 0.6, 0.7, [[('Datos: ', SANSB, 14, SRC), (datos, SANS, 14, SRC)]])
        if i < 3:
            caja(s, x + w, y0 + h / 2 - 0.3, gap, 0.6, [[('→', SANS, 36, CIAN if i < 2 else MAG)]],
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    caja(s, 1.98, 8.75, 16, 0.5, [[('El orden importa: ', SANSB, 21, TXT),
                                   ('el seguro (04) solo tiene base si se sostienen los eslabones 01 y 03.', SANS, 21, TXT2)]])
    caja(s, 1.98, 10.05, 15.6, 0.4, [[('Pregunta acordada en el relato de la tesis (RELATO_ACUERDOS_TESIS, oct. 2026). Cadena: índices climáticos → exposición por fase → rendimiento → índice paramétrico.', SANS, 13, SRC)]])
    nombrar(s, n0)


DATOS = [  # (dato, color, qué mide, espacio, tiempo, tendencia)
    ('Rendimiento GDHY', AMARILLO, 'Maíz, t/ha', '0,5° (≈ 55 km)', 'Anual, año de cosecha',
     'Se quita: una recta por píxel. La mejora tecnológica no es clima.'),
    ('ERA5-Land', CIAN, 'Tmax (calor, EDD29) · Tmin · lluvia (MAT, sequía)', '0,1° (≈ 9 km) → 0,5°', 'Diario',
     'Umbral sobre el dato diario real; luego sin tendencia la serie anual de cada fase.'),
    ('Derivadas', CIAN, 'ETP Hargreaves → P − ETP (sequía < Q1) · EDD29', '0,1° → 0,5°', 'Diario, sumado por fase',
     'Sin tendencia la serie anual de cada fase, igual que el rendimiento.'),
    ('ONI', CIAN, 'Anomalía de SST en Niño 3.4', 'Niño 3.4: un solo valor', 'Mensual (media móvil 3 meses)',
     'Ya sin tendencia: base climática de 30 años que se actualiza.'),
    ('MJO (RMM)', CIAN, 'Fase 1–8 y amplitud', 'Un valor para el trópico', 'Diario',
     'Sin tendencia por construcción: resta el ciclo anual y la media de 120 días.'),
    ('SST (OISST v2.1)', CIAN, 'Temperatura superficial del mar', '0,25° → 0,5°', 'Diario → mensual',
     'Recta ajustada en 1981–2025; rehecha en 1981–2016, r cambia < 0,04.'),
    ('Calendario GGCMI', AMARILLO, 'Siembra, fases y madurez', '0,5°', 'Fijo: un calendario típico',
     'No aplica: el mismo para todos los años.')]


def datos(s):
    n0 = limpiar(s)
    caja(s, 1.98, 2.28, 16, 0.4, [[('1981–2016 · hasta 36 cosechas por píxel · lo que se correlaciona va sin tendencia', SANS, 19.5, TXT2)]])
    cols = [(1.98, 2.75, 'Dato'), (4.85, 3.2, 'Qué mide'), (8.2, 2.9, 'Resolución espacial'), (11.25, 2.45, 'Resolución temporal'),
            (13.85, 4.17, 'Tendencia')]
    yh = 3.05
    for x, w, t in cols:
        caja(s, x, yh, w, 0.35, [[(t, SANSB, 14, SRC)]])
    rect(s, 1.98, yh + 0.42, 16.04, 0.012, '334155')
    paso = 0.75
    for i, (dato, color, que, esp, tiem, tend) in enumerate(DATOS):
        y = yh + 0.6 + i * paso
        rect(s, 1.98, y + 0.07, 0.2, 0.2, color)
        caja(s, 2.3, y, 2.5, 0.7, [[(dato, SANSB, 15, TXT)]])
        caja(s, 4.85, y, 3.2, 0.7, [[(que, SANS, 14, TXT2)]])
        caja(s, 8.2, y, 2.9, 0.7, [[(esp, SANS, 14, TXT2)]])
        caja(s, 11.25, y, 2.45, 0.7, [[(tiem, SANS, 14, TXT2)]])
        caja(s, 13.85, y, 4.17, 0.7, [[(tend, SANS, 14, TXT if i < 3 else TXT2)]])
        rect(s, 1.98, y + paso - 0.1, 16.04, 0.01, LINE)
    caja(s, 1.98, 9.0, 16.04, 0.5, [[('Por qué sin tendencia: ', SANSB, 19, TXT),
                                      ('una tendencia compartida (tecnología, calentamiento) parecería clima sin serlo.', SANS, 19, TXT2)]])
    caja(s, 1.98, 9.52, 16.04, 0.4, [[('GDHY alineado: ', SANSB, 14, TXT2),
                                      ('v1.2 (1981–2010, satélite GIMMS3g) + v1.3 (2011–2016, MODIS), ajustadas para que la serie no salte al cambiar de satélite.', SANS, 14, SRC)]])
    caja(s, 1.98, 10.05, 15.6, 0.4, [[('Iizumi y Sakai (2020) · Muñoz-Sabater et al. (2021) · NOAA CPC ONI (ERSSTv6) · Wheeler y Hendon (2004) · NOAA OISST v2.1 (Huang et al., 2021) · GGCMI Phase 3 (Jägermeyr et al., 2021).', SANS, 13, SRC)]])
    s.notes_slide.notes_text_frame.text = (
        'Resolución y tratamiento de la tendencia por fuente (decisión del 30 oct 2026: todo lo que se correlaciona va sin tendencia).\n'
        '- GDHY v1.2+v1.3 (Iizumi y Sakai, 2020, Sci Data 7:97): rendimiento anual por año de cosecha, malla 0,5°. Se quita una recta por píxel (1981–2016); en Nebraska la pendiente es +0,14 t/ha por año.\n'
        '- ERA5-Land diario agregado (ECMWF/ERA5_LAND/DAILY_AGGR, Muñoz-Sabater et al., 2021): 0,1°. Los umbrales (p. ej., Tmax ≥ 34 °C) se aplican al valor diario observado, porque la planta responde a la temperatura real. Luego cada serie anual por fase (episodios, EDD29, P − ETP) se queda sin tendencia con la misma recta que el rendimiento.\n'
        '- ONI (NOAA CPC): media móvil de 3 meses de la anomalía de SST en Niño 3.4, calculada frente a periodos base de 30 años centrados que se actualizan cada 5 años; por eso no arrastra el calentamiento de largo plazo.\n'
        '- MJO, índice RMM (Wheeler y Hendon, 2004): diario; antes de proyectar se resta el ciclo anual y la media de los 120 días previos, lo que elimina la variabilidad interanual y la tendencia.\n'
        '- GDHY v1.2 + v1.3: la v1.2 cubre 1981–2011 (satélite GIMMS3g); la v1.3, 2000–2016 (MODIS). La versión alineada usa la v1.2 hasta 2010 y la v1.3 para 2011–2016, ajustada para que la serie no salte (Iizumi y Sakai, 2020).\n'
        '- Derivadas: ETP de Hargreaves (FAO-56 ec. 52) con Tmax, Tmin y radiación extraterrestre por latitud y día; P − ETP sumado en la fase; sequía si queda bajo el primer cuartil 1981–2016 del píxel. EDD29 = Σ max(0, Tmax − 29 °C). OJO: la tabla maestra v2 menciona ETP Penman-Monteith, pero el cálculo ejecutado usa Hargreaves (maize_gee_variables_v2.py).\n'
        '- SST: NOAA OISST v2.1 diaria a 0,25° (01_Data/SST), llevada a mensual 0,5° y sin tendencia en SST_monthly_detrended_1981_2025_0p5deg35.nc; la recta se ajustó en 1981–2025. Rehacerla en 1981–2016 para Nebraska cambia r en mediana 0,001 (p95 < 0,04): pixel_tipico/sst_20261101_111241. El H5 de correlaciones (D:) se calculó con otro archivo (..._fixed.nc) que ya no está en disco: reproduce el patrón (r entre mapas 0,86–0,90) pero no los valores exactos.\n'
        '- Calendario GGCMI Phase 3 v1.01 (Jägermeyr et al., 2021) + plantilla del proyecto v4: un calendario típico por píxel, igual todos los años.')
    nombrar(s, n0)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--salida', default=str(PPT))
    a = ap.parse_args()
    prs = Presentation(PPT)
    objetivos(por_titulo(prs, 'Objetivos')); pregunta(por_titulo(prs, 'La pregunta')); datos(por_titulo(prs, 'Primero, los datos'))
    prs.save(a.salida); print('guardado', a.salida)


if __name__ == '__main__':
    main()
