"""Exporta a Excel (.xlsx) los datos exactos que entran a correlaciones_calendario_maiz.py (una fila = píxel × temporada).

Mismas reglas que la corrida: alineación maturity-year, pares válidos, píxeles plausibles, mismas 13 amenazas, ONI v6 mensual
del mes de cosecha y los 11 anteriores, MJO por fase del cultivo (cosechas 2014–2016 vacías, como en la corrida).
Libro 1 (amenazas + ONI): hoja Leeme, hoja Diccionario y una hoja por grupo de calendario.
Libro 2 (MJO): una hoja por grupo. Encabezado fijo y filtro en cada columna.
Uso (requiere openpyxl): python exportar_datos_correlacion.py --corrida RUTA_CARPETA_correlaciones_calendario
"""
import argparse, sqlite3
from pathlib import Path
import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from correlaciones_calendario_maiz import SQL, AUDIT, ONI, AMENAZAS, FASES

UNIDAD = {'pct_dias_afectados': '% días', 'pct_dias_racha_v2': '% días', 'p_menos_et0': 'mm', 'edd29': '°C·día'}
HEAD_FONT, HEAD_FILL = Font(bold=True, color='FFFFFF'), PatternFill('solid', fgColor='2F6B4F')


def hoja(wb, nombre, df, anchos=14):
    ws = wb.create_sheet(nombre[:31])
    ws.freeze_panes = 'C2'
    for i, c in enumerate(df.columns, 1):
        ws.column_dimensions[get_column_letter(i)].width = max(anchos, min(len(str(c)) + 2, 34))
    head = []
    for c in df.columns:
        cell = WriteOnlyCell(ws, value=str(c)); cell.font = HEAD_FONT; cell.fill = HEAD_FILL
        cell.alignment = Alignment(wrap_text=True, vertical='top'); head.append(cell)
    ws.append(head)
    for row in df.itertuples(index=False):
        ws.append([None if (isinstance(v, float) and not np.isfinite(v)) else v for v in row])
    ws.auto_filter.ref = f'A1:{get_column_letter(df.shape[1])}{len(df) + 1}'


