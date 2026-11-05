"""Reglas vigentes de amenazas en formato para el código (5 nov 2026).

Lee AMENAZAS_vigente.xlsx, hoja «3 Tabla vigente» (36 reglas validadas), y escribe reglas_vigentes.csv: una fila por regla
con variable, operador, umbral numérico, tipo de evento y duración mínima, además del texto, la fuente y la página del Excel.
El Excel manda: este CSV no se edita a mano. Cada umbral numérico de ESPEC se comprueba contra el texto «Umbral» del Excel.

Tipos de evento (jerarquía de la tesis):
  racha     días seguidos que cumplen la condición; min_dias de la fuente, o 2 (criterio de la tesis, Li 2025b p. 4)
  dia       cada día que cumple la condición es un evento (la fuente evalúa día a día)
  ventana   sí/no por temporada: la condición se evalúa con un agregado de la fase
  continua  no es evento: variable acumulada (EDD29)

reglas_24_fases_vigentes.csv (v1) no se toca: lo lee maize_gee.py, que solo admite seis reglas de maíz, y queda para
reproducir las corridas de octubre.
Uso: .venv/Scripts/python.exe reglas_vigentes_csv.py
"""
import re
import shutil
from pathlib import Path

import pandas as pd

AM = Path('C:/Users/paola/Tesis/03_Resultados/Agroclima/vigente/amenazas')
REPO = Path(__file__).resolve().parents[2]
EXCEL, SALIDA = AM / 'AMENAZAS_vigente.xlsx', AM / 'reglas_vigentes.csv'
COPIA = REPO / 'outputs/agroclima_vigente/amenazas/reglas_vigentes.csv'

# id: (variable, operador, umbral, tipo de umbral, evento, min_dias)
# variables diarias ERA5-Land: tmax_c, tmin_c, tmean_c, p_mm; derivadas: teff_c = (tmean + tmax)/2, edd29 = Σ max(0, tmax − 29)
SEQ = ('p_menos_etp_suma_fase_mm', '<', None, 'Q1 1981–2016 del píxel', 'ventana', None)
ESPEC = {
    'MAI-EST-CAL': ('tmax_c', '>=', 34.0, 'fijo', 'racha', 2),
    'MAI-EST-SEQ': SEQ,
    'MAI-VEG1-CAL': ('tmax_c', '>=', 34.1, 'fijo', 'racha', 2),
    'MAI-VEG2-CAL': ('tmax_c', '>=', 34.6, 'fijo', 'racha', 2),
    'MAI-VEG-SEQ': SEQ,
    'MAI-FLO-CAL': ('tmax_c', '>=', 33.7, 'fijo', 'racha', 2),
    'MAI-FLO-SEQ': SEQ,
    'MAI-TARDIA-SECA-CALIDA': ('p_suma_y_tmean_media_fase', 'P < y T >', None, 'P < p20 y T > p80 1981–2016 del píxel', 'ventana', None),
    'MAI-EDD-29': ('edd29_cdia', 'suma', 29.0, 'base', 'continua', None),
    'MAI-REP-CAL': ('tmax_c', '>=', 33.7, 'fijo', 'racha', 2),
    'MAI-FIL-CAL': ('tmax_c', '>=', 32.9, 'fijo', 'racha', 2),
    'MAI-FIL-SEQ': SEQ,
    'MAI-MAT-LLU': ('p_mm', '>', 10.0, 'fijo', 'dia', 1),
    'MAI-RACHA-SECA': ('p_mm', '<', 1.0, 'fijo', 'racha', 2),
    'MAI-RACHA-29': ('tmax_c', '>', 29.0, 'fijo', 'racha', 2),
    'ARR-EST-CAL': ('tmean_c', '>', 35.0, 'fijo', 'racha', 2),
    'ARR-EST-FRI': ('tmin_media_30d_desde_siembra_c', '<', 12.0, 'fijo', 'ventana', None),
    'ARR-VEG-CAL': ('tmax_c', '>', 36.0, 'fijo', 'racha', 3),
    'ARR-REP-CAL': ('tmax_c', '>', 35.0, 'fijo', 'racha', 3),
    'ARR-REP-FRI': ('tmin_c', '<', 13.8, 'fijo', 'ventana', None),
    'ARR-FLO-CAL': ('tmax_c', '>', 35.0, 'fijo', 'racha', 3),
    'ARR-FLO-FRI': ('tmin_c', '<', 11.6, 'fijo', 'ventana', None),
    'ARR-FIL-CAL': ('tmax_c', '>', 38.0, 'fijo', 'racha', 3),
    'ARR-MAT-CAL': ('tmean_c', '>', 30.0, 'fijo', 'racha', 2),
    'TRI-EST-FRI': ('tmean_c', '<', 2.0, 'fijo', 'racha', 3),
    'TRI-VEG-HEL': ('tmin_c', '<=', None, 'según días desde el encañado (−4,2 a 0 °C, Feng et al. 1999)', 'dia', 1),
    'TRI-REP-HEL': ('tmin_c', '<', 0.0, 'fijo', 'dia', 1),
    'TRI-FLO-HEL': ('tmin_c', '<', 0.0, 'fijo', 'dia', 1),
    'TRI-FIL-HEL': ('tmin_c', '<', 0.0, 'fijo', 'dia', 1),
    'TRI-MAT-LLU': ('p_mm', '>=', 25.0, 'fijo', 'racha', 2),
    'SOY-EST-HEL': ('tmin_c', '<', 0.0, 'fijo', 'dia', 1),
    'SOY-FLO-CAL': ('teff_c', '>', 35.0, 'fijo', 'dia', 1),
    'SOY-REP-CAL': ('teff_c', '>', 35.0, 'fijo', 'dia', 1),
    'SOY-FIL-CAL': ('tmax_media_fase_c', '>', 30.0, 'fijo', 'ventana', None),
    'SOY-FIL-LLU': ('p_suma_R6_R8_mm', '>', 100.0, 'fijo', 'ventana', None),
    'SOY-MAT-LLU': ('p_suma_R6_R8_mm', '>', 100.0, 'fijo', 'ventana', None),
}


