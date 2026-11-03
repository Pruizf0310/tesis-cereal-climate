"""Correlaciones del píxel típico (por defecto 191325, Nebraska): la cadena índice → amenaza → rendimiento, todo sin tendencia.

1) Clima → rendimiento: cada variable por fase (episodios de calor, EDD29, P − ETP) contra el rendimiento sin tendencia.
2) ONI → rendimiento y ONI → clima: ONI (y RONI como sensibilidad) del mes central de cada fase y del invierno previo (DEF,
   valor de enero), contra el rendimiento y contra las variables por fase.
3) Eventos por tipo: años El Niño / Neutro / La Niña según el ONI de julio (|ONI| ≥ 0,5), con el rendimiento y las
   amenazas medias de cada grupo; y tipos por trayectoria (ONI DEF y JAS, tabla CPC completa): Niño→Niña (DEF ≥ 0,5 y
   JAS ≤ −0,5; verano de transición, Jong, Ting y Seager 2021, J. Climate 34:3629), Niña persistente (ambos ≤ −0,5),
   Niño en verano (JAS ≥ 0,5) y otros.
4) MJO → rendimiento y MJO → clima: días con MJO activa (amplitud RMM ≥ 1) en cada fase del cultivo, total y por pares de
   fases MJO (8–1, 2–3, 4–5, 6–7).
Todas las series se pasan por una recta 1981–2016 y se usa el residuo (decisión del 31 oct 2026).
Con 36 años, |r| ≥ 0,33 equivale a p < 0,05 (dos colas); se informa cuántos falsos positivos se esperan por azar.
Datos: SQLite pares_v2 (maturity-year), cpc_oni_roni_v6_1981_2016.csv, rmm_official.txt (BoM).
Salida: carpeta correlaciones_<fecha> con correlaciones.xlsx y resumen.json.
Uso: .venv/Scripts/python.exe pixel_tipico_correlaciones.py [--pixel 191325]
"""
import argparse, json, sqlite3
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from pixel_tipico_tendencia import SQLITE, BASE, FASES, VARS, ANIOS

REPO = Path(__file__).resolve().parents[3]
ONI = REPO / 'metadata/reference/cpc_oni_roni_v6_1981_2016.csv'
RMM = Path('C:/Users/paola/Tesis/01_Data/RMM/rmm_official.txt')
ONI_TABLA = Path('C:/Users/paola/Tesis/01_Data/ONI/ONI.txt')  # CPC v6, 1950–, columnas DJF…NDJ
PARES_MJO = {'8–1': (8, 1), '2–3': (2, 3), '4–5': (4, 5), '6–7': (6, 7)}


def sin_tendencia(x):
    x = np.asarray(x, float)
    if np.nanstd(x) == 0: return None
    t = stats.linregress(ANIOS, x)
    return x - (t.intercept + t.slope * ANIOS)


def r_p(x, y):
    x, y = sin_tendencia(x), sin_tendencia(y)
    if x is None or y is None: return np.nan, np.nan
    r, p = stats.pearsonr(x, y)
    return r, p


