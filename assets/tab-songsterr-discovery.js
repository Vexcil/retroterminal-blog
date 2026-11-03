(function(root) {
  'use strict';
  function clean(value) {
    return String(value || '').replace(/_/g,' ').replace(/\.(?:gp[3-8]?|gpx|musicxml|xml)$/i,'')
      .replace(/\s*[([](?:ver(?:sion)?\.?\s*\d+|guitar\s*pro|tab)[)\]]\s*$/i,'').trim();
  }
  function normalize(value) {
    return clean(value).normalize('NFKD').replace(/\p{M}/gu,'').toLowerCase()
      .replace(/['’`]/g,'').replace(/[^\p{L}\p{N}]+/gu,' ').trim();
  }
  const useful = value => value && !/^(?:untitled|unknown(?: artist)?|various artists|n\/?a|guitar pro(?: \d)?|new song)$/i.test(value);
  function identity(score, item) {
    let artist=clean(score.artist), title=clean(score.title);
    if(!useful(artist)) artist='';
    if(!useful(title)) title='';
    const filename=clean(item.title || '');
    const split=(title || filename).match(/^(.+?)\s+[-–—]\s+(.+)$/);
    if(!artist && split) { artist=split[1].trim(); title=split[2].trim(); }
    else if(artist && split && normalize(artist)===normalize(split[1])) title=split[2].trim();
    if(!artist) {
      const fromFile=filename.match(/^(.+?)\s+[-–—]\s+(.+)$/);
      if(fromFile) { artist=fromFile[1].trim(); title=title || fromFile[2].trim(); }
    }
    if(!title) {
      const fromFile=filename.match(/^(.+?)\s+[-–—]\s+(.+)$/);
      title=fromFile && normalize(artist)===normalize(fromFile[1])?fromFile[2].trim():filename;
    }
    if(!useful(artist) || !useful(title) || normalize(artist).length<2 || normalize(title).length<2) return null;
    return {artist,title,query:(artist+' '+title).slice(0,120)};
  }
  function catalogIdentity(item) {
    const split=String(item.title || '').split(/\s+[-–—]\s+/);
    const artist=item.artist || (split.length>1 && !/^\d+$/.test(normalize(split[0])) ? split[0].trim() : '');
    return {artist,song_title:item.song_title || (split.length>1 ? split.slice(1).join(' — ') : item.title || '')};
  }
  function catalogMatches(item, query, field='all') {
    const wanted=normalize(query), {artist}=catalogIdentity(item);
    const designations=[artist,...String(item.folder_path || '').replace(/\\/g,'/').split('/')];
    const artistMatch=designations.some(value=>normalize(value).includes(wanted)) ||
      [...String(item.title || '').matchAll(/[-–—]/g)].some(match=>normalize(item.title.slice(0,match.index))===wanted);
    return field==='artist' ? artistMatch : normalize(item.title).includes(wanted) || artistMatch;
  }
  function matchingSongs(wanted, songs) {
    if(!wanted) return [];
    const seen=new Set();
    return songs.filter(s=>Number.isInteger(s.id) && !seen.has(s.id) &&
      normalize(s.artist)===normalize(wanted.artist) && normalize(s.title)===normalize(wanted.title) && seen.add(s.id));
  }
  function compatibleVideos(videos,count) {
    const seen=new Set();
    return (videos || []).filter(v=>{
      if(!/^[\w-]{11}$/.test(v.videoId || '') || seen.has(v.videoId) || !Array.isArray(v.points) ||
          ![count,count+1].includes(v.points.length)) return false;
      let previous=-1;
      if(!v.points.every(p=>{ if(!Number.isFinite(p)||p<0||p<=previous||p>86400) return false; previous=p;return true; })) return false;
      seen.add(v.videoId);return true;
    });
  }
  function preferredVideo(videos) {
    const full=videos.filter(v=>/^(?:full mix|original|official|studio)?$/.test(normalize(v.feature)));
    if(full.length) return full.length===1?full[0]:null;
    const alternatives=videos.filter(v=>!/(?:backing|solo|isolated)/.test(normalize(v.feature)));
    return alternatives.length===1?alternatives[0]:null;
  }
  function active(signal) {
    if(signal?.aborted) { const error=new Error('Lookup cancelled'); error.name='AbortError'; throw error; }
  }
  async function discover({wanted,count,knownId,request,signal}) {
    active(signal);
    let songs;
    if(knownId) songs=[{id:Number(knownId),artist:wanted?.artist || '',title:wanted?.title || ''}];
    else {
      if(!wanted) return {kind:'none'};
      const result=await request('/api/songsterr/search?q='+encodeURIComponent(wanted.query));
      active(signal);
      songs=matchingSongs(wanted,result.items || []);
    }
    if(!songs.length) return {kind:'none'};
    if(songs.length>3) return {kind:'choices',songs};
    const compatible=[];
    for(const song of songs) {
      active(signal);
      const source=await request('/api/songsterr/sync?id='+song.id);
      active(signal);
      if(!knownId && !matchingSongs(wanted,[source]).length) continue;
      const videos=compatibleVideos(source.videos,count);
      if(videos.length) compatible.push({source,videos});
    }
    if(!compatible.length) return {kind:'none'};
    if(compatible.length!==1) return {kind:'choices',songs:compatible.map(x=>x.source)};
    const {source,videos}=compatible[0], video=preferredVideo(videos);
    return video?{kind:'match',source,video}:{kind:'choices',songs:[source]};
  }
  const core={normalize,identity,catalogIdentity,catalogMatches,matchingSongs,compatibleVideos,preferredVideo,discover};
  if(typeof module!=='undefined' && module.exports) module.exports=core;
  root.RetroTabDiscovery=core;
})(typeof window!=='undefined'?window:globalThis);
