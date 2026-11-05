"""Un solo Excel de amenazas con la línea conductora completa: evidencia → 24 reglas → tabla vigente.

Hojas:
  0 Cómo se construyó · los pasos, con cuántas filas entran y salen, el criterio de cada paso y las decisiones con fecha;
  1 Evidencia          · las filas de la búsqueda (63 del corte del 17 ago 2026 + las rondas de octubre), con su tipo de
                         evidencia y el enlace al PDF;
  2 Reglas v1 (24)     · una regla por cultivo y fase (7 oct 2026) y qué pasó con cada una en la tabla vigente;
  3 Tabla vigente      · las reglas de hoy, con definición de evento, tipo de evidencia, estado y enlace al PDF;
  4 Citas              · texto exacto del PDF, página, traducción y valores en conflicto de cada regla vigente;
  Leyenda.
Entradas (no se modifican): metadata/reviewed_sources/REVISION_HUMANA_…xlsx (63 filas), amenazas/tabla_maestra_revision_humana.xlsx
(111 filas y 24 reglas), amenazas/tabla_maestra_amenazas_4cultivos_20261105.xlsx (tabla vigente),
amenazas/validacion_umbrales_20261104.xlsx («¿Cambia?» de cada regla).
Uso: python tabla_amenazas_vigente.py   → 03_Resultados/Agroclima/vigente/amenazas/AMENAZAS_vigente.xlsx
"""
from datetime import date
from pathlib import Path

import openpyxl
import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

REPO = Path(__file__).resolve().parents[2]
AM = Path('C:/Users/paola/Tesis/03_Resultados/Agroclima/vigente/amenazas')
ORIGINAL = REPO / 'metadata/reviewed_sources/REVISION_HUMANA_fases_macro_completada_SOLO_3_COLUMNAS.xlsx'
OCTUBRE = AM / '_construccion/tabla_maestra_revision_humana.xlsx'
MAESTRA = AM / '_construccion/tabla_maestra_amenazas_4cultivos_20261105.xlsx'
VALIDACION = AM / '_construccion/validacion_umbrales_20261104.xlsx'
SALIDA = AM / 'AMENAZAS_vigente.xlsx'

COLOR = {'Umbral verificado': 'FACC15', 'Modelo o parámetro': '22D3EE', 'Tratamiento experimental': 'E91E8C',
         'Asociación o indicador regional': '94A3B8', 'Transferido o tentativo': '64748B'}
# Categorías originales de la hoja «Auditoría web» → familia de la diapositiva 16 (slides_amenazas.py, FAMILIAS).
# Las categorías en español (rondas de octubre) las asigna este script; se declara en la Leyenda.
FAMILIA = {
    'Umbral verificado': ['Verified duration-response threshold', 'Verified physiological threshold', 'Verified operational threshold',
                          'Verified experimental threshold', 'Genotype-dependent operational threshold',
                          'Umbral estimado (ROC/Youden)', 'Umbral estimado (ROC)', 'Umbral formal (inflexión/curvatura)'],
    'Modelo o parámetro': ['Modeled threshold', 'Modeled threshold — provisional duration', 'Modeled cardinal parameter',
                           'Modelo mecánico; escenario, no validación por fase'],
    'Tratamiento experimental': ['Damaging experimental treatment', 'Damaging field treatment', 'Damaging two-year experimental treatment',
                                 'Damaging experimental treatment with temperature gradient', 'Tratamiento perjudicial; umbral no establecido',
                                 'Secondary-source treatment', 'Tratamiento experimental'],
    'Asociación o indicador regional': ['Seasonal observational association', 'Regional indicator', 'Indicador de exposición publicado',
                                        'Clasificación empírica; provisional', 'Clasificación ambiental; provisional'],
    'Transferido o tentativo': ['Transferred frost-damage threshold', 'Transferred candidate', 'Review-derived tentative HNT threshold',
                                'Guía técnica de daño por helada', 'Orientación técnica; no paper primario', 'Referencia técnica fisiológica',
                                'Sensibilidad de fase; criterio asumido', 'Umbral explícito; regla incompleta', 'Referencia previa; no breakpoint',
                                'Umbral de respuesta de transpiración; no umbral universal de pérdida de rendimiento']}
FAMILIA['Modelo o parámetro'] += ['Regla térmica de modelo', 'Regla térmica de modelo; homologación limítrofe']
FAMILIA['Tratamiento experimental'] += ['Exposición experimental en cámara', 'Exposición experimental con lluvia simulada',
                                        'Exposición de campo; no breakpoint']
