"""Rachas de calor de toda la temporada en el píxel típico, sin cortarlas en el borde de las fases.

Pregunta: una misma ola de calor que cruza el borde entre dos fases, ¿cuántas veces se cuenta en reglas v3?
reglas v3 corta cada racha en el borde de la fase (como v1): una ola de 11 días que empieza en FLO y termina en REP-pos
queda como dos eventos más cortos, cada uno con un grado de severidad menor.

Aquí se evalúa la temporada seguida, de VE a R4_R5 (el umbral de cada día es el de su bloque, el mismo de reglas v3),
en cada celda nativa; luego se pondera por cos(lat), igual que reglas v3.
Salida: carpeta rachas_temporada_<fecha> con
  dias.csv     · por año y fecha: bloque, fase y fracción ponderada de celdas en racha ≥ 2 d;
  rachas.csv   · por año: cada ola del píxel (días seguidos con ≥ 50 % de las celdas en racha), fases que toca, su
                 grado por la duración completa y en cuántos pedazos (≥ 2 d) la cuenta reglas v3;
  resumen.json · olas que cruzan un borde y conteo comparado.
Uso: .venv/Scripts/python.exe pixel_tipico_rachas_temporada.py --reglas <carpeta reglas_v3_...> [--pixel 191325]
"""
import argparse, json, math, sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

from pixel_tipico_tendencia import SQLITE, BASE, ANIOS
from pixel_tipico_reglas_v3 import CONFIG, BLOQUES_V3, UMBRAL_V3, ETAPA_BLOQUE, bloques_por_dia, grado, rachas

FASE_BLOQUE = {b: f for f, bs in BLOQUES_V3.items() for b in bs}
CON_CALOR = [b for b in FASE_BLOQUE if b in UMBRAL_V3]  # VE … R4_R5; R6 (MAT) es lluvia


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pixel', type=int, default=191325)
    ap.add_argument('--reglas', required=True, help='carpeta reglas_v3_... con eventos.csv')
    a = ap.parse_args()
    c = json.loads(CONFIG.read_text(encoding='utf-8'))
    data = json.loads((Path(c['calendar_dir']) / 'maize-maize__rf.json').read_text(encoding='utf-8'))
    con = sqlite3.connect(SQLITE)
    ref = pd.read_sql("select latitud, longitud from pares_v2 where pixel_id=? limit 1", con, params=(a.pixel,))
    lat, lon = float(ref.latitud.iloc[0]), float(ref.longitud.iloc[0])
    cal = dict(templates=data['templates'], pixel=data['pixels'][f'{lat:.2f},{lon:.2f}'])

    diario = pd.read_csv(BASE / f'pixel_{a.pixel}' / 'diario_celdas_nativas_1981_2016.csv.gz')
    diario['f'] = pd.to_datetime(diario.fecha).dt.date

    filas = []
    for anio in ANIOS:
        mapa = {d: b for d, b in bloques_por_dia(cal, int(anio)).items() if b in CON_CALOR}
        dias = sorted(mapa)
        w = diario[(diario.f >= dias[0]) & (diario.f <= dias[-1])]
        en_racha, pesos = pd.Series(0.0, index=dias), 0.0
        for (clon, clat), g in w.groupby(['lon', 'lat']):
            g = g.sort_values('f')
            if len(g) != len(dias) or g.tmax_c.isna().any():
                continue
            peso = math.cos(clat * math.pi / 180)
            hits = [t >= UMBRAL_V3[mapa[d]] for t, d in zip(g.tmax_c, g.f)]
            marca = [0] * len(dias)
            for i, largo in rachas(hits):
                for k in range(i, i + largo): marca[k] = 1
            en_racha += peso * pd.Series(marca, index=dias)
            pesos += peso
        for d in dias:
            filas.append(dict(anio=int(anio), fecha=d.isoformat(), dia_ciclo=(d - dias[0]).days, bloque=mapa[d],
                              fase=FASE_BLOQUE[mapa[d]], frac_celdas=en_racha[d] / pesos))
    dd = pd.DataFrame(filas)

    # Olas del píxel: días seguidos con al menos la mitad de las celdas en racha
    olas = []
    for anio, g in dd.groupby('anio'):
        g = g.reset_index(drop=True)
        for i, largo in rachas(list(g.frac_celdas >= 0.5), min_dias=2):
            t = g.iloc[i:i + largo]
            fases = list(dict.fromkeys(t.fase))
            partes = [int((t.fase == f).sum()) for f in fases]
            etapa = ETAPA_BLOQUE[t.bloque.value_counts().index[0]]  # como reglas v3: el bloque con más días
            olas.append(dict(anio=int(anio), inicio=t.fecha.iloc[0], fin=t.fecha.iloc[-1], dia_ini=int(t.dia_ciclo.iloc[0]),
                             dias=largo, fases=' → '.join(fases), dias_por_fase=' + '.join(map(str, partes)),
                             cruza_borde=len(fases) > 1, etapa=etapa, grado_completa=grado(largo, etapa),
                             pedazos_v3=sum(p >= 2 for p in partes), dias_fuera_v3=sum(p for p in partes if p < 2)))
    ol = pd.DataFrame(olas)

    out = BASE / f'rachas_temporada_{datetime.now():%Y%m%d_%H%M%S}'
    out.mkdir()
    dd.to_csv(out / 'dias.csv', index=False)
    ol.to_csv(out / 'rachas.csv', index=False)
    (out / 'resumen.json').write_text(json.dumps(dict(
        pixel=a.pixel, reglas=str(a.reglas), umbral=UMBRAL_V3, criterio_ola='días seguidos (≥ 2) con ≥ 50 % de las celdas en racha',
        olas=len(ol), olas_que_cruzan_borde=int(ol.cruza_borde.sum()),
        contadas_dos_veces=ol[ol.pedazos_v3 > 1][['anio', 'inicio', 'dias', 'dias_por_fase']].to_dict(orient='records'),
        grado_completa=ol.grado_completa.value_counts().to_dict(),
        anios_con_ola_que_cruza=sorted(ol[ol.cruza_borde].anio.unique().tolist())), ensure_ascii=False, indent=1),
        encoding='utf-8')
    print(out)
    print(ol.to_string())


if __name__ == '__main__':
    main()
