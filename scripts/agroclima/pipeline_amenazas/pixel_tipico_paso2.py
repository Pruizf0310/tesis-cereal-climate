"""Paso 2 del procedimiento: ¿el ENSO cambia cuántas veces ocurren las amenazas que pasaron el paso 1? (1950–2024, 75 temporadas)

Amenazas: las que se sostuvieron en el paso 1 (q < 0,05): calor, calor > 29 °C y racha seca en FIL (días en evento);
EDD29 en FIL y en FLO (°C·día). Cada serie se deja sin tendencia (recta 1950–2024).
ONI v6 del CPC, dos momentos por fase:
  durante  ONI medio de los meses de la fase (ponderado por días)
  antes    ONI del mes que está 3 meses antes del inicio de la fase (anticipación)
Clase del año por ese valor: Niño ≥ +0,5; Niña ≤ −0,5; neutro el resto (sin la regla de persistencia del CPC).
Dos lecturas:
  frecuencia   % de años con amenaza alta (tercio superior de la serie sin tendencia) en Niña, neutro y Niño; por azar, 33 %
  correlación  ρ de Spearman entre ONI y la amenaza sin tendencia; q de Benjamini–Hochberg sobre las 10 pruebas;
               y Kruskal–Wallis entre las tres clases.

Entradas: conteo_reglas_<fecha> (eventos.csv, regla_anio.csv), calendario del maíz, metadata/reference/cpc_oni_v6_1950_2026.csv.
Salida: pixel_tipico/paso2_<fecha>/paso2.xlsx (hojas «resumen», «frecuencias», «años») y resumen.json.
Uso: .venv/Scripts/python.exe pixel_tipico_paso2.py --conteo conteo_reglas_20261105_150123
"""
import argparse, json
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, kruskal

from pixel_tipico_tendencia import BASE
from pixel_tipico_reglas_v3 import bloques_por_dia
from pixel_tipico_paso1 import bh

REPO = Path(__file__).resolve().parents[3]
ONI = REPO / 'metadata/reference/cpc_oni_v6_1950_2026.csv'
CAL = Path('C:/Users/paola/Tesis/03_Resultados/Agroclima/vigente/calendario/maize-maize__rf.json')
FASE_DE = dict(VE='EST', V1_V6='VEG', V7_VT='VEG', R1='FLO', R2='REP', R3='FIL', R4_R5='FIL', R6='MAT')
ANIOS = np.arange(1950, 2025)
AMENAZAS = [('Calor', 'FIL', ['MAI-EST-CAL', 'MAI-VEG1-CAL', 'MAI-VEG2-CAL', 'MAI-FLO-CAL', 'MAI-REP-CAL', 'MAI-FIL-CAL']),
            ('Calor sobre 29 °C', 'FIL', ['MAI-RACHA-29']), ('Racha seca', 'FIL', ['MAI-RACHA-SECA']),
            ('EDD29', 'FIL', None), ('EDD29', 'FLO', None)]
CLASES = ['Niña', 'Neutro', 'Niño']


def clase(v):
    return 'Niño' if v >= 0.5 else 'Niña' if v <= -0.5 else 'Neutro'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--conteo', required=True)
    ap.add_argument('--pixel', type=int, default=191325)
    a = ap.parse_args()
    c = BASE / a.conteo
    ev = pd.read_csv(c / 'eventos.csv'); ra = pd.read_csv(c / 'regla_anio.csv')
    ev = ev[ev.anio.between(1950, 2024)]; ra = ra[ra.anio.between(1950, 2024) & (ra.cultivo == 'maize')]
    oni = pd.read_csv(ONI).set_index(['anio', 'mes']).oni
    cj = json.loads(CAL.read_text(encoding='utf-8')); cal = dict(templates=cj['templates'], pixel=cj['pixels']['42.75,-97.25'])

    # ONI durante y antes de cada fase, por año
    o = {}
    for t in ANIOS:
        mapa = bloques_por_dia(cal, int(t))
        for f in ('FLO', 'FIL'):
            dias = sorted(d for d, b in mapa.items() if FASE_DE[b] == f)
            meses = pd.Series([(d.year, d.month) for d in dias]).value_counts()
            o[(t, f, 'durante')] = float(sum(oni.loc[m] * n for m, n in meses.items()) / meses.sum())
            ini = dias[0]; mm = (ini.month - 3 - 1) % 12 + 1; yy = ini.year - (1 if ini.month <= 3 else 0)
            o[(t, f, 'antes')] = float(oni.loc[(yy, mm)])

    filas, freqs, largo = [], [], []
    for nom, f, ids in AMENAZAS:
        if ids:
            v = pd.Series(0.0, index=ANIOS)
            for e in ev[ev.id.isin(ids)].itertuples():
                for ff, k in zip(e.fases.split(' → '), str(e.dias_por_fase).split(' + ')):
                    if ff == f: v[e.anio] += int(k)
        else:
            v = ra[(ra.id == 'MAI-EDD-29') & (ra.fase == f)].set_index('anio').valor.reindex(ANIOS)
        v = v.values.astype(float)
        x = v - np.polyval(np.polyfit(ANIOS, v, 1), ANIOS)
        alto = x >= np.quantile(x, 2 / 3)
        for cuando in ('durante', 'antes'):
            s = np.array([o[(t, f, cuando)] for t in ANIOS]); k = np.array([clase(z) for z in s])
            rho, p = spearmanr(s, x)
            kw = kruskal(*[x[k == cl] for cl in CLASES if (k == cl).sum() > 1]).pvalue
            filas.append(dict(amenaza=nom, fase=f, oni=cuando, rho=rho, p=p, p_kruskal=kw,
                              **{f'n_{cl}': int((k == cl).sum()) for cl in CLASES}))
            for cl in CLASES:
                m = k == cl
                freqs.append(dict(amenaza=nom, fase=f, oni=cuando, clase=cl, anios=int(m.sum()),
                                  anios_alta=int(alto[m].sum()), pct_alta=100 * alto[m].mean(), media=float(v[m].mean())))
            largo += [dict(amenaza=nom, fase=f, oni=cuando, anio=int(t), valor=float(vv), sin_tendencia=float(xx), alta=int(al),
                           oni_valor=float(ss), clase=kk) for t, vv, xx, al, ss, kk in zip(ANIOS, v, x, alto, s, k)]
    r = pd.DataFrame(filas); r['q_bh'] = bh(r.p)
    fr = pd.DataFrame(freqs)
    out = BASE / f'paso2_{datetime.now():%Y%m%d_%H%M%S}'
    out.mkdir()
    with pd.ExcelWriter(out / 'paso2.xlsx') as w:
        r.round(4).to_excel(w, sheet_name='resumen', index=False)
        fr.round(2).to_excel(w, sheet_name='frecuencias', index=False)
        pd.DataFrame(largo).round(3).to_excel(w, sheet_name='años', index=False)
    (out / 'resumen.json').write_text(json.dumps(dict(
        pixel=a.pixel, conteo=a.conteo, oni=str(ONI.name), anios=[1950, 2024], pruebas=len(r), p05=int((r.p < .05).sum()),
        q05=int((r.q_bh < .05).sum()), esperado_azar=round(.05 * len(r), 1),
        clases='Niño ≥ +0,5; Niña ≤ −0,5 (valor del ONI, sin persistencia)', alta='tercio superior de la serie sin tendencia'),
        ensure_ascii=False, indent=1), encoding='utf-8')
    print(out)
    print(r.round(3).to_string(index=False))
    print(fr[fr.oni == 'durante'].round(1).to_string(index=False))


if __name__ == '__main__':
    main()
