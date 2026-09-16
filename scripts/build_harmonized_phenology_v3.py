"""Read the human audit and build grouped hazards only; never write calendar data."""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
import openpyxl

PHASES = dict(zip(['EST', 'VEG', 'FLO', 'REP', 'FIL', 'MAT'],
 ['Establishment', 'Vegetative growth', 'Flowering', 'Reproductive development', 'Grain/seed filling', 'Maturation']))
VARIABLES = dict(zip([
 'Temperatura mínima del aire', 'Potencial hídrico del suelo', 'Temperatura del aire día/noche',
 'Temperatura diurna del aire', 'Temperatura nocturna del aire', 'Temperatura máxima del aire',
 'Velocidad del viento', 'Temperatura del aire', 'Duración de sumersión', 'Temperatura media diaria',
 'Humedad del suelo', 'Precipitación diaria', 'Temperatura media del aire', 'Temperatura diaria del aire',
 'Temperatura cardinal máxima', 'Duración de inundación', 'Profundidad de agua',
 'Humedad volumétrica del suelo', 'Duración de anegamiento', 'Anomalía de temperatura nocturna', 'Intensidad de precipitación'],[
 'Minimum air temperature', 'Soil water potential', 'Day/night air temperature',
 'Daytime air temperature', 'Nighttime air temperature', 'Maximum air temperature',
 'Wind speed', 'Air temperature', 'Submergence duration', 'Daily mean temperature',
 'Soil moisture', 'Daily precipitation', 'Mean air temperature', 'Daily air temperature',
 'Maximum cardinal temperature', 'Flood duration', 'Water depth',
 'Volumetric soil moisture', 'Waterlogging duration', 'Nighttime temperature anomaly', 'Precipitation intensity']))

def codes(value):
 return list(dict.fromkeys(re.findall(r'\b(?:EST|VEG|FLO|REP|FIL|MAT)\b', str(value))))

def translate(value):
 if value is None: return None
 text = str(value)
 if text in VARIABLES: return VARIABLES[text]
 for old, new in {
  'Cada noche desde 50 % de antesis hasta madurez': 'Every night from 50% anthesis to maturity',
  'Reducción': 'Reduction', 'de reducción': 'reduction', 'por noche': 'per night',
  'noches': 'nights', 'días': 'days', 'día': 'day',
  'Umbral experimental': 'Experimental threshold', 'Umbral fisiológico': 'Physiological threshold',
  'Umbral operativo de ensayo': 'Experimental operating threshold',
  'Tratamiento perjudicial': 'Damaging experimental treatment', 'Candidato transferido': 'Transferred candidate',
  'Crítica': 'Critical', 'Alta': 'High',
 }.items(): text = text.replace(old, new)
 return text

