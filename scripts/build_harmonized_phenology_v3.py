import json,re,copy,hashlib
from pathlib import Path
import openpyxl
import argparse
p=argparse.ArgumentParser(description='Build reviewed macro-phase data from a read-only workbook')
p.add_argument('workbook', type=Path)
args=p.parse_args()
root=Path(__file__).resolve().parents[1]
data=root/'web-v2/public/data'
book=args.workbook
sheet=openpyxl.load_workbook(book).worksheets[0]
names=dict(zip(['EST','VEG','FLO','REP','FIL','MAT'],['Establishment','Vegetative growth','Flowering','Reproductive development','Grain/seed filling','Maturation']))
def codes(v): return list(dict.fromkeys(re.findall(r'\b(?:EST|VEG|FLO|REP|FIL|MAT)\b',str(v))))
def english(v):
 if isinstance(v,dict): return {k:english(x) for k,x in v.items()}
 if isinstance(v,list): return [english(x) for x in v]
 if isinstance(v,str):
  for a,b in {'día':'day','de reducción':'reduction','Umbral experimental':'Experimental threshold','Umbral fisiológico':'Physiological threshold','Umbral operativo de ensayo':'Experimental operating threshold','Tratamiento perjudicial':'Damaging experimental treatment','Candidato transferido':'Transferred candidate','Crítica':'Critical','Alta':'High'}.items(): v=v.replace(a,b)
 return v
h=json.loads((data/'hazard_impact_v2.json').read_text(encoding='utf-8'))
lookup={(r['crop'],r['phase_code'],r['details']['rule_id']):r for r in h['rows']}
out=[]; audit=[]
for cells in list(sheet)[4:]:
 v=[c.value for c in cells]
 if not v[0]: continue
 excluded=any(c.fill.patternType and c.fill.fgColor.type=='theme' and c.fill.fgColor.theme==5 for c in cells)
 a={'row':cells[0].row,'crop':v[0],'source_phase_code':v[1],'rule_id':v[14],'excluded_orange':excluded}
 audit.append(a)
 if excluded or v[14]=='MAIZE_REP_LAG_HEAT_ZHANG2023': continue
 r=copy.deepcopy(lookup[(v[0],v[1],v[14])])
 target=codes(v[18]); supported=codes(v[17]); matched=[c for c in target if c in supported]
 a['target_phases']=target; a['paper_phases']=supported; a['assigned_phases']=matched
 if not matched: a['excluded_reason']='No supported phase overlap'; continue
 r['phase_code']='+'.join(matched); r['derived_stage']=' / '.join(names[c] for c in matched)
 r['threshold']=v[4]
 d=r['details']; d['phase_order']=min(list(names).index(c)+1 for c in matched)
 d['source_phase']=f"{v[1]} — {v[2]}"; d['review_row']=str(cells[0].row); d['source_pages']=str(v[9] or '')
 d['homologation']='Project crosswalk: '+ '+'.join(supported)+' reported in the reviewed study; '+ '+'.join(target)+' in the original calendar. Assigned overlap: '+ '+'.join(matched)+'.'
 if len(matched)>1: d['homologation']+=' Shared window; no separate phase duration or independent effect is inferred.'
 if v[14]=='WHEAT_WATERLOG_Z65_3D':
  r['threshold']='Waterlogging treatments of 3, 6 and 9 days, starting at Zadoks 65, with 2 cm of water above the soil.'
  r['quantitative_impact']='Three days did not significantly reduce final yield; 6 and 9 days did. Yield decreased by 28.8% after 9 days.'
  r['category']='Damaging experimental treatment'
 out.append(english(r))
h.update(version='v3.0.0-2026-09-15',source='Human-reviewed workbook; orange-marked rows excluded; project macro-phase crosswalk',rows=out)
(data/'hazard_impact_harmonized_v3.json').write_text(json.dumps(h,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
maps={
'maize': ['EST','VEG','VEG','FLO+REP','FIL','FIL','FIL','MAT'],
'rice':['EST','VEG','VEG','VEG+REP','REP','FLO','FIL','MAT'],
'soybean':['EST','VEG','FLO','REP','REP','FIL','FIL+MAT','MAT'],
'wheat':['EST','VEG','VEG','REP','REP','FLO','FIL','MAT']}
c=json.loads((data/'phenology_technical_v2.json').read_text(encoding='utf-8'))
for crop in c['crops']:
 for band in crop['bands']:
  groups={}
  for phase,key in zip(band['phases'],maps[crop['id']],strict=True):
   if key not in groups: groups[key]={'code':key,'name':' / '.join(names[k] for k in key.split('+')),'order':min(list(names).index(k)+1 for k in key.split('+')),'average_duration_days':0,'average_days_by_month':[0]*12,'source_stages':[]}
   g=groups[key]; g['average_duration_days']+=phase['average_duration_days']; g['average_days_by_month']=[a+b for a,b in zip(g['average_days_by_month'],phase['average_days_by_month'],strict=True)]; g['source_stages'].append(phase['code']+' — '+phase['name'])
  band['phases']=list(groups.values())
c['version']='v3.0.0-2026-09-15'
c['warning']='Intermediate dates remain operational estimates. Combined macro-phase windows are retained where the original calendar cannot separate them; days are never duplicated or split without evidence.'
(data/'phenology_harmonized_v3.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(root/'docs/phenology_harmonization_audit.json').write_text(json.dumps({'workbook':book.name,'sha256':hashlib.sha256(book.read_bytes()).hexdigest(),'rows':audit},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Published',len(out),'rows; excluded orange',sum(a['excluded_orange'] for a in audit))
