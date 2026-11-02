const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),shim={exports:{}};
vm.runInThisContext('(function(module){'+fs.readFileSync(path.join(__dirname,'../assets/tab-songsterr-discovery.js'),'utf8')+'})')(shim);
const d=shim.exports;
const wanted=d.identity({artist:'Nirvana',title:'Come As You Are'},{title:'unused'});
const song={id:14,artist:'Nirvana',title:'Come As You Are'};
const video=(feature='Full mix',points=[0,1,2],videoId='lUBCXGeK694')=>({feature,points,videoId});
test('Names use metadata or an explicit filename delimiter and preserve arrangement qualifiers',()=>{
 assert.deepEqual(wanted,{artist:'Nirvana',title:'Come As You Are',query:'Nirvana Come As You Are'});
 assert.deepEqual(d.identity({artist:'',title:'Untitled'},{title:'Nirvana - Come As You Are.gp5'}),wanted);
 assert.deepEqual(d.identity({artist:'Nirvana',title:'Untitled'},{title:'Nirvana - Come As You Are.gp5'}),wanted);
 assert.equal(d.identity({artist:'',title:'Come As You Are'},{title:'comeasyouare'}),null);
 assert.equal(d.matchingSongs(wanted,[song,{...song,id:2,title:'Come As You Are (Unplugged)'},{...song,id:3,artist:'Another Artist'}]).length,1);
});
test('A unique exact arrangement with compatible full-mix timing is selected',async()=>{
 const calls=[];
 const result=await d.discover({wanted,count:3,request:async url=>{
  calls.push(url);return url.includes('/search')?{items:[song]}:{...song,revision:7,videos:[video('backing',[0,1,2,3,4]),video('alternative',[0,1,2],'M7lc1UVf-VE'),video()]};
 }});
 assert.equal(result.kind,'match'); assert.equal(result.video.feature,'Full mix'); assert.equal(calls.length,2);
});
test('Wrong bar counts and multiple plausible recordings are never silently selected',async()=>{
 const run=videos=>d.discover({wanted,count:3,knownId:14,request:async()=>({...song,videos})});
 assert.equal((await run([video('Full mix',[0,1,2,3,4])])).kind,'none');
 assert.equal((await run([video('alternative'),video('alternative',[0,2,3],'M7lc1UVf-VE')])).kind,'choices');
 assert.equal((await run([video('backing')])).kind,'choices');
});
test('Multiple matching arrangements require a choice even when counts match',async()=>{
 const result=await d.discover({wanted,count:3,request:async url=>url.includes('/search')?{items:[song,{...song,id:15}]}:{...song,id:Number(url.split('=').pop()),videos:[video()]}});
 assert.equal(result.kind,'choices'); assert.equal(result.songs.length,2);
});
test('Known imported song ID skips name search; aborting discards a late result',async()=>{
 const urls=[],controller=new AbortController();
 const result=await d.discover({wanted:null,count:3,knownId:14,request:async url=>{urls.push(url);return {...song,videos:[video()]};}});
 assert.equal(result.kind,'match');assert.deepEqual(urls,['/api/songsterr/sync?id=14']);
 await assert.rejects(d.discover({wanted,count:3,knownId:14,signal:controller.signal,request:async()=>{controller.abort();return {...song,videos:[video()]};}}),{name:'AbortError'});
});
test('No exact match does not start timing downloads; malformed points cannot be selected',async()=>{
 let count=0;
 assert.equal((await d.discover({wanted,count:3,request:async()=>{count++;return {items:[{...song,title:'Come As You Are (Live)'}]};}})).kind,'none');
 assert.equal(count,1);
 assert.deepEqual(d.compatibleVideos([video('Full mix',[0,2,1]),video('Full mix',[0,NaN,2])],3),[]);
});
