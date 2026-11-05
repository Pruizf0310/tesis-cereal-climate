"""¿Los eventos de cada regla de maíz coinciden con las malas cosechas del píxel? (1981–2016, 36 temporadas)

Dos lecturas por regla:
  1 · Tabla 2 × 2 (lectura de seguro): hubo evento sí/no frente a mala cosecha sí/no.
      aciertos = evento y mala cosecha; falsas alarmas = evento sin mala cosecha; fallos = mala cosecha sin evento.
      POD = aciertos / malas cosechas; FAR = falsas alarmas / años con evento. p de Fisher a una cola (más malas
      cosechas con evento de lo esperado por azar).
  2 · Magnitud: días en evento (racha, día) o valor de la fase (ventana, EDD29) frente a la pérdida relativa del año
      (rendimiento / tendencia − 1). Spearman, y Mann–Whitney a una cola entre años malos y el resto (dirección: más
      días o más EDD = peor; menos P − ETP o menos lluvia = peor).
Con 5 malas cosechas en 36 años la potencia es baja: un p alto no prueba que la regla no sirva.

Entradas: conteo_reglas_<fecha>/regla_anio.csv (pixel_tipico_conteo_reglas.py) y
malas_cosechas_<fecha>/anual_maize.csv.gz (malas_cosechas_pixeles.py).
Salida: conteo_reglas_<fecha>/eventos_vs_mala_cosecha.xlsx (hojas «reglas» y «años»).
Uso: .venv/Scripts/python.exe pixel_tipico_eventos_mala_cosecha.py --conteo <carpeta> [--malas <carpeta>]
"""
import argparse
from pathlib import Path

import pandas as pd
from scipy.stats import fisher_exact, mannwhitneyu, spearmanr

from pixel_tipico_tendencia import BASE

MALAS = Path('C:/Users/paola/Tesis/03_Resultados/Agroclima/vigente/rendimiento/malas_cosechas_20261104_213842')
MENOS_ES_PEOR = ('MAI-EST-SEQ', 'MAI-VEG-SEQ', 'MAI-FLO-SEQ', 'MAI-FIL-SEQ')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--conteo', required=True)
    ap.add_argument('--malas', default=str(MALAS))
    ap.add_argument('--pixel', type=int, default=191325)
    a = ap.parse_args()
    carpeta = Path(a.conteo) if Path(a.conteo).is_absolute() else BASE / a.conteo
    ra = pd.read_csv(carpeta / 'regla_anio.csv')
    ra = ra[(ra.cultivo == 'maize') & ra.anio.between(1981, 2016)]
    y = pd.read_csv(Path(a.malas) / 'anual_maize.csv.gz')
    y = y[y.pixel_id == a.pixel].set_index('anio')[['perdida_relativa_pct', 'z_robusto', 'mala_cosecha']]
    filas, anios = [], []
    for (rid, fase), g in ra.groupby(['id', 'fase'], sort=False):
        g = g.set_index('anio').join(y)
        mag = g.valor if g.evento.iloc[0] in ('ventana', 'continua') else g.dias_en_evento
        if rid == 'MAI-TARDIA-SECA-CALIDA': mag = None  # dos variables: solo la tabla 2 × 2
        f = dict(id=rid, regla=g.regla.iloc[0], fase=fase, evento=g.evento.iloc[0], malas=int(g.mala_cosecha.sum()))
        if g.evento.iloc[0] != 'continua':
            ev, m = g.hubo.astype(bool), g.mala_cosecha.astype(bool)
            ac, fa, fl, cn = int((ev & m).sum()), int((ev & ~m).sum()), int((~ev & m).sum()), int((~ev & ~m).sum())
            f |= dict(anios_con_evento=int(ev.sum()), aciertos=ac, falsas_alarmas=fa, fallos=fl, correctos_sin_evento=cn,
                      POD=ac / (ac + fl) if ac + fl else None, FAR=fa / (ac + fa) if ac + fa else None,
                      p_fisher=fisher_exact([[ac, fa], [fl, cn]], alternative='greater')[1] if ev.any() and not ev.all() else None)
        if mag is not None and mag.nunique() > 1:
            peor = -mag if rid in MENOS_ES_PEOR else mag
            f |= dict(magnitud='valor de la fase' if g.evento.iloc[0] in ('ventana', 'continua') else 'días en evento',
                      mediana_anios_malos=mag[g.mala_cosecha == 1].median(), mediana_resto=mag[g.mala_cosecha == 0].median(),
                      spearman_vs_perdida=spearmanr(mag, g.perdida_relativa_pct)[0],
                      p_spearman=spearmanr(mag, g.perdida_relativa_pct)[1],
                      p_mann_whitney=mannwhitneyu(peor[g.mala_cosecha == 1], peor[g.mala_cosecha == 0], alternative='greater')[1])
        filas.append(f)
        anios.append(g.assign(id=rid, fase=fase, magnitud=mag)[['id', 'fase', 'hubo', 'magnitud', 'perdida_relativa_pct', 'mala_cosecha']]
                     .reset_index())
    r = pd.DataFrame(filas)
    salida = carpeta / 'eventos_vs_mala_cosecha.xlsx'
    with pd.ExcelWriter(salida) as w:
        r.round(3).to_excel(w, sheet_name='reglas', index=False)
        pd.concat(anios).round(2).to_excel(w, sheet_name='años', index=False)
    print(salida)
    print(r.drop(columns=['regla']).round(2).to_string(index=False))


if __name__ == '__main__':
    main()
