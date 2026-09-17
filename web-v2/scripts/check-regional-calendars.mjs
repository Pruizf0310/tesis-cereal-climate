import fs from 'node:fs';
import assert from 'node:assert/strict';
const root=new URL('../public/data/',import.meta.url),read=p=>JSON.parse(fs.readFileSync(new URL(p,root)));
const manifest=read('pixel-calendars/manifest.json');let total=0,groups=0;
for(const [crop,c] of Object.entries(manifest.crops))for(const [id,s] of Object.entries(c.seasons)){
 const data=read(s.url.replace('/data/','')),regions=read(s.regional_url.replace('/data/','')),seen=new Set();
 assert.equal(regions.crop,crop);assert.equal(regions.season_id,id);
 for(const b of regions.bands)for(const z of b.zones){
  groups++;assert.equal(z.count,z.members.length);assert.ok(z.members.includes(z.representative));assert.equal(z.candidates[0],z.representative);
  assert.equal(new Set(z.candidates).size,z.candidates.length);assert.equal(z.candidates.length,Math.min(12,z.count));
  assert.ok(z.candidates.every(k=>z.members.includes(k)));
  for(const key of z.members){
   assert.ok(!seen.has(key));seen.add(key);assert.ok(data.pixels[key]);
   const [lat,lon]=key.split(',').map(Number);assert.ok(lat>=b.latitude_min&&lat<b.latitude_max);assert.ok(lon>=z.longitude_min&&lon<z.longitude_max);
   assert.ok(data.pixels[key][1]>=z.cycle_range[0]&&data.pixels[key][1]<=z.cycle_range[1]);
  }
 }
 assert.equal(seen.size,Object.keys(data.pixels).length);total+=seen.size;
}
assert.equal(total,85916);
console.log('PASS:',total,'calendars partitioned once;',groups,'regional groups; candidate membership, coordinate bounds and cycle ranges verified.');
