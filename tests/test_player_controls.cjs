const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const {JSDOM}=require('jsdom');
const root=path.join(__dirname,'..');

test('closing sync settings preserves the iframe, selected source and active external playback',async()=>{
 const dom=new JSDOM(fs.readFileSync(path.join(root,'tabs.md'),'utf8'),{url:'https://retroterminal.net/tabs/',runScripts:'outside-only'});
 const w=dom.window,$=id=>w.document.getElementById(id);
 const points=[{barIndex:0,barOccurence:0,barPosition:0,millisecondOffset:0},{barIndex:1,barOccurence:0,barPosition:0,millisecondOffset:1000}];
 const saved={version:1,videoId:'M7lc1UVf-VE',barCount:2,points};
 let pauses=0,playing=false,video;
 const score={title:'Example',artist:'Artist',masterBars:[{index:0},{index:1}],exportFlatSyncPoints:()=>[],applyFlatSyncPoints:()=>{}};
 const api={tickCache:{masterBars:score.masterBars.map(masterBar=>({masterBar}))},isReadyForPlayback:true,
   playerReady:{on(){}},player:{output:{}},settings:{player:{}},masterVolume:1,
   pause(){pauses++;playing=false;},play(){playing=true;},stop(){playing=false;},updateSettings(){},updateSyncPoints(){}};
 w.alphaTab={PlayerMode:{EnabledSynthesizer:1,EnabledExternalMedia:2}};
 w.YT={PlayerState:{PLAYING:1,PAUSED:2,ENDED:0},Player:class {
   constructor(id,options){video=this;this.state=2;this.options=options;this.frame=w.document.createElement('iframe');$(id).replaceWith(this.frame);queueMicrotask(()=>options.events.onReady());}
   getDuration(){return 100;} getPlaybackRate(){return 1;} getAvailablePlaybackRates(){return [1];}
   getVolume(){return 100;} setVolume(){} cueVideoById(){} getCurrentTime(){return 5;}
   getPlayerState(){return this.state;} seekTo(){}
   playVideo(){this.state=1;this.options.events.onStateChange({data:1});}
   pauseVideo(){this.state=2;} destroy(){this.frame.remove();}
 }};
 w.RetroTabStorage={canonicalFile:file=>file,createStore(options){return {readyForEdits:true,dirty:false,conflict:false,
   load:async()=>{options.onData(saved);options.onStatus('saved');},ready:async()=>{},flush:async()=>{},save(){}};}};
 w.eval(fs.readFileSync(path.join(root,'assets/tab-youtube-sync.js'),'utf8'));
 const sync=w.RetroTabSync.create({getApi:()=>api,getScore:()=>score,getItem:()=>({title:'Example'}),getApiBase:()=>'',importTab(){}});
 try {
   sync.scoreLoaded(score,{file:'/files/example.gp'});
   await $('yt-enable').onclick();
   assert.equal(w.document.querySelector('.tabs-playback-control').dataset.source,'youtube');
   api.player.output.handler.play();
   $('tab-youtube-toggle').click();
   const frame=video.frame, pauseCount=pauses;
   $('yt-close').click();
   assert.equal($('tab-youtube-panel').hidden,true);
   assert.equal($('tab-youtube-player').hidden,false);
   assert.equal(playing,true);assert.equal(video.state,1);assert.equal(pauses,pauseCount);
   assert.equal(frame.isConnected,true);assert.equal(video.frame,frame);
   api.player.output.handler.play();
   assert.equal($('tab-youtube-panel').hidden,true,'Play must not reopen settings');
   $('yt-synth').click();
   assert.equal(w.document.querySelector('.tabs-playback-control').dataset.source,'synth');
   assert.equal(video.state,2);assert.equal(api.settings.player.playerMode,1);
   assert.equal($('yt-synth').getAttribute('aria-pressed'),'true');
   assert.equal($('yt-enable').getAttribute('aria-pressed'),'false');
   assert.equal($('tab-youtube-player').hidden,true);
   assert.ok($('tab-songsterr-open').compareDocumentPosition($('tab-upload-button')) & w.Node.DOCUMENT_POSITION_FOLLOWING);
   assert.equal($('yt-enable').closest('.tabs-playback-control'),$('tab-dock-play').parentElement);
 } finally { sync.beforeLoad();dom.window.close(); }
});
