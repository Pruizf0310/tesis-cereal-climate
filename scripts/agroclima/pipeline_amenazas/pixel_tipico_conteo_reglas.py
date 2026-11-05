"""Conteo de eventos de las reglas vigentes (reglas_vigentes.csv) en el píxel típico: maíz, soya y trigo de invierno.

Las reglas salen de amenazas/reglas_vigentes.csv (generado desde AMENAZAS_vigente.xlsx); aquí no se escribe ningún umbral.
Arroz no se cuenta si el píxel no está en su máscara (Nebraska no lo está).

Cómo se cuenta cada tipo de evento:
  racha / dia  OLA del píxel, igual que pixel_tipico_olas_amenazas.py: en cada celda nativa de ERA5-Land se marcan los días
               que cumplen la condición (racha: solo los que forman racha ≥ min_dias); el píxel está «en evento» el día en que
               al menos el 50 % de las celdas (ponderadas por cos(lat)) lo están; una ola son días seguidos en evento
               (≥ min_dias en racha, ≥ 1 en dia). Las reglas de un mismo cultivo con igual variable, operador y duración se
               evalúan juntas en toda su ventana, cada día con el umbral de su fase: la ola no se corta en el borde y se
               asigna a la regla (fase) donde tiene más días. En dia, cada día de la ola es un evento.
  ventana      sí/no por temporada con el agregado de la fase (suma o media), calculado en cada celda y promediado en el
               píxel con cos(lat). Los percentiles (Q1, p20, p80) son los de las temporadas 1981–2016 del píxel.
  continua     EDD29: Σ max(0, Tmax − 29 °C) por fase; no es evento, se reporta el valor.
Casos de la tabla: trigo VEG (Feng et al. 1999) usa el umbral según los días desde el encañado (inicio de Z30–39), de 4 días
antes a 20 después; la lluvia R6–R8 de soya es una sola ventana (se reporta en FIL y MAT, se cuenta una vez).
Año: anio = año de cosecha (el de GDHY); en trigo de invierno la siembra es el año anterior.

Entrada: pixel_<id>/diario_celdas_nativas_anual_1950_2024.csv.gz (Tmax, Tmin, Tmedia, P; pixel_tipico_descarga.py
--meses 1-12 --nombre anual) y calendario/<cultivo>.json (calendario regional v4).
Salida: carpeta conteo_reglas_<fecha> con eventos.csv (una fila por evento: días por fase y, en calor de maíz, grado), regla_anio.csv (regla × año), resumen.xlsx.
Uso: .venv/Scripts/python.exe pixel_tipico_conteo_reglas.py [--pixel 191325]
"""
import argparse, json, math
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from pixel_tipico_tendencia import BASE
from pixel_tipico_reglas_v3 import bloques_por_dia, rachas, et0_hargreaves, grado, ETAPA_BLOQUE

AM = Path('C:/Users/paola/Tesis/03_Resultados/Agroclima/vigente/amenazas')
CAL = Path('C:/Users/paola/Tesis/03_Resultados/Agroclima/vigente/calendario')
MASCARAS = Path(__file__).resolve().parents[3] / 'metadata' / 'mascaras'
REF = (1981, 2016)  # temporadas para los percentiles de las reglas de ventana
CULTIVOS = {  # prefijo de la regla: (cultivo GDHY, calendario, bloque → fase)
    'MAI': ('maize', 'maize-maize__rf', dict(VE='EST', V1_V6='VEG', V7_VT='VEG', R1='FLO', R2='REP', R3='FIL', R4_R5='FIL', R6='MAT')),
    'SOY': ('soybean', 'soybean-soybean__rf', dict(VE_VC='EST', V1_VN='VEG', R1_R2='FLO', R3='REP', R4='REP', R5='FIL', R6_R7='FIL', R8='MAT')),
    'TRI': ('wheat', 'wheat-winter_wheat__rf', dict(Z00_09='EST', Z10_29='VEG', Z30_39='VEG', Z40_49='REP', Z50_59='REP',
                                                     Z60_69='FLO', Z70_89='FIL', Z90_99='MAT')),
    'ARR': ('rice', None, None)}
