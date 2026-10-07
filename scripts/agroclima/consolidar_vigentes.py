"""Consolidate the user's thesis outputs; preserve original workbooks byte-for-byte."""
import csv, hashlib, json, shutil, zipfile
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

WORK = Path(r'C:/Users/paola/Documents/ChatGPT/Tesis')
THESIS = Path(r'C:/Users/paola/Tesis')
REPO = THESIS/'Repositorio/tesis-cereal-climate'
CURRENT = THESIS/'03_Resultados/Agroclima/vigente'
VERSION = '2026-10-07'
REPO_OUT = REPO/'outputs/agroclima_vigente'
NS = {'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    assert sha(source) == sha(target), target

def rows_excel(path):
    with zipfile.ZipFile(path) as z:
        strings=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            strings=[''.join(el.itertext()) for el in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',NS)]
        root=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        rows=[]
        for row in root.findall('s:sheetData/s:row',NS):
            n=int(row.attrib['r'])
            if not 8<=n<=31: continue
            record={}
            for cell in row:
                value=cell.find('s:v',NS); kind=cell.attrib.get('t')
                text=strings[int(value.text)] if kind=='s' and value is not None else ''.join(cell.find('s:is',NS).itertext()) if kind=='inlineStr' else value.text if value is not None else ''
                record[''.join(c for c in cell.attrib['r'] if c.isalpha())]=text
            rows.append(record)
        return rows

def save_csv(path, rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

CURRENT.mkdir(parents=True,exist_ok=True)
selection={'version':VERSION,'water_system':'rf','water_label':'Secano',
    'seasons':{'maize':['maize__rf'],'soybean':['soybean__rf'],
               'rice':['rice_1__rf','rice_2__rf'],'wheat':['spring_wheat__rf','winter_wheat__rf']},
    'wheat_status':'Spring/winter alternatives retained; one type must be selected for the calculation, not both as independent yields.',
    'rice_note':'Two source seasons retained as temporada 1 and temporada 2. They are not asserted to be meteorological summer/winter everywhere.',
    'yield_note':'GDHY input is annual and does not separate these rice seasons; calculate exposures separately and do not duplicate the annual yield as independent observations.',
    'calendar_status':'Current adopted operational calendar; intermediate phase dates are estimates, not annual observations.'}
cal=CURRENT/'calendario';cal.mkdir(exist_ok=True)
source=REPO/'web-v2/public/data/pixel-calendars'
manifest=json.loads((source/'manifest.json').read_text())
copy(source/'manifest.json',cal/'manifest.json')
copy(REPO/'metadata/six_phase_correspondence_v4.json',cal/'six_phase_correspondence_v4.json')
copy(REPO/'docs/pixel_calendar_provenance.json',cal/'provenance_fuente.json')
copy(REPO/'docs/pixel_calendar_method.md',cal/'metodo_fuente.md')
(cal/'seleccion_vigente.json').write_text(json.dumps(selection,indent=2,ensure_ascii=False),encoding='utf8')
calendar_rows=[];stats={}
for crop,seasons in selection['seasons'].items():
    for season in seasons:
        entry=manifest['crops'][crop]['seasons'][season]
        file=Path(entry['url']).name;copy(source/file,cal/file)
        d=json.loads((cal/file).read_text());count=0
        for key,values in d['pixels'].items():
            lat,lon=map(float,key.split(',')); phases={}
            for i,stage in enumerate(d['templates']):
                assert len(stage['macro_phases'])==1
                macro=stage['macro_phases'][0];start,end=values[3+i],values[4+i]
                rec=phases.setdefault(macro,{'start':start,'end':start,'original':[]})
                assert rec['end']==start
                rec['end']=end;rec['original'].append(stage['code'])
            assert len(phases)==6
            chronological=sorted(phases.items(),key=lambda r:r[1]['start'])
            assert chronological[0][1]['start']==0
            assert chronological[-1][1]['end']==values[1]
            for a,b in zip(chronological,chronological[1:]):assert a[1]['end']==b[1]['start']
            for code,p in chronological:
                a,b=values[0]-1+p['start'],values[0]-1+p['end']-1
                calendar_rows.append(dict(crop=crop,season_id=season,water_system='rf',lat=lat,lon=lon,
                    phase=code,start_doy=a%365+1,end_doy=b%365+1,start_year_offset=a//365,
                    end_year_offset=b//365,start_offset=p['start'],end_offset_exclusive=p['end'],
                    duration_days=p['end']-p['start'],cycle_days=values[1],uncertainty_days=values[2],
                    original_stages=';'.join(p['original']),version=manifest['version'],
                    status='estimated_intermediate_dates'))
            count+=1
        stats[season]=count
save_csv(cal/'calendario_seis_fases_secano.csv',calendar_rows)

threats=CURRENT/'amenazas';threats.mkdir(exist_ok=True)
manual=THESIS/'03_Resultados/Fenologia/REVISION_HUMANA_fases_macro_completada_SOLO_3_COLUMNAS.xlsx'
documental=WORK/'outputs/01a112f0-f212-7130-a752-c0d1dfa88f6e/REVISION_HUMANA_fases_macro_completada_SOLO_3_COLUMNAS.xlsx'
copy(manual,threats/'tabla_maestra_revision_humana.xlsx')
copy(documental,threats/'revision_documental_24_fragmentos_exactos.xlsx')
doc={(r.get('A'),r.get('B')):r for r in rows_excel(documental)}
fields=['cultivo','fase','amenaza','variable_estadistico','umbral','duracion','conteo_eventos','estado','fuente','limites','auditoria']
rules=[];differences=[]
for r in rows_excel(manual):
    key=(r.get('A'),r.get('B'));q=doc[key]
    out={name:r.get(chr(65+i),'') for i,name in enumerate(fields)}
    out.update(fragmento_literal=q.get('L',''),ubicacion=q.get('M',''),fuentes_por_componente=q.get('O',''),
               nota_revision_documental=q.get('J',''),duracion_revision_documental=q.get('F',''),
               version=VERSION,estado_revision='pendiente_corroboracion_humana')
    rules.append(out)
    for col in ['C','D','E','F','G','H','I','J']:
        if r.get(col,'')!=q.get(col,''):
            differences.append(dict(cultivo=key[0],fase=key[1],columna=col,
                revision_humana=r.get(col,''),revision_documental=q.get(col,''),
                accion='Conservar ambas; no sobrescribir silenciosamente la revisión humana.'))
assert len(rules)==24 and len({(r['cultivo'],r['fase']) for r in rules})==24
save_csv(threats/'reglas_24_fases_vigentes.csv',rules)
if differences:save_csv(threats/'diferencias_revision_documental.csv',differences)
diagnostics=CURRENT/'diagnosticos';diagnostics.mkdir(exist_ok=True)
for name in ['netcdf_inventory.json','pixeles_GDHY.csv','comparacion_pixeles_correlacion.json']:
    copy(WORK/'work_climate'/name,diagnostics/name)

script=THESIS/'02_Scripts/agroclima/pipeline_amenazas';script.mkdir(parents=True,exist_ok=True)
for name in ['pipeline.py','requirements.txt','test_eventos.py','EJECUTAR.ps1','LEEME.md']:
    copy(WORK/'pipeline_amenazas'/name,script/name)
c=json.loads((WORK/'pipeline_amenazas/config.json').read_text())
c.update(calendar_dir=str(cal),calendar_selection_confirmed=True,water_system='rf',
    output=str(CURRENT/'ejecuciones/piloto_maize_EST'),
    repository_results=str(REPO_OUT/'ejecuciones/piloto_maize_EST'))
c.pop('calendar_csv',None)
(script/'config.json').write_text(json.dumps(c,indent=2,ensure_ascii=False),encoding='utf8')
(WORK/'pipeline_amenazas/config.json').write_text(json.dumps(c,indent=2,ensure_ascii=False),encoding='utf8')

readme='''# Resultados vigentes: amenazas y calendario

Versión de consolidación: 2026-10-07. Esta carpeta es el punto de entrada vigente de la tesis.

## Calendario adoptado

`calendario/calendario_seis_fases_secano.csv` contiene las seis ventanas por píxel, preservadas desde los JSON del repositorio, versión regional-v4-2026-09-16. Se conserva cada archivo fuente, manifiesto y correspondencia. Riego queda fuera de esta selección.

Maíz y soya: temporada única disponible. Arroz: temporada 1 y temporada 2, ambas de secano; no se interpretan universalmente como invierno/verano meteorológico. Trigo: alternativas primavera/invierno conservadas; la elección de un solo tipo sigue pendiente. No combinar sus rendimientos como observaciones independientes.

Es un calendario operativo coherente adoptado para el cálculo, no fenología anual observada. Las fechas intermedias son estimadas. Año base = año de siembra; verificar asociación con año de rendimiento antes del análisis estadístico. La tabla CSV es una vista auditable; para ejecutar se usan los JSON con límites semiabiertos, incluidos años bisiestos.

## Amenazas

`amenazas/tabla_maestra_revision_humana.xlsx` preserva la versión actual de la carpeta Fenologia y toda la auditoría, comentarios y colores, sin alteraciones.

`amenazas/revision_documental_24_fragmentos_exactos.xlsx` recupera la entrega con citas literales, páginas y procedencia por componente que había quedado fuera de la carpeta de tesis.

`amenazas/reglas_24_fases_vigentes.csv` reúne las 24 reglas de la tabla humana con los fragmentos de la revisión documental. `diferencias_revision_documental.csv` registra discrepancias entre las dos entregas; las aclaraciones documentales no se convierten silenciosamente en reglas aprobadas. La frecuencia de eventos todavía no se ha calculado en GEE.

## Código, resultados y repositorio

Código ejecutable: `C:/Users/paola/Tesis/02_Scripts/agroclima/pipeline_amenazas/`.

Piloto: maíz EST, Tmax >=34 °C, >=2 días consecutivos; tres píxeles, 1981–1983. Usa calendario por píxel de secano, con la correspondencia v4. Falta configurar ID de proyecto GEE y autenticar. El día climático de este piloto es UTC.

Todos los nuevos archivos del piloto se escriben en `ejecuciones/piloto_maize_EST/`. Las salidas derivadas y reportes se copian también a `C:/Users/paola/Tesis/Repositorio/tesis-cereal-climate/outputs/agroclima_vigente/`. El clima bruto permanece en tesis; GitHub recibe su procedencia y resultados derivados, evitando subir las bases científicas masivas.

El repositorio actualizado de trabajo está en `C:/Users/paola/Tesis/Repositorio/tesis-cereal-climate/`. No continuar desde la copia antigua de Documents/Codex sin actualizarla. Versionar las nuevas salidas requiere commit/push; el pipeline no publica automáticamente resultados no revisados. La web no se modifica con esta consolidación.

`diagnosticos/` contiene inventarios GDHY y la comparación con los píxeles de correlación. No son conteos climáticos.
'''
(CURRENT/'LEEME_VIGENTE.md').write_text(readme,encoding='utf8')
verification=dict(version=VERSION,repository_base_commit='4fe1be652b8cc0ae94aa785feb05f5ef9686c4e3',
    selection=selection,calendar_version=manifest['version'],calendar_counts=stats,
    calendar_rows=len(calendar_rows),calendar_continuity='PASS',rules=24,
    workbook_originals_preserved=True,documentary_difference_cells=len(differences),
    gee_execution='NOT_STARTED',outputs={})
for p in CURRENT.rglob('*'):
    if p.is_file():verification['outputs'][str(p.relative_to(CURRENT)).replace('\\','/')]=sha(p)
(CURRENT/'manifest_vigente.json').write_text(json.dumps(verification,indent=2,ensure_ascii=False),encoding='utf8')
# Only small/current artifacts. Scientific climate cache is deliberately not copied to Git.
for p in CURRENT.rglob('*'):
    if p.is_file() and 'clima' not in p.relative_to(CURRENT).parts:
        copy(p,REPO_OUT/p.relative_to(CURRENT))
for p in script.iterdir():
    if p.is_file():copy(p,REPO/'scripts/agroclima/pipeline_amenazas'/p.name)
(THESIS/'03_Resultados/Agroclima/LEEME_VIGENTE.md').write_text(readme,encoding='utf8')
print(json.dumps({k:v for k,v in verification.items() if k!='outputs'},indent=2,ensure_ascii=False))
