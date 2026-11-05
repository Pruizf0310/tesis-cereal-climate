"""Diapositiva «Qué son ONI y MJO»: qué mide cada índice, su escala, y por qué ONI y no RONI, con datos reales del CPC.

Busca la diapositiva por su título (el orden de la presentación cambia), conserva título/subrayado/número y redibuja el resto.
Datos: metadata/reference/cpc_oni_roni_v6_1981_2016.csv (tablas ONI v6 y RONI v6 del CPC, descargadas el 31 oct 2026).
Al final renumera los pies de página de toda la presentación.
Uso (con el .venv del pipeline):  python slide_oni_mjo.py [--salida ruta.pptx]
"""
import argparse, math, re
from pathlib import Path

import numpy as np
import pandas as pd
from pptx import Presentation
from pptx.chart.data import XyChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

from slides_pixel_tipico import (PPT, TXT, TXT2, SRC, CIAN, MAG, PANEL, SERIF, SANS, SANSB, caja, rect, rgb,
                                 estilo_ejes, recta, renumerar, num, fuente_run)
from slides_inicio import limpiar, nombrar

DATOS = Path(__file__).resolve().parents[2] / 'metadata/reference/cpc_oni_roni_v6_1981_2016.csv'
ENLACES = [('CPC · ONI v6', 'https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/oni/v6/'),
           ('CPC · RONI', 'https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/'),
           ('CPC · intensidad ENSO', 'https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/strengths.php'),
           ('BoM · RMM', 'https://www.bom.gov.au/climate/mjo/'),
           ('Wheeler y Hendon (2004)', 'https://doi.org/10.1175/1520-0493(2004)132%3C1917:AARMMI%3E2.0.CO;2')]


FUERTE, MESES = 1.5, 3  # CPC: fuerte = |ONI| ≥ 1,5 °C en al menos 3 trimestres móviles seguidos (no es clasificación oficial)
NINO_F, NINA_F = 'E5484D', '60A5FA'


def tramos_fuertes(d):
    """Tramos de ≥ 3 meses seguidos con ONI ≥ 1,5 (Niño fuerte) o ≤ −1,5 (Niña fuerte): [(signo, [(x, oni), …]), …]."""
    out, act = [], None
    for _, r in d.iterrows():
        sg = 1 if r.oni >= FUERTE else -1 if r.oni <= -FUERTE else 0
        x = r.anio + (r.mes - .5) / 12
        if sg and act and act[0] == sg: act[1].append((x, r.oni))
        else:
            act = (sg, [(x, r.oni)]) if sg else None
            if act: out.append(act)
    return [o for o in out if len(o[1]) >= MESES]


def estadisticas(d):
    p = d[(d.anio >= 1981) & (d.anio <= 2016)]
    cat = lambda x: np.where(x >= .5, 1, np.where(x <= -.5, -1, 0))
    return dict(r=p.oni.corr(p.roni), dif=(p.roni - p.oni).mean(), misma=(cat(p.oni) == cat(p.roni)).mean(), n=len(p))


def color_enlaces(prs, color=CIAN):
    """Los enlaces del tema salían azul oscuro sobre fondo K: hlink y folHlink pasan a cian."""
    from pptx.opc.constants import RELATIONSHIP_TYPE as RT
    tema = prs.slide_master.part.part_related_by(RT.THEME)
    xml = tema.blob.decode('utf-8')
    for tag in ('hlink', 'folHlink'):
        xml = re.sub(rf'(<a:{tag}>\s*<a:srgbClr val=")[0-9A-Fa-f]{{6}}', rf'\g<1>{color}', xml)
    tema._blob = xml.encode('utf-8')