# ventanas que no son la fase entera de la regla
BLOQUES = {'MAI-VEG1-CAL': ['V1_V6'], 'MAI-VEG2-CAL': ['V7_VT'], 'SOY-FIL-LLU': ['R6_R7', 'R8'], 'SOY-MAT-LLU': ['R6_R7', 'R8']}
TARDIA = ['FLO', 'REP', 'FIL']
FENG = [(-4, 0, -4.2), (1, 5, -3.5), (6, 10, -2.5), (11, 15, -1.0), (16, 20, 0.0)]  # días desde el encañado → Tmin
OPS = {'>': np.greater, '>=': np.greater_equal, '<': np.less, '<=': np.less_equal}


def fases_regla(fase):
    f = str(fase)
    if f.startswith('Todas'): return ['EST', 'VEG', 'FLO', 'REP', 'FIL', 'MAT']
    if '+' in f: return TARDIA
    return [f.split('-')[0]]  # REP-pre / REP-pos → REP


def cargar(pixel):
    arch = BASE / f'pixel_{pixel}' / 'diario_celdas_nativas_anual_1950_2024.csv.gz'
    d = pd.read_csv(arch)
    d['f'] = pd.to_datetime(d.fecha).dt.date
    d['teff_c'] = (d.tmean_c + d.tmax_c) / 2
    d['edd29'] = (d.tmax_c - 29).clip(lower=0)
    d['et0_mm'] = [et0_hargreaves(f, la, tx, tn) for f, la, tx, tn in zip(d.f, d.lat, d.tmax_c, d.tmin_c)]
    d['p_menos_et0'] = d.p_mm - d.et0_mm
    celdas = d[['lon', 'lat']].drop_duplicates().sort_values(['lon', 'lat'])
    piv = {v: d.pivot(index='f', columns=['lon', 'lat'], values=v)[list(map(tuple, celdas.values))]
           for v in ['tmax_c', 'tmin_c', 'tmean_c', 'teff_c', 'p_mm', 'edd29', 'p_menos_et0']}
    peso = np.cos(np.radians(celdas.lat.values))
    return arch, piv, peso


def dias_regla(r, mapa, fase_de):
    """Fecha → umbral de esta regla en la temporada (mapa: fecha → bloque)."""
    if r.id == 'TRI-VEG-HEL':
        enc = min(d for d, b in mapa.items() if b == 'Z30_39')
        out = {}
        for a, b, u in FENG:
            for k in range(a, b + 1): out[enc + timedelta(days=k)] = u
        return out
    bl = BLOQUES.get(r.id)
    fs = fases_regla(r.fase)
    return {d: r.umbral for d, b in mapa.items() if (b in bl if bl else fase_de[b] in fs)}


def olas_grupo(grupo, piv, peso, mapa, fase_de):
    """Olas de un grupo de reglas (misma variable, operador, evento y duración) en una temporada."""
    r0 = grupo[0]
    umbral, regla = {}, {}
    for r in grupo:
        for d, u in dias_regla(r, mapa, fase_de).items():
            umbral[d] = u; regla[d] = r.id
    dias = pd.date_range(min(umbral), max(umbral)).date
    x = piv[r0.variable].reindex(dias)
    ok = ~x.isna().any().values  # celdas con todos los días
    u = np.array([umbral.get(d, np.nan) for d in dias])
    hit = OPS[r0.operador](x.values, u[:, None]) & ~np.isnan(u)[:, None]
    marca = np.zeros_like(hit, dtype=float)
    md = int(r0.min_dias)
    for j in np.where(ok)[0]:
        for i, largo in rachas(list(hit[:, j]), min_dias=md if r0.evento == 'racha' else 1):
            marca[i:i + largo, j] = 1
    frac = (marca[:, ok] * peso[ok]).sum(1) / peso[ok].sum()
    out = []
    for i, largo in rachas(list(frac >= 0.5), min_dias=md if r0.evento == 'racha' else 1):
        tramo = dias[i:i + largo]
        ids = [regla.get(d) for d in tramo if regla.get(d)]
        rid = max(dict.fromkeys(ids), key=ids.count)
        fases = [fase_de[mapa[d]] for d in tramo if d in mapa]
        orden = list(dict.fromkeys(fases))
        bls = [mapa[d] for d in tramo if d in mapa]
        b = max(dict.fromkeys(bls), key=bls.count) if bls else None
        out.append(dict(id=rid, inicio=tramo[0], fin=tramo[-1], dias=largo,
                        fase=max(orden, key=fases.count) if orden else '', fases=' → '.join(orden),
                        dias_por_fase=' + '.join(str(fases.count(f)) for f in orden), cruza_borde=len(orden) > 1,
                        # grado por la duración completa (Li 2025b, Tabla 2): solo calor de maíz por fase
                        grado=grado(largo, ETAPA_BLOQUE[b]) if rid.startswith('MAI-') and rid.endswith('-CAL') and b in ETAPA_BLOQUE else ''))
    return out


