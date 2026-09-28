const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const load=require('./load-project-ts.cjs');
const {REFERENCE_MONTHS,calendarPosition,calendarDate}=load(path.resolve(__dirname,'../lib/calendar-display.ts'));
const {pixelWindows}=load(path.resolve(__dirname,'../lib/pixel-phenology.ts'));
const publicDir=path.resolve(__dirname,'../public');
const manifest=JSON.parse(fs.readFileSync(path.join(publicDir,'data/pixel-calendars/manifest.json')));
assert.equal(REFERENCE_MONTHS.length,24);
assert.equal(REFERENCE_MONTHS.reduce((sum,m)=>sum+m.days,0),730);
assert.equal(REFERENCE_MONTHS[12].start,365);
assert.equal(calendarDate(117,0),'27 Apr (Year 1)');
assert.equal(calendarDate(84,1),'25 Mar (Year 2)');
let count=0;
for(const crop of Object.values(manifest.crops))for(const entry of Object.values(crop.seasons)){
  const data=JSON.parse(fs.readFileSync(path.join(publicDir,entry.url)));
  for(const [cell,tuple] of Object.entries(data.pixels)){
    const windows=pixelWindows(data,...cell.split(',').map(Number));
    const positions=windows.map(calendarPosition);
    assert(Math.abs(positions[0].left-(tuple[0]-1)/730*100)<1e-10);
    for(let i=0;i<positions.length;i++){
      const p=positions[i];assert(p.left>=0&&p.width>0&&p.left+p.width<=100+1e-10);
      assert(Math.abs(p.width-windows[i].duration_days/730*100)<1e-10);
      if(i)assert(Math.abs(positions[i-1].left+positions[i-1].width-p.left)<1e-10);
    }
    count++;
  }
}
const maize=JSON.parse(fs.readFileSync(path.join(publicDir,'data/pixel-calendars/maize-maize__rf.json')));
const north=pixelWindows(maize,39.75,-95.25),south=pixelWindows(maize,-35.25,-60.75);
assert(calendarPosition(south[0]).left>calendarPosition(north[0]).left);
assert.equal(south.at(-1).end_year_offset,1);
assert.equal(north.at(-1).end_year_offset,0);
console.log(`PASS: ${count} monthly timelines, continuous positions, reference dates and north/south placement.`);