def construir(prs, d):
    s = next(sl for sl in prs.slides if any(sh.has_text_frame and sh.text_frame.text.strip() == 'Qué son ONI y MJO' for sh in sl.shapes))
    n0 = limpiar(s)
    e = estadisticas(d)
    caja(s, 1.98, 2.28, 16, 0.4, [[('Dos relojes del clima tropical: uno lento, de meses a años, y uno rápido, de días a semanas.', SANS, 19.5, TXT2)]])

    # ONI
    caja(s, 1.98, 2.95, 7.8, 0.6, [[('ONI', SERIF, 32, CIAN), ('  El Niño – La Niña', SANSB, 18, TXT)]])
    caja(s, 1.98, 3.6, 7.8, 1.0, [[('Anomalía de la temperatura del mar en Niño 3.4, media móvil de 3 meses. '
                                    'Niño ≥ +0,5 °C y Niña ≤ −0,5 °C durante 5 trimestres seguidos.', SANS, 16, TXT2)]])
    cd = XyChartData()
    for nombre, col in [('ONI', 'oni'), ('RONI', 'roni')]:
        se = cd.add_series(nombre)
        for _, r in d.iterrows(): se.add_data_point(r.anio + (r.mes - .5) / 12, r[col])
    for v in (.5, -.5, FUERTE, -FUERTE):
        se = cd.add_series(f'{v}'); se.add_data_point(1981, v); se.add_data_point(2017, v)
    tramos = tramos_fuertes(d)
    for k, (sg, pts) in enumerate(tramos):
        se = cd.add_series(f'fuerte{k}')
        for x, v in pts: se.add_data_point(x, v)
    gf = s.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS, Inches(1.75), Inches(4.65), Inches(8.1), Inches(3.05), cd)
    ch = gf.chart; ch.has_legend = False
    estilo_ejes(ch, 1981, 2017, -3, 3, 5, 1, yfmt='0;−0;0')
    recta(ch.series[0], CIAN, 2); recta(ch.series[1], TXT2, 1)
    for k in (2, 3):
        recta(ch.series[k], '475569', 1); ch.series[k].format.line.dash_style = 4
    for k, c in ((4, NINO_F), (5, NINA_F)):
        recta(ch.series[k], c, 0.75); ch.series[k].format.line.dash_style = 4
    for k, (sg, _) in enumerate(tramos):
        recta(ch.series[6 + k], NINO_F if sg > 0 else NINA_F, 3.5)
    caja(s, 2.3, 4.55, 7.5, 0.35, [[('—', SANSB, 15, CIAN), (' ONI  ', SANS, 13, TXT2), ('—', SANSB, 15, TXT2), (' RONI  ', SANS, 13, TXT2),
                                    ('━', SANSB, 15, NINO_F), (' Niño fuerte  ', SANS, 13, TXT2), ('━', SANSB, 15, NINA_F),
                                    (' Niña fuerte  (|ONI| ≥ 1,5 °C)', SANS, 13, TXT2)]])

    # MJO
    xm = 10.75
    caja(s, xm, 2.95, 7.3, 0.6, [[('MJO', SERIF, 32, CIAN), ('  Oscilación Madden–Julian', SANSB, 18, TXT)]])
    caja(s, xm, 3.6, 7.3, 1.0, [[('Pulso de nubes, lluvia y viento que recorre el trópico hacia el este en 30–60 días. '
                                  'RMM diario: fase = dónde está la convección; amplitud > 1 = activa.', SANS, 16, TXT2)]])
    cx, cy, R = 14.35, 6.4, 1.05
    anillo = s.shapes.add_shape(9, Inches(cx - .62), Inches(cy - .62), Inches(1.24), Inches(1.24))
    anillo.fill.background(); anillo.line.color.rgb = rgb('334155'); anillo.line.width = Pt(1); anillo.shadow.inherit = False
    caja(s, cx - .6, cy - .25, 1.2, 0.5, [[('débil', SANS, 12, SRC)], [('≤ 1', SANS, 12, SRC)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    for k in range(8):
        a = math.radians(202.5 + 45 * k)
        x, y = cx + R * math.cos(a), cy - R * math.sin(a)
        c = s.shapes.add_shape(9, Inches(x - .27), Inches(y - .27), Inches(.54), Inches(.54))
        c.fill.solid(); c.fill.fore_color.rgb = rgb(PANEL); c.line.color.rgb = rgb(CIAN); c.line.width = Pt(1.25); c.shadow.inherit = False
        caja(s, x - .27, y - .27, .54, .54, [[(str(k + 1), SANSB, 15, TXT)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    for texto, x, y, w, al in [('Océano Índico · 2–3', cx - 2, cy + R + .3, 4, PP_ALIGN.CENTER),
                               ('Continente Marítimo · 4–5', cx + R + .45, cy - .2, 2.3, PP_ALIGN.LEFT),
                               ('Pacífico occidental · 6–7', cx - 2, cy - R - .68, 4, PP_ALIGN.CENTER),
                               ('Hemisferio occ. y África · 8–1', cx - R - 2.75, cy - .2, 2.3, PP_ALIGN.RIGHT)]:
        caja(s, x, y, w, 0.4, [[(texto, SANS, 13, SRC)]], align=al)

    # Por qué ONI y no RONI
    y0, h = 7.95, 1.95
    rect(s, 1.98, y0, 16.04, h, PANEL); rect(s, 1.98, y0, 0.07, h, CIAN)
    caja(s, 2.35, y0 + 0.2, 6, 0.4, [[('¿Por qué ONI y no RONI?', SANSB, 19, TXT)]])
    cols = [('Qué cambia', [('RONI resta el calentamiento de todo el trópico (20° S–20° N). Desde 2026 el CPC lo usa como índice principal.', SANS, 15, TXT2)]),
            ('En nuestro periodo', [(f'1981–2016: r = {num(e["r"])}; diferencia media {num(e["dif"])} °C; '
                                     f'misma categoría en el {e["misma"] * 100:.0f} % de los meses.', SANS, 15, TXT2)]),
            ('Después de 2016', [('RONI queda en promedio 0,4 °C por debajo de ONI: el trópico se calentó. '
                                  'Para nosotros, RONI sirve para comprobar que el resultado no cambia.', SANS, 15, TXT2)])]
    for i, (cab, cuerpo) in enumerate(cols):
        x = 2.35 + i * 5.25
        caja(s, x, y0 + 0.72, 4.95, 0.35, [[(cab, SANSB, 15, CIAN)]])
        caja(s, x, y0 + 1.08, 4.95, 0.85, [cuerpo])

    # fuentes con enlaces cortos
    tb = caja(s, 1.98, 10.1, 15.6, 0.35, [[('Fuentes: ', SANS, 13, SRC)]])
    p = tb.text_frame.paragraphs[0]
    for i, (texto, url) in enumerate(ENLACES):
        r = p.add_run(); r.text = texto; fuente_run(r, SANS, 13, CIAN); r.hyperlink.address = url
        if i < len(ENLACES) - 1:
            r = p.add_run(); r.text = '  ·  '; fuente_run(r, SANS, 13, SRC)
    s.notes_slide.notes_text_frame.text = (
        'ONI (Oceanic Niño Index), NOAA CPC, ERSSTv6: media móvil de 3 meses de la anomalía de SST en Niño 3.4 (5° N–5° S, 170°–120° O). '
        'La anomalía se calcula con periodos base de 30 años que se actualizan cada 5 años. Episodio: ±0,5 °C durante al menos 5 trimestres móviles seguidos.\n'
        'RONI (Relative ONI), NOAA CPC: Niño 3.4 menos la anomalía media del cinturón tropical 20° S–20° N, reescalado a la varianza del Niño 3.4. '
        'Mide si el Pacífico central está más cálido que el resto del trópico, que es lo que mueve la convección. Mismos umbrales. '
        'Circular del CPC de mayo de 2026: RONI pasa a ser el estándar principal para avisos y clasificación.\n'
        f'Comparación propia con las tablas oficiales v6 (descargadas 31 oct 2026), {e["n"]} meses de 1981–2016: r = {e["r"]:.3f}; '
        f'diferencia media RONI − ONI = {e["dif"]:+.3f} °C; misma categoría (solo umbral ±0,5, sin persistencia) en {e["misma"] * 100:.1f} % de los meses. '
        'De 2017 en adelante la diferencia media es −0,41 °C. Archivo: metadata/reference/cpc_oni_roni_v6_1981_2016.csv.\n'
        'Niño y Niña fuertes (resaltados en la serie): ONI ≥ +1,5 °C o ≤ −1,5 °C durante al menos 3 trimestres móviles seguidos, convención de intensidad del CPC '
        '(débil 0,5–0,9; moderado 1,0–1,4; fuerte ≥ 1,5 °C), que el mismo CPC aclara que no es una clasificación oficial. '
        'En 1981–2016: ' + '; '.join(f'{"Niño" if sg > 0 else "Niña"} {int(p[0][0])}–{int(p[-1][0])} (pico {max(abs(v) for _, v in p):.1f} °C)'
                                     for sg, p in tramos_fuertes(d)) + '.\n'
        'Respuesta para la exposición: en el periodo de la tesis los dos índices dan prácticamente la misma historia; se usa ONI porque es el índice de la literatura '
        'ENSO–rendimiento y el que se calculó; RONI se usa para comprobar que el resultado no cambia.\n'
        'MJO: índice RMM (Wheeler y Hendon, 2004), diario, del Bureau of Meteorology de Australia (rmm.74toRealtime.txt). '
        'Fase 1–8 = longitud de la convección; amplitud > 1 = MJO activa; ≤ 1 = débil. Se proyecta tras quitar el ciclo anual y la media de 120 días.')
    nombrar(s, n0)
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--salida', default=str(PPT))
    a = ap.parse_args()
    d = pd.read_csv(DATOS)
    prs = Presentation(PPT)
    construir(prs, d); color_enlaces(prs); renumerar(prs)
    prs.save(a.salida); print('guardado', a.salida, estadisticas(d))


if __name__ == '__main__':
    main()
