const test=require('node:test'), assert=require('node:assert/strict');
const fs=require('node:fs'), path=require('node:path'), vm=require('node:vm');
const shim={exports:{}};
vm.runInThisContext('(function(module){'+fs.readFileSync(path.join(__dirname,'../assets/tab-youtube-sync.js'),'utf8')+'})')(shim);
const core=shim.exports;
test('YouTube URLs are parsed with a host allowlist',()=>{
 assert.equal(core.videoId('https://youtu.be/lUBCXGeK694?t=3'),'lUBCXGeK694');
 assert.equal(core.videoId('https://www.youtube.com/watch?v=lUBCXGeK694'),'lUBCXGeK694');
 assert.equal(core.videoId('https://evil.example/watch?v=lUBCXGeK694'),null);
 assert.equal(core.videoId('javascript:alert(1)'),null);
});
test('Repeat occurrences preserve playback order',()=>{
 const score={masterBars:[{index:0},{index:1}]};
 const bars=core.timeline({tickCache:{masterBars:[{masterBar:score.masterBars[0]},{masterBar:score.masterBars[1]},{masterBar:score.masterBars[0]}]}},score);
 assert.deepEqual(bars.map(b=>[b.barIndex,b.barOccurence]),[[0,0],[1,0],[0,1]]);
 assert.equal(core.importedPoints([1,2,4],bars)[2].barOccurence,1);
 assert.equal(core.importedPoints([1,2,4,6],bars)[3].barPosition,1);
 assert.throws(()=>core.importedPoints([1,2],bars),/arrangement/);
 assert.throws(()=>core.importedPoints([1,2,1],bars),/invalid/);
 assert.throws(()=>core.importedPoints([1,NaN,4],bars),/invalid/);
});
