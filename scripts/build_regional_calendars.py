"""Navigable regional groups, restricted to the crop inventory; no spatial averaging of dates."""
from pathlib import Path
import csv,json,math,statistics,hashlib
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'web-v2/public/data'
OUT=DATA/'regional-calendars';OUT.mkdir(exist_ok=True)
manifest=json.loads((DATA/'pixel-calendars/manifest.json').read_text())
inventory=defaultdict(set)
with (DATA/'phase_pixel_inventory.csv').open() as f:
 for r in csv.DictReader(f):inventory[r['crop']].add(f"{float(r['lat']):.2f},{float(r['lon_ee']):.2f}")
def direction(x,lat=False):return f"{abs(x):g}°{'N' if x>=0 else 'S'}" if lat else f"{abs(x):g}°{'E' if x>=0 else 'W'}"
months=['Jan–Feb','Mar–Apr','May–Jun','Jul–Aug','Sep–Oct','Nov–Dec']
total=0
for crop,meta in manifest['crops'].items():
 for season,entry in meta['seasons'].items():
  source=json.loads((DATA/entry['url'].replace('/data/','')).read_text());groups=defaultdict(list)
  for key,value in source['pixels'].items():
   if key not in inventory[crop]:continue
   lat,lon=map(float,key.split(','));latbin=math.floor(lat/10)*10;lonbin=math.floor(lon/30)*30
   import datetime
   month=(datetime.date(2001,1,1)+datetime.timedelta(days=value[0]-1)).month
   groups[(latbin,lonbin,(month-1)//2)].append(key)
  bands=defaultdict(list)
  for (latbin,lonbin,regime),keys in sorted(groups.items()):
   keys.sort();pm=statistics.median(source['pixels'][k][0] for k in keys);cm=statistics.median(source['pixels'][k][1] for k in keys)
   rep=min(keys,key=lambda k:(abs(source['pixels'][k][0]-pm)+abs(source['pixels'][k][1]-cm),k))
   # Deterministic spatial coverage, independent of climate outcomes.
   candidates=[rep];coords={k:tuple(map(float,k.split(','))) for k in keys}
   while len(candidates)<min(12,len(keys)):
    remaining=[k for k in keys if k not in candidates]
    candidates.append(max(remaining,key=lambda k:(min((coords[k][0]-coords[j][0])**2+((coords[k][1]-coords[j][1])*math.cos(math.radians(coords[k][0])))**2 for j in candidates),k)))
   cycles=sorted(source['pixels'][k][1] for k in keys)
   bands[latbin].append(dict(id=f'{latbin}_{lonbin}_{regime}',label=f'{direction(lonbin)} to {direction(lonbin+30)} · planting {months[regime]}',longitude_min=lonbin,longitude_max=lonbin+30,planting_regime=months[regime],count=len(keys),representative=rep,candidates=candidates,members=keys,cycle_range=[cycles[0],cycles[-1]],cycle_median=statistics.median(cycles)))
  payload=dict(version=manifest['version'],crop=crop,season_id=season,selection='Crop inventory intersection; 10-degree latitude bands, 30-degree longitude sectors and two-month planting regimes. Representative is the existing cell closest to median planting DOY and cycle length, not an average calendar.',bands=[dict(id=str(b),label=f'{direction(b,True)} to {direction(b+10,True)}',latitude_min=b,latitude_max=b+10,zones=z) for b,z in sorted(bands.items(),reverse=True)])
  (OUT/f'{crop}-{season}.json').write_text(json.dumps(payload,separators=(',',':'))+'\n',encoding='utf-8')
  entry['regional_url']=f'/data/regional-calendars/{crop}-{season}.json'
  total+=sum(len(z['members']) for zones in bands.values() for z in zones)
manifest['regional_selection']='Choose a latitude band, longitude sector and planting regime. Weather and calendar dates can vary within a band.'
manifest['inputs']=[i for i in manifest['inputs'] if i['path']!='web-v2/public/data/phase_pixel_inventory.csv']
manifest['inputs'].append(dict(path='web-v2/public/data/phase_pixel_inventory.csv',sha256=hashlib.sha256((DATA/'phase_pixel_inventory.csv').read_bytes()).hexdigest()))
(DATA/'pixel-calendars/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(ROOT/'docs/pixel_calendar_provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(f'{total} calendar/crop-inventory matches indexed in latitude/longitude/planting groups')
