const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {JSDOM}=require('jsdom');
const root=path.join(__dirname,'..'),page=fs.readFileSync(path.join(root,'tabs.md'),'utf8');
const access=fs.readFileSync(path.join(root,'assets/tab-access.js'),'utf8');
function section(start,end){return page.slice(page.indexOf(start),page.indexOf(end,page.indexOf(start)));}
function harness(){
 const d=new JSDOM(page,{url:'https://retroterminal.net/tabs/',runScripts:'outside-only'}),w=d.window;
 w.eval(`let libraryScope='mine', favoriteTabs=[],currentPage=1,useRemoteApi=true, indexRequestController=null,searchDebounce=null;
 const fileBaseUrl='https://tabs.retroterminal.net',primaryApiUrl=fileBaseUrl+'/api/tabs',PAGE_SIZE=20;
 const searchInput=document.getElementById('tab-search'),searchField=document.getElementById('tab-search-field'),sortSelect=document.getElementById('tab-sort'),folderSelect=document.getElementById('tab-folder');
 const favoritesSection=document.getElementById('tab-favorites'),favoritesList=document.getElementById('tab-favorites-list'),collectionStatus=document.getElementById('tab-collection-status'),listEl=document.getElementById('tab-list'),mineScopeBtn=document.getElementById('tabs-scope-mine'),allScopeBtn=document.getElementById('tabs-scope-all');
 const youtubeSync={artistButton(name){const b=document.createElement('button');b.textContent=name;return b;}};
 let opened=null,refreshes=[]; function loadTab(item){opened=item;} async function fetchRemotePage(page){refreshes.push(page);}
 ${section('  function buildApiUrl(page)', '  function syncFolderOptions')}
 ${section('  async function changeMembership(', '  function renderPage()')}
 ${section('  async function selectLibraryScope(', "  mineScopeBtn.addEventListener")}
 window.myTabsTest={createLibraryCard,changeMembership,renderFavorites,selectLibraryScope,buildApiUrl,setFavorites(items){favoriteTabs=items;},getScope(){return libraryScope;},getOpened(){return opened;},getRefreshes(){return refreshes;}};`);
 return {d,w,api:w.myTabsTest};
}
test('My Tabs is the default; All Tabs remains an explicit shared scope',async()=>{
 const {d,w,api}=harness();try{
  assert.equal(new URL(api.buildApiUrl(1)).searchParams.get('scope'),'mine');
  assert.equal(w.document.getElementById('tabs-scope-mine').getAttribute('aria-pressed'),'true');
  await api.selectLibraryScope('all');assert.equal(new URL(api.buildApiUrl(1)).searchParams.get('scope'),'all');
  assert.equal(w.document.getElementById('tab-favorites').hidden,true);
  await api.selectLibraryScope('mine');assert.equal(w.document.getElementById('tab-favorites').hidden,false);
 }finally{w.close();}
});
test('shared cards add membership; personal removal never asks to delete file',async()=>{
 const {w,api}=harness();let requests=[];w.fetch=async(url,options)=>{requests.push({url,body:JSON.parse(options.body)});return {ok:true,json:async()=>({ok:true})};};
 try{
  const item={title:'Butterfly',file:'https://tabs.retroterminal.net/files/butterfly.gp5',in_my_tabs:false,favorite:false};
  const card=api.createLibraryCard(item);const buttons=card.querySelectorAll('button');assert.equal(buttons.length,2);
  assert.equal(buttons[1].textContent,'Add to My Tabs');await buttons[1].onclick();
  assert.equal(requests[0].url,'https://tabs.retroterminal.net/api/my-tabs');assert.equal(requests[0].body.action,'add');assert.equal(requests[0].body.file,'/files/butterfly.gp5');assert.equal(requests[0].body.username,undefined);
  const personal=api.createLibraryCard({...item,in_my_tabs:true});await personal.querySelectorAll('button')[1].onclick();
  assert.equal(requests[1].body.action,'remove');assert.match(w.document.getElementById('tab-collection-status').textContent,/shared file is unchanged/);
  assert.equal(requests.some(r=>r.body.action==='delete'),false);
 }finally{w.close();}
});
test('favorites use separate scrollable section and allow un-favorite',async()=>{
 const {w,api}=harness();let body;w.fetch=async(url,options)=>{body=JSON.parse(options.body);return {ok:true,json:async()=>({ok:true})};};
 try{
  api.setFavorites([{title:'Favorite Song',file:'/files/favorite.gp5',in_my_tabs:true,favorite:true}]);api.renderFavorites();
  const list=w.document.getElementById('tab-favorites-list');assert.equal(list.querySelectorAll('li').length,1);assert.equal(w.getComputedStyle(list).overflow,'auto');
  const star=list.querySelector('button[aria-pressed]');assert.equal(star.textContent,'Unfavorite');assert.equal(star.getAttribute('aria-pressed'),'true');await star.onclick();assert.equal(body.action,'favorite');assert.equal(body.favorite,false);
 }finally{w.close();}
});
test('failed membership change is visible and button remains retryable',async()=>{
 const {w,api}=harness();w.fetch=async()=>({ok:false,json:async()=>({error:'Please sign in.'})});try{
 const card=api.createLibraryCard({title:'Song',file:'/files/song.gp5',in_my_tabs:false});const button=card.querySelectorAll('button')[1];await button.onclick();assert.equal(button.disabled,false);assert.equal(w.document.getElementById('tab-collection-status').textContent,'Please sign in.');assert.equal(api.getRefreshes().length,0);
 }finally{w.close();}
});
test('trusted network alone cannot identify a personal collection',async()=>{
 const d=new JSDOM('<body></body>',{url:'https://retroterminal.net/tabs/',runScripts:'outside-only'}),w=d.window;try{
 w.fetch=async()=>({ok:true,json:async()=>({authenticated:true,username:null})});w.eval(access);w.RetroTabAccess.start('https://tabs.retroterminal.net');await new Promise(r=>setTimeout(r,0));assert.ok(w.document.querySelector('.tabs-access-gate'));assert.equal(w.document.body.classList.contains('tabs-authenticated'),false);assert.equal(w.document.querySelector('[name=username]').value,'');
 }finally{w.close();}
});
test('personal API failure does not fall back to the shared static index',()=>{
 const load=section('  async function loadIndex()', '  async function fetchIndexJson');assert.ok(load.indexOf("libraryScope === 'mine'")<load.indexOf('falling back'));assert.match(load,/Unable to load My Tabs/);
});
