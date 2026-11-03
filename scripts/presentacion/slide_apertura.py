"""Reemplaza la imagen de la diapositiva 1 (apertura El Niño 1972–1973) por cajas de texto editables con el diseño de la PPT.

Reejecutable: borra las formas AP_* y la imagen original («Freeform 2») y vuelve a dibujar. Conserva y amplía las notas.
Uso (con el .venv del pipeline):  python slide_apertura.py [--salida ruta.pptx]
"""
import argparse

from pptx import Presentation
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

from slides_pixel_tipico import (PPT, BG, TXT, TXT2, SRC, CIAN, MAG, PANEL, SERIF, SANS, SANSB, caja, rect, rgb)

NOTA_SOYA = (
    '\n\nAmpliación 30 oct 2026 (paso a la soya, verificado):\n'
    '- «The monthly average price received for soybeans reached $10.00 per bushel in June 1973.» '
    'Coppess, J. (2019). A brief review of the consequential seventies. farmdoc daily (9):99, Univ. of Illinois.\n'
    '- En junio de 1973 EE. UU. embargó las exportaciones de soya y semilla de algodón; se levantó antes del 1 oct 1973 (misma fuente).\n'
    '- USDA ERS (Peters, Langley y Westcott, 2009, Amber Waves): la falla de la anchoveta peruana en 1972 redujo la proteína '
    'para piensos, aumentó la demanda de harina de soya y los precios de la soya se dispararon en 1973 y 1974.\n'
    '- Límite: el alza también respondió a la compra soviética de granos de 1972, la devaluación del dólar y la demanda mundial. '
    'El Niño fue un detonante dentro de varias causas, no la única. Falta un precio de soya de 1972 de la misma serie para '
    'expresar el alza como porcentaje.')


def construir(prs):
    s = prs.slides[0]
    for sh in list(s.shapes):
        if sh.name.startswith('AP_') or sh.name == 'Freeform 2':
            sh._element.getparent().remove(sh._element)
    s.background.fill.solid(); s.background.fill.fore_color.rgb = rgb(BG)
    n0 = len(s.shapes)

    caja(s, 1.98, 0.95, 10, 0.4, [[('PERÚ · 1972–1973', SANSB, 17, CIAN)]])
    caja(s, 1.98, 1.5, 16.0, 1.9, [[('Cuando cambió el Pacífico,', SERIF, 54, TXT)],
                                    [('cambió el precio de alimentar al mundo', SERIF, 54, MAG)]])

    tarjetas = [
        ('01 · OCÉANO', 'El Niño', '1972–1973',
         'El mar se calienta frente a Perú, sobre una pesquería que ya estaba sobreexplotada.', CIAN),
        ('02 · PESCA', '13,1 → 1,7', 'millones de t de anchoveta, 1970 → 1973',
         'La captura cae 87 % y se reduce el suministro mundial de harina de pescado.', CIAN),
        ('03 · PIENSO', '180 → 450', 'USD por t de harina de pescado',
         'De sep. 1972 a sep. 1973: +150 %. Falta proteína para alimentar ganado.', CIAN),
        ('04 · SOYA', '3,30 → 10,10', 'USD por bushel al productor, Iowa',
         'De jun. 1972 a jun. 1973. La soya reemplaza a la harina de pescado y EE. UU. embarga sus exportaciones.', MAG)]
    x0, w, gap, y0, h = 1.98, 3.6, 0.547, 4.0, 3.95
    for i, (eti, grande, unidad, texto, color) in enumerate(tarjetas):
        x = x0 + i * (w + gap)
        rect(s, x, y0, w, h, PANEL)
        rect(s, x, y0, w, 0.07, color)
        caja(s, x + 0.3, y0 + 0.35, w - 0.6, 0.35, [[(eti, SANSB, 15, SRC)]])
        caja(s, x + 0.25, y0 + 0.85, w - 0.35, 0.9, [[(grande, SERIF, 34, color)]])
        caja(s, x + 0.3, y0 + 1.75, w - 0.6, 0.7, [[(unidad, SANSB, 16, TXT)]])
        caja(s, x + 0.3, y0 + 2.55, w - 0.6, 1.5, [[(texto, SANS, 16, TXT2)]])
        if i < 3:
            caja(s, x + w, y0 + h / 2 - 0.3, gap, 0.6, [[('→', SANS, 36, CIAN)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    caja(s, 1.98, 8.45, 16.0, 0.5, [[('Una anomalía del océano viajó por la cadena de proteína: ', SANSB, 21, TXT),
                                     ('del mar peruano al precio de la soya.', SANS, 21, TXT2)]])
    caja(s, 1.98, 9.0, 16.0, 0.45, [[('El Niño fue un detonante, no la única causa: en 1972–1973 también pesaron la compra soviética de granos y la devaluación del dólar.', SANS, 15, SRC)]])
    caja(s, 1.98, 10.05, 15.6, 0.4, [[('Fuentes: FAO (1975), SOFA 1974; FAO, Examen de los recursos pesqueros marinos; '
                                       'USDA NASS, precios recibidos (Iowa); Coppess (2019), farmdoc daily 9:99; USDA ERS (2009).', SANS, 13, SRC)]])
    for k, sh in enumerate(list(s.shapes)[n0:]):
        sh.name = f'AP_{k:02d}'
    tf = s.notes_slide.notes_text_frame
    if 'Ampliación 30 oct 2026' not in tf.text:
        tf.text = tf.text + NOTA_SOYA
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--salida', default=str(PPT))
    a = ap.parse_args()
    prs = Presentation(PPT)
    construir(prs)
    prs.save(a.salida); print('guardado', a.salida)


if __name__ == '__main__':
    main()
