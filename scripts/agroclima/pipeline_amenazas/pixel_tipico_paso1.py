"""Paso 1 del procedimiento: ¿qué amenaza, en qué fase, acompaña las pérdidas de rendimiento del píxel? (1981–2016)

Por amenaza y fase, una sola variable por año (más amenaza = valor mayor):
  calor, calor > 29 °C, racha seca, lluvia   días en evento en esa fase (los días de un evento que pasa de fase se reparten)
  sequía                                     déficit = −Σ(P − ETP) de la fase
  seco-cálido                                1 si hubo evento en FLO–FIL, 0 si no
  EDD29                                      °C·día sobre 29 °C (no es evento; regla continua)
Frente a la pérdida relativa del año (rendimiento / tendencia − 1, la misma de la mala cosecha).
Cada amenaza se deja sin tendencia (residuo de una recta 1981–2016), igual que el rendimiento.
  ρ de Spearman (negativo = más amenaza, menos cosecha), su p, ρ sin 2012, y q de Benjamini–Hochberg sobre todas las celdas.
  Lectura de seguro: cuántas de las malas cosechas tuvieron la amenaza en esa fase (días > 0 o bandera = 1).

Entradas: conteo_reglas_<fecha>/eventos.csv y regla_anio.csv; malas_cosechas_<fecha>/anual_maize.csv.gz.
Salida: pixel_tipico/paso1_<fecha>/paso1.xlsx (hojas «celdas» y «años») y resumen.json.
Uso: .venv/Scripts/python.exe pixel_tipico_paso1.py --conteo conteo_reglas_20261105_150123
"""
import argparse, json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from pixel_tipico_tendencia import BASE

MALAS = Path('C:/Users/paola/Tesis/03_Resultados/Agroclima/vigente/rendimiento/malas_cosechas_20261104_213842')
FASES = ['EST', 'VEG', 'FLO', 'REP', 'FIL', 'MAT']
ANIOS = np.arange(1981, 2017)
CAL = ['MAI-EST-CAL', 'MAI-VEG1-CAL', 'MAI-VEG2-CAL', 'MAI-FLO-CAL', 'MAI-REP-CAL', 'MAI-FIL-CAL']
AMENAZAS = [('Calor', CAL), ('Calor sobre 29 °C', ['MAI-RACHA-29']), ('Racha seca', ['MAI-RACHA-SECA']),
            ('Lluvia', ['MAI-MAT-LLU']), ('Sequía', None), ('Seco-cálido', None), ('EDD29', None)]


def sin_tendencia(v):
    b = np.polyfit(ANIOS, v, 1)
    return v - np.polyval(b, ANIOS)


def bh(p):
    p = np.asarray(p, float); n = len(p); o = np.argsort(p)
    q = p[o] * n / np.arange(1, n + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    out = np.empty(n); out[o] = np.minimum(q, 1); return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--conteo', required=True)
    ap.add_argument('--pixel', type=int, default=191325)
    a = ap.parse_args()
    c = BASE / a.conteo
    ev = pd.read_csv(c / 'eventos.csv'); ra = pd.read_csv(c / 'regla_anio.csv')
    ev = ev[ev.anio.between(1981, 2016)]; ra = ra[ra.anio.between(1981, 2016) & (ra.cultivo == 'maize')]
    y = pd.read_csv(MALAS / 'anual_maize.csv.gz'); y = y[y.pixel_id == a.pixel].set_index('anio').loc[ANIOS]
    perdida, mala = y.perdida_relativa_pct.values, y.mala_cosecha.values.astype(bool)

    series = {}  # (amenaza, fase) → valores por año
    for nom, ids in AMENAZAS:
        if ids:
            d = pd.DataFrame(0.0, index=ANIOS, columns=FASES)
            for o in ev[ev.id.isin(ids)].itertuples():
                for f, k in zip(o.fases.split(' → '), str(o.dias_por_fase).split(' + ')): d.loc[o.anio, f] += int(k)
            fases = {'Calor': FASES[:5], 'Lluvia': ['MAT']}.get(nom, FASES)
            for f in fases: series[(nom, f)] = d[f].values
        elif nom == 'Sequía':
            for r, g in ra[ra.id.str.endswith('-SEQ')].groupby('fase'):
                series[(nom, r)] = -g.set_index('anio').loc[ANIOS, 'valor'].values
        elif nom == 'Seco-cálido':
            series[(nom, 'FLO')] = ra[ra.id == 'MAI-TARDIA-SECA-CALIDA'].set_index('anio').loc[ANIOS, 'hubo'].values
        else:
            for f, g in ra[ra.id == 'MAI-EDD-29'].groupby('fase'):
                series[(nom, f)] = g.set_index('anio').loc[ANIOS, 'valor'].values
    filas, largo = [], []
    sin12 = ANIOS != 2012
    for (nom, f), v in series.items():
        v = np.asarray(v, float)
        fila = dict(amenaza=nom, fase=f, anios_con_amenaza=int((v > 0).sum()) if nom not in ('Sequía', 'EDD29') else None,
                    malas_con_amenaza=int((v[mala] > 0).sum()) if nom not in ('Sequía', 'EDD29') else None, malas=int(mala.sum()))
        if np.nanstd(v) == 0:
            filas.append(fila | dict(nota='sin variación (no hubo eventos)')); continue
        x = sin_tendencia(v)
        rho, p = spearmanr(x, perdida)
        fila |= dict(rho=rho, p=p, rho_sin_2012=spearmanr(x[sin12], perdida[sin12])[0],
                     media_malas=float(v[mala].mean()), media_resto=float(v[~mala].mean()))
        filas.append(fila)
        largo += [dict(amenaza=nom, fase=f, anio=int(t), valor=float(vv), valor_sin_tendencia=float(xx), perdida_pct=float(pp), mala=int(m))
                  for t, vv, xx, pp, m in zip(ANIOS, v, x, perdida, mala)]
    r = pd.DataFrame(filas)
    ok = r.p.notna()
    r.loc[ok, 'q_bh'] = bh(r.loc[ok, 'p'])
    out = BASE / f'paso1_{datetime.now():%Y%m%d_%H%M%S}'
    out.mkdir()
    with pd.ExcelWriter(out / 'paso1.xlsx') as w:
        r.round(4).to_excel(w, sheet_name='celdas', index=False)
        pd.DataFrame(largo).round(3).to_excel(w, sheet_name='años', index=False)
    (out / 'resumen.json').write_text(json.dumps(dict(
        pixel=a.pixel, conteo=a.conteo, malas=MALAS.name, pruebas=int(ok.sum()), p05=int((r.p < .05).sum()),
        q05=int((r.q_bh < .05).sum()), esperado_azar=round(.05 * int(ok.sum()), 1),
        criterio='Spearman entre la amenaza sin tendencia y la pérdida relativa; q de Benjamini–Hochberg'), ensure_ascii=False, indent=1), encoding='utf-8')
    print(out)
    print(r.round(2).to_string(index=False))


if __name__ == '__main__':
    main()