def agregado(piv, peso, var, dias, como):
    x = piv[var].reindex(sorted(dias))
    ok = ~x.isna().any().values
    v = getattr(x.loc[:, ok], como)()
    return float((v.values * peso[ok]).sum() / peso[ok].sum())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pixel', type=int, default=191325)
    a = ap.parse_args()
    reglas = pd.read_csv(AM / 'reglas_vigentes.csv', encoding='utf-8-sig')
    arch, piv, peso = cargar(a.pixel)
    hay = set(piv['tmax_c'].index)
    eventos, filas, omitidas = [], [], []
    for pref, (cultivo, cal_nombre, fase_de) in CULTIVOS.items():
        rs = reglas[reglas.id.str.startswith(pref)]
        m = pd.read_csv(MASCARAS / f'pixeles_{cultivo}.csv', encoding='utf-8-sig')
        fila = m[m.pixel_id == a.pixel]
        if fila.empty or cal_nombre is None:
            omitidas += list(rs.id); continue
        cj = json.loads((CAL / f'{cal_nombre}.json').read_text(encoding='utf-8'))
        clave = f'{float(fila.latitude.iloc[0]):.2f},{float(fila.longitude.iloc[0]):.2f}'
        cal = dict(templates=cj['templates'], pixel=cj['pixels'][clave])
        temporadas = {}
        for siembra in range(1950, 2025):
            mapa = bloques_por_dia(cal, siembra)
            if set(mapa) <= hay:
                temporadas[max(mapa).year] = mapa  # año de cosecha
        grupos = {}
        for r in rs[rs.evento.isin(['racha', 'dia'])].itertuples():
            grupos.setdefault((r.variable, r.operador, r.evento, r.min_dias, r.fase if str(r.fase).startswith('Todas') else ''), []).append(r)
        for anio, mapa in temporadas.items():
            ev = [e | dict(anio=anio) for g in grupos.values() for e in olas_grupo(g, piv, peso, mapa, fase_de)]
            eventos += ev
            for r in rs.itertuples():
                base = dict(id=r.id, regla=r.regla, cultivo=cultivo, fase=r.fase, evento=r.evento, anio=anio)
                if r.evento in ('racha', 'dia'):
                    e = [x for x in ev if x['id'] == r.id]
                    filas.append(base | dict(eventos=sum(x['dias'] for x in e) if r.evento == 'dia' else len(e),
                                             olas=len(e), dias_en_evento=sum(x['dias'] for x in e),
                                             ola_max=max([x['dias'] for x in e], default=0), hubo=int(bool(e))))
                    continue
                fs = fases_regla(r.fase)
                bl = BLOQUES.get(r.id)
                dias = [d for d, b in mapa.items() if (b in bl if bl else fase_de[b] in fs)]
                if r.id == 'MAI-EDD-29':
                    for f in TARDIA:
                        filas.append(base | dict(fase=f, valor=agregado(piv, peso, 'edd29', [d for d, b in mapa.items() if fase_de[b] == f], 'sum')))
                    continue
                if r.variable.startswith('p_menos_etp'):
                    filas.append(base | dict(valor=agregado(piv, peso, 'p_menos_et0', dias, 'sum')))
                elif r.variable.startswith('p_suma_y_tmean'):
                    filas.append(base | dict(valor=agregado(piv, peso, 'p_mm', dias, 'sum'), valor_t=agregado(piv, peso, 'tmean_c', dias, 'mean')))
                elif r.variable == 'tmax_media_fase_c':
                    filas.append(base | dict(valor=agregado(piv, peso, 'tmax_c', dias, 'mean')))
                elif r.variable.startswith('p_suma'):
                    filas.append(base | dict(valor=agregado(piv, peso, 'p_mm', dias, 'sum')))
                else:
                    raise ValueError(f'Regla de ventana sin cálculo: {r.id} ({r.variable})')
    ra = pd.DataFrame(filas)
    # reglas de ventana: umbral fijo o percentiles 1981–2016 del píxel
    en_ref = ra.anio.between(*REF)
    for r in reglas[reglas.evento == 'ventana'].itertuples():
        s = ra.id == r.id
        if not s.any(): continue
        if r.variable.startswith('p_menos_etp'):
            q1 = ra.loc[s & en_ref, 'valor'].quantile(.25)
            ra.loc[s, 'umbral_usado'] = q1; ra.loc[s, 'hubo'] = (ra.loc[s, 'valor'] < q1).astype(int)
        elif r.variable.startswith('p_suma_y_tmean'):
            p20, t80 = ra.loc[s & en_ref, 'valor'].quantile(.2), ra.loc[s & en_ref, 'valor_t'].quantile(.8)
            ra.loc[s, 'umbral_usado'] = p20; ra.loc[s, 'umbral_t'] = t80
            ra.loc[s, 'hubo'] = ((ra.loc[s, 'valor'] < p20) & (ra.loc[s, 'valor_t'] > t80)).astype(int)
        else:
            ra.loc[s, 'umbral_usado'] = r.umbral; ra.loc[s, 'hubo'] = OPS[r.operador](ra.loc[s, 'valor'], r.umbral).astype(int)
        ra.loc[s, 'eventos'] = ra.loc[s, 'hubo']
    ev = pd.DataFrame(eventos)

    def resumir(sub, nombre):
        g = sub.groupby(['id', 'regla', 'cultivo', 'fase', 'evento'], sort=False)
        return g.agg(anios=('anio', 'nunique'), anios_con_evento=('hubo', 'sum'), eventos_por_anio=('eventos', 'mean'),
                     dias_en_evento_por_anio=('dias_en_evento', 'mean'), ola_max=('ola_max', 'max'),
                     valor_medio=('valor', 'mean')).reset_index().assign(periodo=nombre)
    res = pd.concat([resumir(ra[en_ref], '1981–2016'), resumir(ra, f'{ra.anio.min()}–{ra.anio.max()}')])
    res['pct_anios_con_evento'] = 100 * res.anios_con_evento / res.anios

    out = BASE / f'conteo_reglas_{datetime.now():%Y%m%d_%H%M%S}'
    out.mkdir()
    ev.to_csv(out / 'eventos.csv', index=False)
    ra.to_csv(out / 'regla_anio.csv', index=False)
    with pd.ExcelWriter(out / 'resumen.xlsx') as w:
        res.round(2).to_excel(w, sheet_name='resumen', index=False)
        pd.DataFrame(dict(id=omitidas, motivo='el píxel no está en la máscara del cultivo')).to_excel(w, sheet_name='omitidas', index=False)
    (out / 'resumen.json').write_text(json.dumps(dict(
        pixel=a.pixel, diario=str(arch), reglas=str(AM / 'reglas_vigentes.csv'), periodo_percentiles=REF,
        criterio_ola='≥ 50 % de las celdas (cos(lat)) en evento; la ola se asigna a la regla con más días',
        omitidas=omitidas, anios={c: [int(ra[ra.cultivo == c].anio.min()), int(ra[ra.cultivo == c].anio.max())] for c in ra.cultivo.unique()},
        olas_por_regla=ev.id.value_counts().to_dict()), ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    print(out)
    print(res[res.periodo == '1981–2016'][['id', 'fase', 'evento', 'pct_anios_con_evento', 'eventos_por_anio', 'dias_en_evento_por_anio',
                                            'ola_max', 'valor_medio']].round(1).to_string(index=False))


if __name__ == '__main__':
    main()
