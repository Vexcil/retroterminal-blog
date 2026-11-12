const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const {JSDOM}=require('jsdom');
const root=path.join(__dirname,'..');

test('closing sync settings preserves the iframe, selected source and active external playback',async()=>{
 const dom=new JSDOM(fs.readFileSync(path.join(root,'tabs.md'),'utf8'),{url:'https://retroterminal.net/tabs/',runScripts:'outside-only'});
 const w=dom.window,$=id=>w.document.getElementById(id);
 w.HTMLElement.prototype.scrollIntoView=function(){};
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
   $('tab-songsterr-toggle').click();
   assert.equal($('tab-songsterr-panel').hidden,false);
   assert.equal(w.document.activeElement,$('songsterr-query'));
   $('songsterr-close').click();
   assert.equal(playing,true);assert.equal(video.state,1);assert.equal(pauses,pauseCount);
   assert.equal(video.frame,frame);assert.equal(frame.isConnected,true);
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

test('Songsterr search works before a tab is loaded and opens duplicate-safe imports',async()=>{
 const dom=new JSDOM(fs.readFileSync(path.join(root,'tabs.md'),'utf8'),{url:'https://retroterminal.net/tabs/',runScripts:'outside-only'});
 const w=dom.window,$=id=>w.document.getElementById(id);
 w.HTMLElement.prototype.scrollIntoView=function(){};
 let imported=null,requests=[],failSearch=true;
 w.fetch=async(url,options={})=>{
   requests.push({url,options});
   if(url.includes('/api/songsterr/search')) return failSearch
     ? {ok:false,json:async()=>({error:'Search unavailable. Try again.'})}
     : {ok:true,json:async()=>({items:[{id:5532,artist:'Death',title:'Scavenger Of Human Sorrow'}]})};
   assert.equal(url,'/api/songsterr/import');
   return {ok:true,json:async()=>({file:'uploads/Death.gp',alreadyExists:true})};
 };
 w.eval(fs.readFileSync(path.join(root,'assets/tab-youtube-sync.js'),'utf8'));
 const sync=w.RetroTabSync.create({getApi:()=>null,getScore:()=>null,getItem:()=>null,getApiBase:()=>'',
   async importTab(item){imported=item;sync.beforeLoad();}});
 try {
   assert.deepEqual(Array.from(w.document.querySelectorAll('.tabs-view-actions button'),b=>b.textContent),['Library','Search tabs','YouTube','Focus view']);
   $('tab-songsterr-toggle').click();
   assert.equal($('tab-songsterr-toggle').getAttribute('aria-expanded'),'true');
   assert.equal(w.document.activeElement,$('songsterr-query'));
   $('songsterr-query').value='Death Scavenger';
   const submit=new w.Event('submit',{cancelable:true});
   await $('songsterr-search-form').onsubmit(submit);
   assert.equal(submit.defaultPrevented,true,'Enter submits the form without navigation');
   assert.match($('songsterr-status').textContent,/Search unavailable/);
   failSearch=false;
   await $('songsterr-search-form').onsubmit(new w.Event('submit'));
   assert.equal($('songsterr-results').getAttribute('aria-busy'),'false');
   assert.match($('songsterr-results').textContent,/Scavenger Of Human Sorrow/);
   await $('songsterr-results').querySelector('button[aria-label^="Import or open"]').onclick();
   assert.equal(imported.alreadyExists,true);
   assert.equal(requests.at(-1).options.method,'POST');
   assert.equal(requests.at(-1).options.credentials,'include');
   assert.deepEqual(JSON.parse(requests.at(-1).options.body),{id:'5532'});
   assert.equal($('tab-songsterr-panel').hidden,true);
   assert.equal($('tab-songsterr-toggle').getAttribute('aria-expanded'),'false');
   assert.equal(requests.some(r=>r.url.includes('/api/songsterr/sync')),false,'searching for tabs does not fetch video timing');
   $('tab-songsterr-open').click();
   $('songsterr-query').dispatchEvent(new w.KeyboardEvent('keydown',{key:'Escape',bubbles:true}));
   assert.equal($('tab-songsterr-panel').hidden,true);
   assert.equal(w.document.activeElement,$('tab-songsterr-toggle'));
   $('tab-songsterr-toggle').click();$('tab-youtube-toggle').click();
   assert.equal($('tab-songsterr-panel').hidden,true);
   assert.equal($('tab-youtube-panel').hidden,false);
 } finally { sync.beforeLoad();dom.window.close(); }
});

test('artist links scope Songsterr searches and carry the same artist to library search and pagination',async()=>{
 const dom=new JSDOM(fs.readFileSync(path.join(root,'tabs.md'),'utf8'),{url:'https://retroterminal.net/tabs/',runScripts:'outside-only'});
 const w=dom.window,$=id=>w.document.getElementById(id);w.HTMLElement.prototype.scrollIntoView=function(){};
 const requests=[];let opened;
 w.fetch=async(url)=>{
   requests.push(new URL(url,w.location.origin));
   return {ok:true,json:async()=>url.startsWith('/api/tabs')
     ? {items:[{file:'/files/death.gp',title:'Death - Symbolic',artist:'Death',song_title:'Symbolic'}],total:30,has_more:true}
     : {items:[{id:6352,artist_id:1851,artist:'Death',title:'Symbolic'}],artist_id:1851,has_more:true}};
 };
 w.eval(fs.readFileSync(path.join(root,'assets/tab-songsterr-discovery.js'),'utf8'));
 w.eval(fs.readFileSync(path.join(root,'assets/tab-youtube-sync.js'),'utf8'));
 const sync=w.RetroTabSync.create({getApi:()=>null,getScore:()=>null,getItem:()=>null,getApiBase:()=>'',openTab:async item=>{opened=item;}});
 try {
   const artist=sync.artistButton('Death');$('tab-song-artist').append(artist);await artist.onclick();
   assert.equal($('tab-songsterr-panel').hidden,false);
   assert.equal($('songsterr-artist-name').textContent,'Death');
   assert.equal(requests.at(-1).searchParams.get('artist'),'Death');
   assert.equal(requests.at(-1).searchParams.get('q'),'Death');
   await $('songsterr-results').querySelector('.tabs-artist-link').onclick();
   assert.equal(requests.at(-1).searchParams.get('artist_id'),'1851');
   await $('library-source').onclick();
   assert.equal(requests.at(-1).pathname,'/api/tabs');
   assert.equal(requests.at(-1).searchParams.get('search'),'Death');
   assert.equal(requests.at(-1).searchParams.get('search_field'),'artist');
   assert.equal(requests.at(-1).searchParams.get('artist_exact'),'1');
   assert.equal($('library-source').getAttribute('aria-pressed'),'true');
   await $('songsterr-next').onclick();
   assert.equal(requests.at(-1).searchParams.get('page'),'2');
   assert.equal(requests.at(-1).searchParams.get('artist_exact'),'1');
   await $('songsterr-results').querySelector('button[aria-label^="Open "]').onclick();
   assert.equal(opened.file,'/files/death.gp');
   assert.equal(requests.some(r=>r.pathname.endsWith('/import')),false);
   await $('songsterr-source').onclick();
   assert.equal(requests.at(-1).searchParams.get('artist_id'),'1851');
   $('songsterr-query').value='Crystal Mountain';$('songsterr-query').dispatchEvent(new w.Event('input'));
   await $('songsterr-search-form').onsubmit(new w.Event('submit'));
   assert.equal(requests.at(-1).searchParams.has('artist'),false);
   assert.equal($('songsterr-artist-filter').hidden,true);
 } finally {sync.beforeLoad();w.close();}
});

test('GameTabs source searches separately, explains login requirement and rejects stale source results',async()=>{
 const dom=new JSDOM(fs.readFileSync(path.join(root,'tabs.md'),'utf8'),{url:'https://retroterminal.net/tabs/',runScripts:'outside-only'});
 const w=dom.window,$=id=>w.document.getElementById(id);
 w.HTMLElement.prototype.scrollIntoView=function(){};
 let calls=[],late;
 w.fetch=async(url,options={})=>{
   calls.push({url,options});
   if(url.includes('gametabs')) return {ok:true,json:async()=>({items:[{id:'chrono-trigger/wind-scene',artist:'Chrono Trigger',title:'Wind Scene',url:'https://gametabs.net/chrono-trigger/wind-scene'}],page:1,has_more:false,import_available:false})};
   return new Promise(resolve=>{late=()=>resolve({ok:true,json:async()=>({items:[{id:3,artist:'Old',title:'Stale result'}]})});});
 };
 w.eval(fs.readFileSync(path.join(root,'assets/tab-youtube-sync.js'),'utf8'));
 const sync=w.RetroTabSync.create({getApi:()=>null,getScore:()=>null,getItem:()=>null,getApiBase:()=>'',importTab(){throw Error('must not import');}});
 try {
   $('songsterr-query').value='Chrono Trigger';
   const pending=$('songsterr-search-form').onsubmit(new w.Event('submit'));
   await $('gametabs-source').onclick(new w.Event('click'));
   assert.match(calls[1].url,/\/api\/gametabs\/search\?/);
   assert.equal($('gametabs-source').getAttribute('aria-pressed'),'true');
   assert.equal($('songsterr-source').getAttribute('aria-pressed'),'false');
   assert.equal($('songsterr-direct-import').hidden,true);
   assert.equal($('songsterr-results').querySelector('button').disabled,true);
   assert.match($('songsterr-status').textContent,/connected GameTabs account/);
   assert.equal($('songsterr-results').querySelectorAll('a').length,1);
   assert.equal(new URL(calls[1].url,'https://retroterminal.net').searchParams.get('q'),'');
   late();await pending;
   assert.doesNotMatch($('songsterr-results').textContent,/Stale result/);
   $('songsterr-query').value='';
   await $('library-source').onclick(new w.Event('click'));
   assert.equal($('songsterr-results').children.length,0);
   assert.equal($('songsterr-results').getAttribute('aria-busy'),'false');
 } finally {sync.beforeLoad();dom.window.close();}
});

test('GameTabs opens Top Tabs automatically and pages top and searched results',async()=>{
 const dom=new JSDOM(fs.readFileSync(path.join(root,'tabs.md'),'utf8'),{url:'https://retroterminal.net/tabs/',runScripts:'outside-only'});
 const w=dom.window,$=id=>w.document.getElementById(id);w.HTMLElement.prototype.scrollIntoView=function(){};
 const requests=[];w.fetch=async url=>{requests.push(new URL(url,'https://retroterminal.net'));return {ok:true,json:async()=>({items:[{id:'game/title',artist:'Game',title:'A long readable title',url:'https://gametabs.net/tabs/game/title'}],has_more:true,import_available:true})};};
 w.eval(fs.readFileSync(path.join(root,'assets/tab-youtube-sync.js'),'utf8'));
 const sync=w.RetroTabSync.create({getApi:()=>null,getScore:()=>null,getItem:()=>null,getApiBase:()=>''});
 try {
  $('songsterr-query').value='Old Songsterr query';await $('gametabs-source').onclick(new w.Event('click'));
  assert.equal(requests.at(-1).searchParams.get('q'),'');assert.equal(requests.at(-1).searchParams.get('page'),'1');
  assert.equal($('songsterr-query').required,false);assert.equal($('songsterr-results').querySelector('button').disabled,false);
  assert.equal($('songsterr-results').querySelectorAll('a').length,1);assert.ok($('songsterr-results').querySelector('.gametabs-result'));
  await $('songsterr-next').onclick();assert.equal(requests.at(-1).searchParams.get('page'),'2');assert.equal(requests.at(-1).searchParams.get('q'),'');
  await $('songsterr-prev').onclick();assert.equal(requests.at(-1).searchParams.get('page'),'1');
  $('songsterr-query').value='Zelda';await $('songsterr-search-form').onsubmit(new w.Event('submit'));
  await $('songsterr-next').onclick();assert.equal(requests.at(-1).searchParams.get('q'),'Zelda');assert.equal(requests.at(-1).searchParams.get('page'),'2');
 } finally {sync.beforeLoad();w.close();}
});