def numeros(texto):
    return {float(x.replace(',', '.')) for x in re.findall(r'\d+(?:[.,]\d+)?', str(texto))}


def main():
    t = pd.read_excel(EXCEL, sheet_name='3 Tabla vigente', header=3).dropna(subset=['ID'])
    if set(t.ID) != set(ESPEC):
        raise ValueError(f'Reglas distintas entre el Excel y ESPEC: {sorted(set(t.ID) ^ set(ESPEC))}')
    filas = []
    for _, r in t.iterrows():
        var, op, umbral, tipo, evento, min_dias = ESPEC[r.ID]
        if umbral is not None and umbral not in numeros(r.Umbral):
            raise ValueError(f'{r.ID}: el umbral {umbral} no aparece en el Excel («{r.Umbral}»)')
        if str(r['Estado de validación']).strip() != 'Validada':
            raise ValueError(f'{r.ID}: no está validada')
        filas.append({'id': r.ID, 'regla': r.Regla, 'cultivo': r.Cultivo, 'fase': r.Fase, 'familia': r.Familia,
                      'amenaza': r.Amenaza, 'variable': var, 'operador': op, 'umbral': umbral, 'tipo_umbral': tipo,
                      'evento': evento, 'min_dias': min_dias, 'umbral_texto': r.Umbral,
                      'definicion_evento': r['Definición de evento (conteo)'], 'origen_duracion': r['Origen de la duración'],
                      'tipo_evidencia': r['Tipo de evidencia'], 'estado': r['Estado de validación'],
                      'fuente': r['Fuente (referencia completa)'], 'pagina_pdf': r['Página PDF']})
    d = pd.DataFrame(filas)
    d['min_dias'] = d.min_dias.astype('Int64')
    d.to_csv(SALIDA, index=False, encoding='utf-8-sig')
    shutil.copy2(SALIDA, COPIA)
    print(len(d), 'reglas →', SALIDA)
    print(d.groupby(['cultivo', 'evento']).size().unstack(fill_value=0))


if __name__ == '__main__':
    main()