FAMILIA['Asociación o indicador regional'] += ['Asociación estadística fase-específica', 'Indicador climático regional',
                                               'Riesgo climático de helada', 'Regla de riesgo climático con respaldo bibliográfico']
CAT_FAM = {c: f for f, cs in FAMILIA.items() for c in cs}
ORIGINALES = {c for f, cs in FAMILIA.items() for c in cs if c[:1].isupper() and c.split()[0] in
              ('Verified', 'Genotype-dependent', 'Modeled', 'Damaging', 'Secondary-source', 'Seasonal', 'Regional', 'Transferred', 'Review-derived')}
ASIGNADA = set(CAT_FAM) - ORIGINALES
HEAD = PatternFill('solid', fgColor='1E293B')
WRAP = Alignment(wrap_text=True, vertical='top')


def auditoria(f):
    a = pd.read_excel(f, sheet_name='Auditoría web', header=3)
    return a[a.Cultivo.notna()].reset_index(drop=True)


CULTIVO = dict(maize='Maíz', rice='Arroz', soybean='Soya', wheat='Trigo')


def clave(d):
    return d.Cultivo.astype(str).replace(CULTIVO) + '|' + d.Amenaza.astype(str) + '|' + d.Fuente.astype(str)


def enlaces(f, hoja, col, fila_encabezado):
    """Hipervínculos de una columna, en orden de filas de datos."""
    ws = openpyxl.load_workbook(f)[hoja]
    j = [c.value for c in ws[fila_encabezado]].index(col) + 1
    return [ws.cell(r, j).hyperlink.target if ws.cell(r, j).hyperlink else None for r in range(fila_encabezado + 1, ws.max_row + 1)]


def hoja(wb, nombre, df, anchos, links=None, colorea=None, titulo=None):
    ws = wb.create_sheet(nombre)
    r0 = 1
    if titulo:
        for t in titulo:
            ws.cell(r0, 1, t).font = Font(bold=r0 == 1, size=13 if r0 == 1 else 10)
            r0 += 1
        r0 += 1
    for j, c in enumerate(df.columns, 1):
        x = ws.cell(r0, j, c); x.font = Font(bold=True, color='FFFFFF'); x.fill = HEAD; x.alignment = WRAP
        ws.column_dimensions[get_column_letter(j)].width = anchos.get(c, 16)
    for i, fila in enumerate(df.itertuples(index=False), r0 + 1):
        for j, v in enumerate(fila, 1):
            x = ws.cell(i, j, None if pd.isna(v) else v); x.alignment = WRAP
        if links:
            for col, lista in links.items():
                t = lista[i - r0 - 1]
                if t:
                    x = ws.cell(i, list(df.columns).index(col) + 1); x.hyperlink = t; x.font = Font(color='0563C1', underline='single')
        if colorea:
            col, fam = colorea
            f = df.iloc[i - r0 - 1][fam]
            if f in COLOR:
                x = ws.cell(i, list(df.columns).index(col) + 1)
                x.fill = PatternFill('solid', fgColor=COLOR[f])
                x.font = Font(color='FFFFFF' if f in ('Tratamiento experimental', 'Transferido o tentativo') else '0F172A', bold=True)
    ws.freeze_panes = ws.cell(r0 + 1, 4)
    ws.auto_filter.ref = f'A{r0}:{get_column_letter(len(df.columns))}{r0 + len(df)}'
    return ws


