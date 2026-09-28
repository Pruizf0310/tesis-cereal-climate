const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const http=require('node:http');
const {spawn}=require('node:child_process');
const root=path.join(__dirname,'..');
const manifest=JSON.parse(fs.readFileSync(path.join(root,'public/data/pixel-calendars/manifest.json')));
const rule=JSON.parse(fs.readFileSync(path.join(root,'public/data/gee_rule_audit.json'))).rules.find(r=>r.rule_id==='MAIZE_EMERGENCE_COLD6');
const regions=JSON.parse(fs.readFileSync(path.join(root,'public',manifest.crops.maize.seasons.maize__rf.regional_url)));
const cell=regions.bands[0].zones[0].members[0], [lat,lon]=cell.split(',').map(Number);
let requests=0;
const server=http.createServer(async(req,res)=>{
 res.setHeader('Content-Type','application/json');
 if(req.method==='GET'){res.end(JSON.stringify({configured:true}));return;}
 let text='';for await(const part of req)text+=part;
 const request=JSON.parse(text);requests++;
 assert.equal(request.summary_only,true);
 res.end(JSON.stringify({request,rule,annual:{evaluable:true,event_occurred:request.year===2000},provenance:{calendar_version:manifest.version,calendar_inputs:manifest.inputs,dataset:'TEST FIXTURE'}}));
});
function run(args){return new Promise((resolve,reject)=>{
 const process=spawn(global.process.execPath,[path.join(__dirname,'prepare-atlas.cjs'),...args],{cwd:root,stdio:['ignore','pipe','pipe']});let output='';
 process.stdout.on('data',d=>output+=d);process.stderr.on('data',d=>output+=d);process.on('error',reject);process.on('exit',code=>code===0?resolve(output):reject(Error(output)));
});}
(async()=>{
 const folder=fs.mkdtempSync(path.join(os.tmpdir(),'cerealrisk-atlas-test-'));
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const args=['--crop','maize','--season','maize__rf','--rule',rule.rule_id,'--first','2000','--last','2001',`--bounds=${lon-.01},${lat-.01},${lon+.01},${lat+.01}`,'--origin',`http://127.0.0.1:${server.address().port}`,'--checkpoint',path.join(folder,'resume.ndjson'),'--output',folder,'--max-requests','2','--run'];
 try{
  await run(args);assert.equal(requests,2);
  const index=JSON.parse(fs.readFileSync(path.join(folder,'index.json')));
  const layer=JSON.parse(fs.readFileSync(path.join(folder,path.basename(index.layers[0].url))));
  assert.equal(layer.cells.length,1);assert.equal(layer.cells[0][2],'10');
  await run(args);assert.equal(requests,2,'Resumed run must reuse successful annual records');
  console.log('Offline preparation: compact layer, provenance checkpoint, index and restart reuse passed.');
 }finally{server.close();}
})().catch(e=>{server.close();console.error(e);process.exitCode=1;});
