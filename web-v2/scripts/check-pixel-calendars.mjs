import fs from 'node:fs';
import assert from 'node:assert/strict';
import ts from 'typescript';
const compile=path=>ts.transpileModule(fs.readFileSync(new URL(path,import.meta.url),'utf8'),{compilerOptions:{module:ts.ModuleKind.ESNext}}).outputText;
const uri=text=>'data:text/javascript;base64,'+Buffer.from(text).toString('base64');
const macro=uri(compile('../lib/macro-phases.ts'));
const {pixelWindows,phaseDates}=await import(uri(compile('../lib/pixel-phenology.ts').replace("'./macro-phases'",JSON.stringify(macro))));
const dir=new URL('../public/data/pixel-calendars/',import.meta.url);
const manifest=JSON.parse(fs.readFileSync(new URL('manifest.json',dir)));
let n=0,shared=0;
for(const crop of Object.values(manifest.crops)) for(const season of Object.values(crop.seasons)) {
 const data=JSON.parse(fs.readFileSync(new URL(season.url.split('/').pop(),dir)));
 for(const [key,tuple] of Object.entries(data.pixels)) {
  const [lat,lon]=key.split(',').map(Number);const windows=pixelWindows(data,lat,lon);
  assert.equal(windows.length,data.crop==='wheat'?6:5); const covered=new Set();
  assert.equal(windows[0].start_offset,0);
  for(let i=1;i<windows.length;i++){
   assert.equal(windows[i-1].end_offset,windows[i].start_offset);
   for(const year of [1999,2000,2001])assert.equal(phaseDates(year,windows[i-1]).endExclusive.getTime(),phaseDates(year,windows[i]).start.getTime());
  }
  for(const w of windows) {
   assert.ok(w.duration_days>0);assert.equal(w.end_offset-w.start_offset,w.duration_days);
   for(let day=w.start_offset;day<w.end_offset;day++){assert.ok(!covered.has(day),'No day may belong to two intervals');covered.add(day);}
   const dates=phaseDates(2000,w);assert.ok(dates.start<=dates.end);
   assert.ok(dates.expectedDays===w.duration_days||dates.expectedDays===w.duration_days+1);
   if(w.shared)shared++;
  }
  assert.equal(covered.size,tuple[1]);assert.equal(Math.min(...covered),0);assert.equal(Math.max(...covered),tuple[1]-1);
  n++;
 }
}
assert.equal(n,85916);
console.log(`PASS: ${n} exact-coordinate calendars, consecutive nonoverlapping intervals, ${shared} explicitly combined intervals; complete cycle and leap-year checks passed.`);
