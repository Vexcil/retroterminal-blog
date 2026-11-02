const test=require('node:test'), assert=require('node:assert/strict');
const fs=require('node:fs'), path=require('node:path'), vm=require('node:vm');
const shim={exports:{}};
vm.runInThisContext('(function(module){'+fs.readFileSync(path.join(__dirname,'../assets/tab-sync-storage.js'),'utf8')+'})')(shim);
const {canonicalFile,validSync,createStore}=shim.exports;
const copy=value=>JSON.parse(JSON.stringify(value));
const timing=(ms=1000)=>({version:1,videoId:'lUBCXGeK694',barCount:2,points:[
 {barIndex:0,barOccurence:0,barPosition:0,millisecondOffset:0},
 {barIndex:1,barOccurence:0,barPosition:0,millisecondOffset:ms} ]});
function server() {
 const records=new Map(); let fail=false, hold=null;
 async function request(method,body) {
  if(fail) throw new Error('Network unavailable');
  const key=canonicalFile(body.file), current=records.get(key)||{sync:null,revision:0};
  if(method==='GET') return copy(current);
  if(hold) await hold;
  if(body.revision!==current.revision) { const e=new Error('Conflict');e.status=409;throw e; }
  const next={sync:copy(body.sync),revision:current.revision+1}; records.set(key,next); return copy(next);
 }
 return {request,records,set fail(v){fail=v;},set hold(v){hold=v;}};
}
function device(api,file='/files/song.gp',legacy=null) {
 let local=legacy, data, state;
 const store=createStore({file,request:api.request,delay:10000,readLocal:()=>local,writeLocal:v=>{local=copy(v);},onData:v=>{data=v;},onStatus:v=>{state=v;}});
 return {store,get local(){return local;},get data(){return data;},get state(){return state;}};
}
test('Public and tailnet URLs share identity; legacy timing migrates once',async()=>{
 const api=server(), first=device(api,'https://tabs.retroterminal.net/files/a%20b.gp',timing());
 await first.store.load(); await first.store.flush(); assert.equal(first.state,'saved');
 const second=device(api,'https://vex-ser.adal-fort.ts.net:11443/files/a%20b.gp',timing(3000));
 await second.store.load(); assert.deepEqual(second.data,timing()); assert.equal(second.local.pending,false);
 assert.equal(api.records.size,1); assert.equal([...api.records.values()][0].revision,1);
});
test('Edits during a save are serialized and the latest edit survives',async()=>{
 const api=server(), d=device(api); await d.store.load();
 let release; api.hold=new Promise(r=>{release=r;});
 d.store.save(timing()); const flushing=d.store.flush(); d.store.save(timing(2000));
 api.hold=null; release(); await flushing;
 assert.deepEqual(api.records.get('/files/song.gp').sync,timing(2000));
 assert.equal(d.local.pending,false); assert.equal(d.local.revision,2);
});
test('A failed save retains its draft and retries without losing edits',async()=>{
 const api=server(), d=device(api); await d.store.load(); api.fail=true;
 d.store.save(timing()); await assert.rejects(d.store.flush(),/Network/);
 assert.equal(d.state,'error'); assert.equal(d.local.pending,true);
 api.fail=false; await d.store.retry(); assert.equal(d.state,'saved'); assert.equal(d.local.pending,false);
});
test('Pending drafts survive reopening and stale drafts do not replace newer server data',async()=>{
 const api=server(), d=device(api); await d.store.load(); d.store.save(timing());
 api.fail=true; await assert.rejects(d.store.flush()); api.fail=false;
 const reopened=device(api,'/files/song.gp',d.local); await reopened.store.load(); await reopened.store.flush();
 assert.deepEqual(api.records.get('/files/song.gp').sync,timing());
 const stale=device(api,'/files/song.gp',d.local); await stale.store.load();
 assert.equal(stale.state,'conflict'); assert.deepEqual(stale.local.sync,timing());
 await stale.store.retry(); assert.equal(stale.state,'saved'); assert.equal(stale.local.pending,false);
});
test('Two devices cannot silently overwrite each other',async()=>{
 const api=server(), a=device(api), b=device(api); await a.store.load(); await b.store.load();
 a.store.save(timing()); await a.store.flush();
 b.store.save(timing(4000)); await assert.rejects(b.store.flush(),/Conflict/);
 assert.equal(b.state,'conflict'); assert.equal(b.local.pending,true);
 assert.deepEqual(api.records.get('/files/song.gp').sync,timing());
 await b.store.retry(); assert.deepEqual(b.data,timing());
});
test('Timing validation rejects malformed browser copies',()=>{
 assert.equal(validSync(timing()),true);
 assert.equal(validSync({...timing(),barCount:true}),false);
 assert.equal(validSync(timing(-1)),false);
 assert.equal(validSync({...timing(),videoId:'https://evil.example'}),false);
});