def main():
    orig, octu = auditoria(ORIGINAL), auditoria(OCTUBRE)
    octu['Ronda'] = ['Corte original (17 ago 2026)' if k in set(clave(orig)) else 'Rondas de octubre (vacíos por cultivo y fase)'
                     for k in clave(octu)]
    octu['Tipo de evidencia'] = octu['Categoría de evidencia'].map(CAT_FAM).fillna('Sin clasificar')
    octu['Familia asignada por'] = ['Hoja «Auditoría web»' if c not in ASIGNADA else 'Este archivo (categoría en español)'
                                    for c in octu['Categoría de evidencia']]
    # los enlaces locales de octubre son relativos a C:/Users/paola (../../../Documents/...): se pasan a ruta absoluta
    links_ev = [('file:///C:/Users/paola/' + x.replace('../', '', 3)) if x and x.startswith('../') else x
                for x in enlaces(OCTUBRE, 'Auditoría web', 'Abrir PDF local', 4)[:len(octu)]]
    links_ev = [x if x and Path(x.replace('file:///', '')).exists() else None for x in links_ev]
    links_web = enlaces(OCTUBRE, 'Auditoría web', 'Abrir DOI/URL', 4)[:len(octu)]
    ev = octu[['Ronda', 'Cultivo', 'Fase\n código', 'Macrofase que debería corresponder', 'Amenaza', 'Umbral publicado en la web',
               'Categoría de evidencia', 'Tipo de evidencia', 'Familia asignada por', 'Fuente', 'Página\n PDF', 'Abrir PDF local',
               'Abrir DOI/URL', 'Rule ID', 'Regla utilizable / motivo de descarte', 'Limitaciones ya declaradas en la web']].rename(
        columns={'Fase\n código': 'Etapa (fuente)', 'Macrofase que debería corresponder': 'Fase homologada', 'Página\n PDF': 'Página PDF',
                 'Abrir PDF local': 'Abrir PDF', 'Abrir DOI/URL': 'Abrir en la web'})
    ev['Abrir PDF'] = ['Abrir PDF' if t else None for t in links_ev]
    ev['Abrir en la web'] = ['Abrir en la web' if t else None for t in links_web]

    t = pd.read_excel(OCTUBRE, sheet_name='Tabla maestra', header=6)
    v1 = t[t.Cultivo.notna() & t['Fase única'].notna()].iloc[:, :10].reset_index(drop=True)
    val = pd.read_excel(VALIDACION, sheet_name='Reglas')
    viejas = val[~val.ID.isin(['R02']) & (val.ID.str[1:].astype(int) <= 25)]
    fase = lambda c, f: f if f != 'REP' else ('REP-pre' if c in ('Arroz', 'Trigo') else 'REP-pos')
    hoy, ids = [], []
    for r in v1.itertuples():
        m = viejas[(viejas.Cultivo == r.Cultivo) & (viejas.Fase == fase(r.Cultivo, r[2]))]
        ids.append(', '.join(m.ID)); hoy.append(' · '.join(m['¿Cambia?'].astype(str).str.replace(' — decide Paola', '', regex=False)))
    mt = pd.read_excel(MAESTRA, sheet_name='Tabla maestra', header=2)
    mt = mt[mt.ID.notna()].reset_index(drop=True)
    estado = dict(zip(mt['Regla (Excel de validación)'].astype(str), mt['Estado de validación']))
    v1.insert(0, 'ID vigente', ids); v1['Cambio frente a v1'] = hoy
    v1['Estado hoy'] = [' · '.join(str(estado.get(i.strip(), '—')) for i in x.split(',')) for x in ids]
    v1['Cambio frente a v1'] = ['Sí (cambio aprobado)' if c == 'Propuesta' and e == 'Validada' else 'Cambio propuesto' if c == 'Propuesta' else c
                               for c, e in zip(v1['Cambio frente a v1'], v1['Estado hoy'])]
    links_mt = enlaces(MAESTRA, 'Tabla maestra', 'Abrir PDF (#page=N)', 3)[:len(mt)]
    vig = mt[['ID', 'Regla (Excel de validación)', 'Cultivo', 'Fase', 'Familia', 'Amenaza', 'Variable y estadístico exactos', 'Umbral',
              'Definición de evento (conteo)', 'Origen de la duración', 'Tipo de evidencia', 'Nivel (a/b/c/d)', 'Estado de validación',
              'Validación Paola', 'Fuente (referencia completa)', 'Página PDF', 'Abrir PDF (#page=N)', 'Valores en conflicto',
              'Observaciones']].rename(columns={'Regla (Excel de validación)': 'Regla', 'Abrir PDF (#page=N)': 'Abrir PDF'})
    vig['Abrir PDF'] = ['Abrir PDF' if x else None for x in links_mt]
    citas = mt[['ID', 'Regla (Excel de validación)', 'Cultivo', 'Fase', 'Texto exacto (copiado del PDF, re-extraído)', 'Página PDF',
                'Página impresa', 'Traducción al español (no es cita)', 'Citas complementarias (ID; ver docs/amenazas_citas_textuales.md)',
                'Valores en conflicto', 'Ruta del archivo', 'Enlace web']].rename(columns={'Regla (Excel de validación)': 'Regla'})

    fam_ev = ev['Tipo de evidencia'].value_counts(); est = vig['Estado de validación'].value_counts()
    n_orig, n_oct = int((ev.Ronda.str.startswith('Corte')).sum()), len(ev)
    pasos = pd.DataFrame([
        (1, 'Búsqueda dirigida por cultivo + fase + amenaza + umbral + impacto (no sistemática). Cada valor con fase, exposición, impacto y página.',
         f'{len(orig)} filas de evidencia', 'Corte del 17 ago 2026.', '1 Evidencia (Ronda = Corte original)'),
        (2, 'Rondas siguientes: solo los vacíos de cada cultivo y fase (frío, helada, lluvia, sequía).',
         f'{n_oct} filas ({n_oct - n_orig} nuevas)', 'Octubre 2026.', '1 Evidencia (Ronda = Rondas de octubre)'),
        (3, 'Clasificar cada valor por tipo de evidencia: no todo valor publicado es un umbral.',
         ' · '.join(f'{k} {v}' for k, v in fam_ev.items()), 'Cinco familias de la diapositiva 16; ver Leyenda.', '1 Evidencia (Tipo de evidencia)'),
        (4, 'Filtrar con seis criterios: C1 mecanismo en esa fase con cita y página; C2 variable global equivalente (ERA5-Land); C3 nivel de '
            'evidencia declarado; C4 que varíe entre años; C5 una principal por fase y familia; C6 unidad comparable.',
         f'{len(v1)} reglas v1', 'Una regla por cultivo y fase (7 oct 2026).', '2 Reglas v1 (24)'),
        (5, 'Maíz v2: se suman sequía (P − ETP < Q1) y calor continuo (EDD29); una fase puede tener hasta tres reglas.',
         'Maíz: 1–3 reglas por fase', '23 oct 2026.', '3 Tabla vigente (Maíz)'),
        (6, 'Revisión trazable: re-extraer el texto exacto de cada PDF y buscar fuentes nuevas solo donde la regla no se podía medir con dato '
            'diario de ERA5-Land.', f'{len(vig)} reglas vigentes', '4–5 nov 2026.', '3 Tabla vigente y 4 Citas'),
        (7, 'Definir el evento de cada regla: si hay fuente, se toma el dato de la fuente (su duración, o cada día si mide por día). Solo si '
            'la fuente no da unidad de tiempo, criterio de la tesis: racha ≥ 2 días (mínimo de Li 2025b, p. 4, transferido).',
         ' · '.join(f'{k} {v}' for k, v in est.items()), '5 nov 2026.', '3 Tabla vigente (Definición de evento, Origen de la duración)'),
    ], columns=['Paso', 'Qué se hizo', 'Resultado', 'Cuándo / nota', 'Dónde verlo'])
    decisiones = pd.DataFrame([
        ('3 nov 2026', 'Maíz VEG = V1–V6 (≥ 34,1 °C) + V7–VT (≥ 34,6 °C); FIL ≥ 32,9 °C (Li 2025a; el 32,7 de Li 2025b era error al citarla).'),
        ('3 nov 2026', 'Severidad del calor en maíz por duración con la Tabla 2 de Li 2025b, por etapa, en días enteros.'),
        ('4 nov 2026', 'Arroz REP-pre, FLO y FIL con Jiang 2023 (35/35/38 °C, ≥ 3 días según su método, p. 7); Jiang 2024 se descarta (cuenta días con HCIId > 0).'),
        ('4 nov 2026', 'Nuevas: sequía como racha seca P < 1 mm (ETCCDI, CDD) y calor sobre 29 °C (Schlenker y Roberts 2009).'),
        ('4 nov 2026', 'Evento del píxel = ola: días seguidos con ≥ 50 % de las 25 celdas ERA5-Land (0,1°) del píxel GDHY (0,5°) en racha; '
                       'la ola se cuenta completa y se asigna a la fase con más días.'),
        ('5 nov 2026', 'R01 validada. Jerarquía del evento: si hay fuente, el dato de la fuente; si no, racha ≥ 2 días.'),
    ], columns=['Fecha', 'Decisión'])

    wb = openpyxl.Workbook(); ws = wb.active; ws.title = '0 Cómo se construyó'
    ws['A1'] = 'Amenazas por cultivo y fase — archivo vigente'; ws['A1'].font = Font(bold=True, size=14)
    ws['A2'] = (f'Generado el {date.today():%Y-%m-%d} con scripts/agroclima/tabla_amenazas_vigente.py. Lee de arriba abajo: cada paso '
                'parte de lo que dejó el anterior. Las hojas 1 a 4 tienen el detalle de cada paso.')
    ws['A2'].alignment = WRAP; ws.merge_cells('A2:E2'); ws.row_dimensions[2].height = 32
    r = 4
    for j, c in enumerate(pasos.columns, 1):
        x = ws.cell(r, j, c); x.font = Font(bold=True, color='FFFFFF'); x.fill = HEAD
    for fila in pasos.itertuples(index=False):
        r += 1
        for j, v in enumerate(fila, 1): ws.cell(r, j, v).alignment = WRAP
    r += 2; ws.cell(r, 1, 'Decisiones con fecha').font = Font(bold=True, size=12)
    for fila in decisiones.itertuples(index=False):
        r += 1; ws.cell(r, 1, fila[0]); ws.cell(r, 2, fila[1]).alignment = WRAP; ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
    for col, w in zip('ABCDE', (12, 70, 34, 28, 34)): ws.column_dimensions[col].width = w

    hoja(wb, '1 Evidencia', ev, {'Umbral publicado en la web': 40, 'Categoría de evidencia': 28, 'Tipo de evidencia': 22, 'Fuente': 28,
                                 'Regla utilizable / motivo de descarte': 40, 'Limitaciones ya declaradas en la web': 40, 'Amenaza': 18,
                                 'Ronda': 18}, links={'Abrir PDF': links_ev, 'Abrir en la web': links_web}, colorea=('Tipo de evidencia', 'Tipo de evidencia'),
         titulo=['Paso 1–3 · Evidencia de la literatura',
                 f'{n_orig} filas del corte original (17 ago 2026) y {n_oct - n_orig} de las rondas de octubre. Cada fila es un valor publicado, no una regla.'])
    hoja(wb, '2 Reglas v1 (24)', v1, {c: 24 for c in v1.columns} | {'Cambio frente a v1': 30, 'Estado hoy': 14, 'ID vigente': 10},
         titulo=['Paso 4 · Las 24 reglas v1 (una por cultivo y fase, 7 oct 2026)',
                 '«ID vigente», «Cambio frente a v1» y «Estado hoy» dicen cómo quedó cada una en la hoja 3 (columna «Regla»).'])
    hoja(wb, '3 Tabla vigente', vig, {'Amenaza': 22, 'Variable y estadístico exactos': 26, 'Umbral': 26, 'Definición de evento (conteo)': 46,
                                      'Origen de la duración': 40, 'Tipo de evidencia': 22, 'Validación Paola': 30,
                                      'Fuente (referencia completa)': 40, 'Valores en conflicto': 40, 'Observaciones': 40},
         links={'Abrir PDF': links_mt}, colorea=('Tipo de evidencia', 'Tipo de evidencia'),
         titulo=['Pasos 5–7 · Tabla vigente de amenazas (la que se usa para contar eventos)',
                 'Estado: Validada = aprobada por Paola; Propuesta = con fuente verificada, falta su validación; Sin fuente verificable.'])
    hoja(wb, '4 Citas', citas, {'Texto exacto (copiado del PDF, re-extraído)': 70, 'Traducción al español (no es cita)': 60,
                                'Citas complementarias (ID; ver docs/amenazas_citas_textuales.md)': 30, 'Valores en conflicto': 40,
                                'Ruta del archivo': 40, 'Enlace web': 30},
         titulo=['Evidencia textual de cada regla vigente', 'Todas las citas, una por una: docs/amenazas_citas_textuales.md.'])

    ley = openpyxl.load_workbook(MAESTRA)['Leyenda']
    wl = wb.create_sheet('Leyenda')
    for row in ley.iter_rows(values_only=True):
        wl.append(list(row))
    wl.append([])
    wl.append(['Familia asignada por', 'En la hoja 1, las categorías en inglés vienen de la hoja «Auditoría web»; las categorías en español '
               '(rondas de octubre) se asignaron a una familia en este archivo: ' +
               '; '.join(f'{c} → {CAT_FAM[c]}' for c in sorted(ASIGNADA))])
    wl.column_dimensions['A'].width = 34; wl.column_dimensions['B'].width = 110
    for row in wl.iter_rows():
        for c in row: c.alignment = WRAP
    wb.save(SALIDA)
    print(SALIDA, len(ev), len(v1), len(vig))
    print(fam_ev.to_string()); print(est.to_string())


if __name__ == '__main__':
    main()
