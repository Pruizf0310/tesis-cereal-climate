"""Diapositiva 2 («Tesis»): título de la tesis con color por concepto (CMY sobre fondo K).

Cian = clima, amarillo = cultivo, magenta = seguro; las palabras de enlace en gris claro. Añade una leyenda pequeña.
Reejecutable: reescribe el cuadro del título y la forma TS_leyenda.
Uso (con el .venv del pipeline):  python slide_tesis.py [--salida ruta.pptx]
"""
import argparse

from pptx import Presentation

from slides_pixel_tipico import PPT, TXT2, SRC, CIAN, MAG, SERIF, SANS, SANSB, caja, fuente_run

AMARILLO = 'FACC15'
SEGMENTOS = [('Categorización de los impactos de ', TXT2), ('variabilidad climática global', CIAN),
             (' en el ', TXT2), ('rendimiento de cereales', AMARILLO),
             (' y la generación de insumos para el desarrollo de ', TXT2), ('seguros paramétricos', MAG),
             (' orientados a fortalecer la seguridad alimentaria.', TXT2)]


def construir(prs):
    s = prs.slides[1]
    titulo = next(sh for sh in s.shapes if sh.has_text_frame and sh.text_frame.text.startswith('Categorización'))
    p = titulo.text_frame.paragraphs[0]
    for r in list(p.runs): p._p.remove(r._r)
    for texto, color in SEGMENTOS:
        r = p.add_run(); r.text = texto; fuente_run(r, SERIF, 40, color)
    for sh in list(s.shapes):
        if sh.name == 'TS_leyenda': sh._element.getparent().remove(sh._element)
    ley = caja(s, 1.98, 5.15, 12, 0.4, [[('■', SANS, 17, CIAN), (' Clima     ', SANS, 17, SRC), ('■', SANS, 17, AMARILLO),
                                         (' Cultivo     ', SANS, 17, SRC), ('■', SANS, 17, MAG), (' Seguro', SANS, 17, SRC)]])
    ley.name = 'TS_leyenda'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--salida', default=str(PPT))
    a = ap.parse_args()
    prs = Presentation(PPT)
    construir(prs)
    prs.save(a.salida); print('guardado', a.salida)


if __name__ == '__main__':
    main()