def texto(wb, nombre, filas):
    ws = wb.create_sheet(nombre); ws.column_dimensions['A'].width = 34; ws.column_dimensions['B'].width = 80; ws.column_dimensions['C'].width = 45
    for f in filas:
        ws.append(list(f))


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--corrida', required=True)
    a = ap.parse_args(); run = Path(a.corrida); out = run / 'datos_para_ver'; out.mkdir(exist_ok=True)
    G = pd.read_csv(run / 'grupos_calendario.csv').set_index('pixel_id')
    plaus = set(pd.read_csv(AUDIT).query("clase in ['OK','DUDOSO_RATIO_FAO']").pixel_id)
    con = sqlite3.connect(f'file:{SQL.as_posix()}?mode=ro', uri=True)
    q = """select pixel_id, temporada, fase, fin, anio_rendimiento, rendimiento_sin_tendencia, z_rendimiento,
                  pct_dias_afectados, pct_dias_racha_v2, p_menos_et0, edd29, """ + \
        ', '.join(f'fraccion_dias_mjo_{k}' for k in range(1, 9)) + """
           from pares_v2 where alineacion = 'maturity-year' and par_amenaza_rendimiento_valido = 1"""
    d = pd.concat(pd.read_sql_query(q, con, chunksize=500_000), ignore_index=True); con.close()
    d = d[d.pixel_id.isin(plaus) & d.pixel_id.isin(G.index)]
    print(f'filas leídas: {len(d):,}', flush=True)
    keys = ['pixel_id', 'temporada']
    T = d.drop_duplicates(keys).set_index(keys)[['anio_rendimiento', 'rendimiento_sin_tendencia', 'z_rendimiento']]
    T.columns = ['anio_cosecha', 'rendimiento_sin_tendencia (t/ha)', 'z_rendimiento']
    dic = [('Columna', 'Qué es', 'De dónde sale'),
           ('pixel_id', 'Identificador del píxel GDHY de 0,5°', 'pares_v2.pixel_id'),
           ('grupo', 'Hemisferio × trimestre del mes de siembra', 'grupos_calendario.csv'),
           ('temporada', 'Año en que empieza la temporada (siembra)', 'pares_v2.temporada'),
           ('latitud, longitud', 'Centro del píxel', 'grupos_calendario.csv'),
           ('mes_siembra, mes_cosecha', 'Mes de inicio de EST y de fin de MAT (fijos en el calendario del píxel)', 'grupos_calendario.csv'),
           ('anio_cosecha', 'Año de cosecha (convención GDHY: año de cosecha)', 'pares_v2.anio_rendimiento'),
           ('rendimiento_sin_tendencia (t/ha)', 'Rendimiento GDHY menos su tendencia lineal 1981–2016', 'pares_v2.rendimiento_sin_tendencia'),
           ('z_rendimiento', 'Y de las correlaciones: rendimiento sin tendencia estandarizado por píxel', 'pares_v2.z_rendimiento')]
    for nom, col, fase, *_ in AMENAZAS:
        c = f'{nom} ({UNIDAD[col]})'
        T[c] = d[d.fase == fase].set_index(keys)[col]
        dic.append((c, f'Amenaza {nom} (tabla maestra v2)', f'pares_v2.{col} donde fase = {fase}'))
    mat = d[d.fase == 'MAT'].set_index(keys)
    f = pd.to_datetime(mat.fin)
    T['fin_MAT (cosecha)'] = f.dt.strftime('%Y-%m-%d')
    dic.append(('fin_MAT (cosecha)', 'Fecha en que termina MAT; su mes es el "mes de cosecha"', 'pares_v2.fin donde fase = MAT'))
    oni = pd.read_csv(ONI, parse_dates=['month_center'])
    oni_ym = dict(zip(oni.month_center.dt.year * 12 + oni.month_center.dt.month - 1, oni.oni))
    ym = f.dt.year * 12 + f.dt.month - 1
    for k in range(12):
        c = 'ONI mes de cosecha' if k == 0 else f'ONI mes-{k}'
        T[c] = (ym - k).map(oni_ym)
        dic.append((c, f'ONI v6 del mes que está {k} meses antes del mes de cosecha' if k else 'ONI v6 del mes de cosecha',
                    'oni_v6_monthly_centers.csv (= tabla oficial ONI v6)'))
    ids = G[['grupo', 'latitud', 'longitud', 'region', 'mes_siembra', 'mes_cosecha']]
    T = ids.join(T.reset_index().set_index('pixel_id'), how='inner').rename_axis('pixel_id').reset_index()
    T = T[['pixel_id', 'temporada'] + [c for c in T.columns if c not in ('pixel_id', 'temporada')]]
    num = T.select_dtypes('number').columns
    T[num] = T[num].round(3)
    T = T.sort_values(['grupo', 'pixel_id', 'temporada'])

    wb = Workbook(write_only=True)
    texto(wb, 'Leeme', [
        ('Datos de entrada de las correlaciones de maíz', '', ''),
        ('Corrida', run.name, ''),
        ('Una fila', 'Un píxel en una temporada (año de cosecha). Estos son exactamente los valores que entraron a la correlación.', ''),
        ('Correlación', 'Para cada píxel: Pearson entre la columna z_rendimiento y UNA columna de amenaza u ONI, con sus 34–36 años.', ''),
        ('Hojas', 'Diccionario + una hoja por grupo de calendario. La MJO está en el otro libro (datos_MJO.xlsx).', ''),
        ('Filtros', 'Cada hoja tiene filtro en el encabezado: filtra pixel_id para ver los 36 años de un píxel.', ''),
        ('Celdas vacías', 'Dato faltante en la base (no es cero).', ''),
        ('Fuente', str(SQL), ''),
    ])
    texto(wb, 'Diccionario', dic)
    for g, s in T.groupby('grupo'):
        hoja(wb, g.replace('·', '-'), s.drop(columns='grupo'))
        print(f'  hoja {g}: {len(s):,} filas', flush=True)
    wb.save(out / 'datos_amenazas_ONI.xlsx')
    print(f'Libro 1: {len(T):,} filas, {T.pixel_id.nunique():,} píxeles, {T.shape[1]} columnas', flush=True)

    M = d.drop_duplicates(keys).set_index(keys)[['anio_rendimiento']].rename(columns={'anio_rendimiento': 'anio_cosecha'})
    for fase in FASES:
        s = d[d.fase == fase].set_index(keys)
        for k in range(1, 9):
            M[f'MJO{k} en {fase}'] = s[f'fraccion_dias_mjo_{k}']
    mc = [c for c in M.columns if c.startswith('MJO')]
    M.loc[M.anio_cosecha >= 2014, mc] = np.nan
    M[mc] = M[mc].round(3)
    M = ids[['grupo']].join(M.reset_index().set_index('pixel_id'), how='inner').rename_axis('pixel_id').reset_index()
    M = M[['pixel_id', 'temporada', 'grupo', 'anio_cosecha'] + mc].sort_values(['grupo', 'pixel_id', 'temporada'])
    wb = Workbook(write_only=True)
    texto(wb, 'Leeme', [('MJO por fase del cultivo', '', ''),
                        ('Columna "MJOk en FASE"', 'Fracción (0 a 1) de los días de esa fase del cultivo en que la MJO estuvo en la fase k', 'pares_v2.fraccion_dias_mjo_k'),
                        ('Cosechas 2014–2016', 'Vacías: desde 2014 el archivo RMM no tiene removida la señal ENSO', 'encabezado de rmm_official.txt')])
    for g, s in M.groupby('grupo'):
        hoja(wb, g.replace('·', '-'), s.drop(columns='grupo'), anchos=11)
    wb.save(out / 'datos_MJO.xlsx')
    print(f'Libro 2 (MJO): {len(M):,} filas, {M.shape[1]} columnas')
    print(f'Escrito en {out}')


if __name__ == '__main__':
    main()