def build(workbook, root):
 data = root / 'web-v2/public/data'
 source = json.loads((data / 'hazard_impact_v2.json').read_text(encoding='utf-8'))
 lookup = {(r['crop'], r['phase_code'], r['details']['rule_id']): r for r in source['rows']}
 sheet = openpyxl.load_workbook(workbook).worksheets[0]
 assert [sheet.cell(4,c).value for c in (20,21,22)] == ['Variable amenaza', 'Umbral exacto', 'Tiempo consecutivo']
 groups, audit = {}, []
 for cells in list(sheet)[4:]:
  v = [c.value for c in cells]
  if not v[0]: continue
  row_number = cells[0].row
  orange = any(c.fill.patternType and c.fill.fgColor.type == 'theme' and c.fill.fgColor.theme == 5 for c in cells)
  target, paper = codes(v[18]), codes(v[17])
  matched = [phase for phase in target if phase in paper]
  record = dict(row=row_number, crop=v[0], source_phase_code=v[1], rule_id=v[14],
   source=v[8], source_pages=str(v[9] or ''), orange=orange,
   calendar_phases=target, reviewed_paper_phases=paper, output_ids=[])
  audit.append(record)
  if v[14] == 'MAIZE_REP_LAG_HEAT_ZHANG2023':
   record.update(decision='reserved', reason='Literature context only. User will assign the maize REP hazard and threshold.')
   continue
  if orange or not matched:
   record['decision'] = 'reviewed_not_published'
   record['reason'] = {
    'MAIZE_EARLYFILL_HEAT42_30_6D': 'Reviewer rejects the experimental temperature contrast as an onset threshold; no accepted occurrence of this rule remains.',
    'SOY_GERMINATION_TMAX46_92': 'A modeled germination cardinal maximum is not a mortality or yield-loss threshold; no accepted occurrence of this rule remains.',
    'SOY_SEASONAL_HEAT30': 'The review supports flowering and filling; the removed original phase is unsupported or combines filling with unsupported maturity.',
    'SOY_FLOOD_DURATION6_GRAIN': 'The reviewed exposure is flowering/podding, not seed filling.',
    'WHEAT_SEEDLING_HEAT42': 'Seedling evidence belongs to EST; it does not independently support the leaf-development/tillering assignment.',
    'RICE_SUBMERGENCE_SENSITIVE7D': 'Seedling/vegetative exposure does not establish a booting REP window.',
   }[v[14]]
   continue
  base = copy.deepcopy(lookup[(v[0], v[1], v[14])])
  base.update(threshold=translate(v[4]), category=translate(base['category']),
   variable=VARIABLES[v[19]], exact_threshold=translate(v[20]), consecutive_exposure=translate(v[21]))
  if row_number == 62:
   base['category'] = 'Damaging experimental treatment'
   base['quantitative_impact'] = 'Three days did not significantly reduce final yield; 6 and 9 days did. Yield decreased by 28.8% after 9 days.'
   base['details']['limitations'] += ' The workbook value of 3 days is a treatment duration, not a demonstrated yield-loss onset threshold.'
  if row_number == 54:
   base['details']['limitations'] += ' The reviewed experiment concerns seedlings, not specifically germination/emergence; EST is the project-level correspondence.'
  record['decision'] = 'grouped'
  for phase in matched:
   key = (v[0], phase, v[14]); output_id = '/'.join(key)
   record['output_ids'].append(output_id)
   if key not in groups:
    r = copy.deepcopy(base)
    r.update(id=output_id, phase_code=phase, derived_stage=PHASES[phase])
    r['details'].update(phase_order=list(PHASES).index(phase)+1, source_assignments=[], reviewed_elsewhere=[])
    groups[key] = r
   r = groups[key]
   for field in ('variable', 'exact_threshold', 'consecutive_exposure', 'category'):
    assert r[field] == base[field], (key, field, row_number)
   r['details']['source_assignments'].append(dict(review_row=row_number,
    source_phase=f'{v[1]} — {v[2]}', source_pages=str(v[9] or ''), paper_macro_phases=paper,
    assignment_note=(
     'Only the beginning-maturity boundary R7 is supported; do not extend to R8.'
     if row_number == 52 and phase == 'MAT' else
     'Shared study window; this assignment is not an independent experiment or a phase-specific effect estimate.'
     if len(matched)>1 else
     'Biological correspondence from the reviewed paper phase to the project macro-phase.')))
 rows = sorted(groups.values(), key=lambda r:(r['crop'],r['details']['phase_order'],r['details']['rule_id']))
 for item in audit:
  retained = [r for r in rows if r['crop']==item['crop'] and r['details']['rule_id']==item['rule_id']]
  item['retained_same_evidence'] = [r['id'] for r in retained]
  if item['decision'] == 'reviewed_not_published':
   item['coverage'] = 'Same rule/source retained in the listed supported macro-phases.' if retained else 'No same-source replacement. Other evidence in this phase is not an equivalent substitute.'
   for row in retained:
    row['details']['reviewed_elsewhere'].append(dict(review_row=item['row'],original_phase=item['source_phase_code'],reason=item['reason']))
 payload = dict(version='v3.1.0-2026-09-15', source=workbook.name,
  interpretation='Grouped by crop, macro-phase and evidence rule. Original assignments and reviewed removals remain traceable. Repeated assignments are not independent evidence.',
  phases=[dict(code=k,name=v) for k,v in PHASES.items()],rows=rows)
 audit_payload = dict(workbook=workbook.name,sha256=hashlib.sha256(workbook.read_bytes()).hexdigest(),
  grouping_key=['crop','macro_phase','rule_id'],rows=audit)
 for path, content in [(data/'hazard_impact_harmonized_v3.json',payload),(root/'docs/phenology_harmonization_audit.json',audit_payload)]:
  path.write_text(json.dumps(content,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(f'{len(audit)} reviewed input rows; {len(rows)} grouped evidence rows; maize REP reserved separately.')
 return payload,audit_payload

if __name__ == '__main__':
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('workbook',type=Path)
 args=parser.parse_args()
 build(args.workbook,Path(__file__).resolve().parents[1])