def leer_rmm():
    d = pd.read_csv(RMM, sep=r'\s+', skiprows=2, header=None, usecols=range(7),
                    names=['anio', 'mes', 'dia', 'rmm1', 'rmm2', 'fase', 'amp'])
    d['fecha'] = pd.to_datetime(dict(year=d.anio, month=d.mes, day=d.dia))
    d = d[(d.amp < 999) & d.fecha.dt.year.between(1981, 2016)]
    return d.set_index('fecha')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pixel', type=int, default=191325)
    a = ap.parse_args()
    c = sqlite3.connect(SQLITE)
    d = pd.read_sql("select * from pares_v2 where pixel_id=? and alineacion='maturity-year'", c, params=(a.pixel,))
    y = d.drop_duplicates('anio_rendimiento').set_index('anio_rendimiento').rendimiento_sin_tendencia.loc[ANIOS].values
    oni = pd.read_csv(ONI).set_index(['anio', 'mes'])
    rmm = leer_rmm()
    faltan_rmm = int(pd.date_range('1981-01-01', '2016-12-31').difference(rmm.index).size)

    serie = pd.DataFrame({'anio': ANIOS, 'rendimiento_sin_tendencia_t_ha': y})
    ventanas = {}
    for f in FASES:
        g = d[d.fase == f].set_index('anio_rendimiento').loc[ANIOS]
        ventanas[f] = list(zip(pd.to_datetime(g.inicio), pd.to_datetime(g.fin)))
        for v in VARS:
            serie[f'{f}_{v}'] = g[v].values.astype(float)
        # ONI y RONI del mes central de la fase
        medio = [i + (fi - i) / 2 for i, fi in ventanas[f]]
        for idx in ('oni', 'roni'):
            serie[f'{f}_{idx}'] = [oni.loc[(m.year, m.month), idx] for m in medio]
        # MJO: días activos en la ventana, total y por pares de fases
        act = []
        for i, fi in ventanas[f]:
            w = rmm.loc[i:fi]; on = w[w.amp >= 1]
            fila = {'activa': len(on) / max(len(w), 1)}
            for k, ph in PARES_MJO.items():
                fila[k] = on.fase.isin(ph).sum() / max(len(w), 1)
            act.append(fila)
        act = pd.DataFrame(act)
        serie[f'{f}_mjo_activa'] = act.activa.values
        for k in PARES_MJO: serie[f'{f}_mjo_{k}'] = act[k].values
    for idx in ('oni', 'roni'):
        serie[f'DEF_{idx}'] = [oni.loc[(t, 1), idx] for t in ANIOS]  # DEF centrado en enero, antes de la siembra
        serie[f'JUL_{idx}'] = [oni.loc[(t, 7), idx] for t in ANIOS]

    # 1) clima → rendimiento
    clima = []
    for f in FASES:
        for v, nom in VARS.items():
            r, p = r_p(serie[f'{f}_{v}'], y)
            clima.append(dict(fase=f, variable=v, descripcion=nom, r=r, p=p))
    clima = pd.DataFrame(clima)

    # 2) índices → rendimiento y → clima
    indices = []
    for idx in ('oni', 'roni'):
        for ventana in ['DEF'] + FASES:
            x = serie[f'{ventana}_{idx}']
            r, p = r_p(x, y)
            indices.append(dict(indice=idx.upper(), ventana=ventana, objetivo='rendimiento', r=r, p=p))
            for f in FASES:
                if ventana not in ('DEF', f): continue
                for v in VARS:
                    r, p = r_p(x, serie[f'{f}_{v}'])
                    indices.append(dict(indice=idx.upper(), ventana=ventana, objetivo=f'{f}_{v}', r=r, p=p))
    for f in FASES:
        for k in ['activa'] + list(PARES_MJO):
            x = serie[f'{f}_mjo_{k}']
            r, p = r_p(x, y)
            indices.append(dict(indice=f'MJO {k}', ventana=f, objetivo='rendimiento', r=r, p=p))
            for v in VARS:
                r, p = r_p(x, serie[f'{f}_{v}'])
                indices.append(dict(indice=f'MJO {k}', ventana=f, objetivo=f'{f}_{v}', r=r, p=p))
    indices = pd.DataFrame(indices)

    # 3) eventos ENSO por tipo (ONI de julio, en la floración)
    tipo = np.where(serie.JUL_oni >= 0.5, 'El Niño', np.where(serie.JUL_oni <= -0.5, 'La Niña', 'Neutro'))
    serie['enso_julio'] = tipo
    comp = []
    for t in ('El Niño', 'Neutro', 'La Niña'):
        m = tipo == t
        fila = dict(tipo=t, anios=int(m.sum()), lista=', '.join(map(str, ANIOS[m])),
                    rendimiento_media=float(y[m].mean()), rendimiento_min=float(y[m].min()),
                    pct_anios_perdida_1t=float((y[m] < -1).mean() * 100))
        for f in ('VEG', 'FLO', 'FIL'):
            fila[f'{f}_edd29_media'] = float(serie.loc[m, f'{f}_edd29'].mean())
            fila[f'{f}_episodios_media'] = float(serie.loc[m, f'{f}_conteo_original'].mean())
        comp.append(fila)
    comp = pd.DataFrame(comp)
    u = stats.kruskal(*[y[tipo == t] for t in ('El Niño', 'Neutro', 'La Niña')])

    # trayectoria del ENSO en el año (verano de transición)
    tabla = pd.read_csv(ONI_TABLA, sep='	').set_index('Year')
    def trayectoria(t):
        djf, jas = tabla.loc[t, 'DJF'], tabla.loc[t, 'JAS']
        if djf >= 0.5 and jas <= -0.5: return 'Niño→Niña'
        if djf <= -0.5 and jas <= -0.5: return 'Niña persistente'
        if jas >= 0.5: return 'Niño en verano'
        return 'Otro'
    serie['enso_trayectoria'] = [trayectoria(t) for t in ANIOS]
    tray = []
    edd_fil = sin_tendencia(serie.FIL_edd29); pe_fil = sin_tendencia(serie.FIL_p_menos_et0)
    serie['FIL_edd29_sin_tendencia'] = edd_fil; serie['FIL_p_menos_et0_sin_tendencia'] = pe_fil
    for t in ('Niño en verano', 'Niño→Niña', 'Niña persistente', 'Otro'):
        m = serie.enso_trayectoria.values == t
        tray.append(dict(tipo=t, anios=int(m.sum()), lista=', '.join(map(str, ANIOS[m])), rendimiento_media=float(y[m].mean()),
                         FIL_edd29_anomalia=float(edd_fil[m].mean()), FIL_p_menos_et0_anomalia=float(pe_fil[m].mean()),
                         p_mw_rendimiento=float(stats.mannwhitneyu(y[m], y[~m]).pvalue),
                         p_mw_FIL_edd29=float(stats.mannwhitneyu(edd_fil[m], edd_fil[~m]).pvalue)))
    tray = pd.DataFrame(tray)
    todos = pd.Series({t: trayectoria(t) for t in range(1950, 2025)})

    validas = lambda t: t.dropna(subset=['r'])
    resumen = dict(
        pixel=a.pixel, anios=len(ANIOS), r_critico_p05=float(stats.t.ppf(0.975, 34) / np.sqrt(34 + stats.t.ppf(0.975, 34) ** 2)),
        clima_pruebas=len(validas(clima)), clima_p05=int((validas(clima).p < 0.05).sum()),
        indices_rend_pruebas=int(validas(indices[indices.objetivo == 'rendimiento']).shape[0]),
        indices_rend_p05=int((validas(indices[indices.objetivo == 'rendimiento']).p < 0.05).sum()),
        indices_clima_pruebas=int(validas(indices[indices.objetivo != 'rendimiento']).shape[0]),
        indices_clima_p05=int((validas(indices[indices.objetivo != 'rendimiento']).p < 0.05).sum()),
        kruskal_enso_julio_p=float(u.pvalue), dias_rmm_faltantes=faltan_rmm,
        trayectoria_1950_2024={k: int(v) for k, v in todos.value_counts().items()},
        transicion_1950_2024=[int(t) for t in todos[todos == 'Niño→Niña'].index],
        nota_rmm='BoM: ENSO retirado de RMM hasta 2013-12-31; desde 2014 solo se retira la media de 120 días.')
    out = BASE / f'correlaciones_{datetime.now():%Y%m%d_%H%M%S}'; out.mkdir(parents=True)
    with pd.ExcelWriter(out / 'correlaciones.xlsx') as w:
        clima.to_excel(w, sheet_name='clima_rendimiento', index=False)
        indices.to_excel(w, sheet_name='indices', index=False)
        comp.to_excel(w, sheet_name='enso_por_tipo', index=False)
        tray.to_excel(w, sheet_name='enso_trayectoria', index=False)
        serie.to_excel(w, sheet_name='serie', index=False)
    (out / 'resumen.json').write_text(json.dumps(resumen, ensure_ascii=False, indent=1), encoding='utf-8')
    print(out); print(json.dumps(resumen, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
