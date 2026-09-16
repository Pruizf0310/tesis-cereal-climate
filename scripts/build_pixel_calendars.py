"""Build coordinate-specific windows from the archived calendar matrix and Excel crosswalk."""
import csv, gzip, hashlib, json, re
from pathlib import Path
import openpyxl

ROOT = Path(__file__).resolve().parents[1]
CALENDAR = ROOT/'outputs/fenologia_v1/tabla_maestra_fenologia_global_v1.xlsx'
MATRIX = CALENDAR.with_suffix('.csv.gz')
REVIEW = ROOT/'metadata/reviewed_sources/REVISION_HUMANA_fases_macro_completada_SOLO_3_COLUMNAS.xlsx'
OUT = ROOT/'web-v2/public/data/pixel-calendars'
OUT.mkdir(exist_ok=True)
catalog_book = openpyxl.load_workbook(CALENDAR, read_only=True, data_only=True)
catalog_rows = list(catalog_book['Catálogo fases'].values)
headers = [str(v).lstrip('\ufeff') for v in catalog_rows[0]]
catalog = [dict(zip(headers, row)) for row in catalog_rows[1:] if row[0]]
review_book = openpyxl.load_workbook(REVIEW, read_only=True, data_only=True)
crosswalk = list(review_book['Hoja1'].values)
names = dict((row[0], row[1]) for row in crosswalk[1:7])
labels = {'maize':'Maize','rice':'Rice','soybean':'Soybean','wheat':'Wheat'}
columns = {'maize':1,'rice':2,'soybean':3,'wheat':4}
english = json.loads((ROOT/'web-v2/public/data/phenology_technical_v2.json').read_text())
phase_names = {c['id']:{p['code']:p['name'] for p in c['bands'][0]['phases']} for c in english['crops']}
templates = {}
for crop in labels:
 templates[crop] = []
 for row in sorted([r for r in catalog if r['crop']==crop],key=lambda r:int(r['phase_order'])):
  code = row['phase_code']
  mapped = [str(r[0])[:3] for r in crosswalk[10:16] if re.search(r'(?<![A-Z0-9_])'+re.escape(code)+r'(?![A-Z0-9_])',str(r[columns[crop]]))]
  assert mapped, (crop,code)
  templates[crop].append(dict(code=code,name=phase_names[crop][code],macro_phases=mapped,
    fraction_start=float(row['fraction_start']),fraction_end=float(row['fraction_end']),
    timing_basis='Estimated from normalized cycle fractions; not observed phase dates',
    workbook_sheet='Catálogo fases',crosswalk_sheet='Hoja1'))

seasons = {}
count = 0
with gzip.open(MATRIX,'rt',encoding='utf-8-sig') as stream:
 for row in csv.DictReader(stream):
  crop=row['crop']; season_id=row['season']+'__'+row['water_system']; key=f"{float(row['latitude']):.2f},{float(row['longitude']):.2f}"
  season=seasons.setdefault((crop,season_id),{})
  p=int(row['calendar_planting_doy']); start=int(row['phase_start_doy']); dur=int(row['phase_duration_days']); index=int(row['phase_order'])-1
  # Store actual technical intervals from the archived matrix, not reconstructed rounding.
  offset=(start-p)%365
  value=season.setdefault(key,dict(planting_doy=p,cycle_days=int(row['cycle_days_inclusive']),uncertainty_days=int(row['uncertainty_days']),bounds=[None]*8))
  assert value['bounds'][index] is None
  value['bounds'][index]=[offset,offset+dur] # half-open, relative to planting
  count+=1
for (crop,season_id), pixels in seasons.items():
 for key,value in pixels.items():
  bounds=value['bounds']; assert bounds[0][0]==0 and bounds[-1][1]==value['cycle_days'],key
  assert all(a[1]==b[0] for a,b in zip(bounds,bounds[1:])),key
 # Compact tuple: planting day, inclusive cycle duration, uncertainty, nine exclusive boundaries.
 compact={k:[v['planting_doy'],v['cycle_days'],v['uncertainty_days'],*[b[0] for b in v['bounds']],v['bounds'][-1][1]] for k,v in pixels.items()}
 payload=dict(crop=crop,season_id=season_id,templates=templates[crop],pixels=compact)
 (OUT/f'{crop}-{season_id}.json').write_text(json.dumps(payload,separators=(',',':'))+'\n')
manifest=dict(version='2026-09-16',source='GGCMI Phase 3 v1.01 endpoints and archived normalized phase estimates',
 source_doi='10.5281/zenodo.5062513',phases=[dict(code=k,name=v) for k,v in names.items()],
 shared_window_policy='Unite macro-phases with unresolved internal boundaries into one consecutive interval. Each day is counted exactly once; multiple triggers may be evaluated in the united window. No invented temporal split.',
 crops={crop:dict(label=label,seasons={sid:dict(label=sid.split('__')[0].replace('_',' ').title(),water_system=sid.split('__')[1],water_label='Rainfed' if sid.endswith('__rf') else 'Irrigated',url=f'/data/pixel-calendars/{crop}-{sid}.json',pixel_count=len(pixels)) for (c,sid),pixels in seasons.items() if c==crop}) for crop,label in labels.items()},
 inputs=[dict(path=str(p.relative_to(ROOT)).replace('\\','/'),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in (CALENDAR,MATRIX,REVIEW)])
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(ROOT/'docs/pixel_calendar_provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(f'Validated {count} original phase rows and {sum(len(p) for p in seasons.values())} coordinate calendars; {len(seasons)} season files.')
