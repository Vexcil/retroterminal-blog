(function(root) {
  'use strict';
  function videoId(value) {
    value = String(value || '').trim();
    if (/^[\w-]{11}$/.test(value)) return value;
    let u; try { u = new URL(value); } catch (_) { return null; }
    if (!['https:', 'http:'].includes(u.protocol)) return null;
    const host = u.hostname.replace(/^www\./, '');
    let id = host === 'youtu.be' ? u.pathname.split('/')[1] :
      ['youtube.com', 'm.youtube.com', 'youtube-nocookie.com'].includes(host) ?
      (u.searchParams.get('v') || (/^\/(embed|shorts|live)\//.test(u.pathname) ? u.pathname.split('/')[2] : '')) : '';
    return /^[\w-]{11}$/.test(id || '') ? id : null;
  }
  function timeline(api, score) {
    const seen = new Map();
    const bars = api.tickCache && api.tickCache.masterBars;
    return (bars && bars.length ? bars : score.masterBars.map(b => ({masterBar:b}))).map(b => {
      const i = b.masterBar.index, occurrence = seen.get(i) || 0;
      seen.set(i, occurrence + 1);
      return {barIndex:i, barPosition:0, barOccurence:occurrence, lookup:b};
    });
  }
  function importedPoints(seconds, bars) {
    if (!Array.isArray(seconds) || ![bars.length, bars.length + 1].includes(seconds.length))
      throw new Error('This Songsterr timing has ' + (seconds || []).length + ' points; your tab has ' + bars.length + ' played bars. Choose another arrangement or mark timing manually.');
    let previous = -1;
    return seconds.map((s, i) => {
      if (typeof s !== 'number' || !Number.isFinite(s) || s < 0 || s <= previous || s > 86400)
        throw new Error('The video timing is invalid or not in playback order.');
      previous = s;
      const bar = bars[Math.min(i, bars.length - 1)];
      return {barIndex:bar.barIndex, barPosition:i === bars.length ? 1 : 0,
        barOccurence:bar.barOccurence, millisecondOffset:s * 1000};
    });
  }
  const core = {videoId, timeline, importedPoints};
  if (typeof module !== 'undefined' && module.exports) module.exports = core;
  if (!root.document) return;
  let youtubeReady;
  function loadYouTube() {
    if (root.YT && root.YT.Player) return Promise.resolve();
    if (!youtubeReady) youtubeReady = new Promise((resolve, reject) => {
      const previous = root.onYouTubeIframeAPIReady;
      const timeout = setTimeout(() => { youtubeReady = null; reject(new Error('YouTube did not load. Check your connection or content blocker.')); }, 20000);
      root.onYouTubeIframeAPIReady = () => { clearTimeout(timeout); if (previous) previous(); resolve(); };
      const script = document.createElement('script'); script.src = 'https://www.youtube.com/iframe_api';
      script.onerror = () => { clearTimeout(timeout); youtubeReady = null; reject(new Error('Unable to load YouTube.')); };
      document.head.append(script);
    });
    return youtubeReady;
  }
  root.RetroTabSync = {core, create(context) {
    const $ = id => document.getElementById(id);
    const panel = $('tab-youtube-panel'), toggle = $('tab-youtube-toggle');
    const status = $('yt-status'), url = $('yt-url'), pointsList = $('yt-points');
    const apiBase = () => context.getApiBase();
    let player, playerPromise, timer, enabled = false, saved = null, original = [], generation = 0, pendingSeek = null;
    let searchController, sourceController, pendingImportId, storage, cuedVideoId, edits=0;
    const attached = new WeakSet();
    const api = () => context.getApi(), score = () => context.getScore();
    const bars = () => score() ? timeline(api(), score()) : [];
    const storageStatus = $('yt-storage-status'), retrySave = $('yt-retry-save');
    const message = (text, error) => { status.textContent = text; status.classList.toggle('is-error', !!error); };
    function open(value) { panel.hidden = !value; toggle.setAttribute('aria-expanded', String(value)); }
    $('tab-songsterr-open').onclick = () => { open(true); panel.scrollIntoView({block:'center'}); $('yt-song-link').focus(); };
    function persist() {
      if (!storage) throw new Error('Open a tab first.');
      storage.save(saved);
    }
    function loadStorage(item) {
      const file = item.file, path = RetroTabStorage.canonicalFile(file);
      const cacheKey = 'retroterminal.youtube.v2:' + path;
      let current;
      const isCurrent = () => storage === current;
      current = RetroTabStorage.createStore({file,
        readLocal() {
          const cached = localStorage.getItem(cacheKey);
          if (cached) return JSON.parse(cached);
          // Migrate the original browser copy only when no server version exists.
          for (let i=0; i<localStorage.length; i++) {
            const key=localStorage.key(i), prefix='retroterminal.youtube.v1:';
            if (key?.startsWith(prefix) && RetroTabStorage.canonicalFile(key.slice(prefix.length))===path)
              return JSON.parse(localStorage.getItem(key));
          }
          return null;
        },
        writeLocal(value) { localStorage.setItem(cacheKey,JSON.stringify(value)); },
        async request(method, body) {
          const controller=new AbortController(), timeout=setTimeout(()=>controller.abort(),15000);
          try {
            const target=apiBase()+'/api/youtube-sync'+(method==='GET'?'?file='+encodeURIComponent(file):'');
            const response=await fetch(target,{method,credentials:'include',cache:'no-store',signal:controller.signal,
              ...(method==='POST'?{headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{})});
            const data=await response.json();
            if(!response.ok) { const error=new Error(data.error||'Unable to reach saved timing.'); error.status=response.status; throw error; }
            return data;
          } finally { clearTimeout(timeout); }
        },
        onData(value) {
          if(!isCurrent()) return;
          saved=value; url.value=value?'https://www.youtube.com/watch?v='+value.videoId:'';
          $('yt-song-link').value=value?.source?.songsterrId?String(value.source.songsterrId):'';
          message(value?'Saved video and timing loaded. Choose Use YouTube.':'Find the matching Songsterr tab, or paste a YouTube URL. Changes save automatically to the server.'); draw();
        },
        onStatus(state) {
          if(!isCurrent()) return;
          const labels={loading:'Loading saved timing…',saving:'Saving to server…',saved:'Saved on server · available on all devices',empty:'Video links and timing save automatically across your devices.',error:'Server save unavailable. Keep this tab open and retry, or export a backup.',conflict:'Another device changed this timing. Export your local copy or load the server version.'};
          storageStatus.textContent=labels[state]; storageStatus.classList.toggle('is-error',['error','conflict'].includes(state));
          retrySave.hidden=!['error','conflict'].includes(state);
          retrySave.textContent=state==='conflict'?'Load server version':'Retry server save';
        }
      });
      storage=current;
      current.load().catch(()=>{});
    }
    retrySave.onclick=async()=>{ const current=storage; if(!current) return; retrySave.disabled=true; try { await current.retry(); } catch(e) { message(e.message,true); } finally { retrySave.disabled=false; } };
    const refreshStorage=()=>{ if(storage && !enabled && !edits && !storage.dirty && !storage.conflict) storage.load().catch(()=>{}); };
    root.addEventListener('focus',refreshStorage);
    function draw() {
      pointsList.replaceChildren();
      const points = saved?.points || [];
      $('yt-point-count').textContent = points.length + ' timing points · ' + bars().length + ' played bars';
      for (const p of points) {
        const li = document.createElement('li');
        li.textContent = 'Bar ' + (p.barIndex + 1) + (p.barOccurence ? ' (repeat ' + (p.barOccurence + 1) + ')' : '') + ': ' + (p.millisecondOffset / 1000).toFixed(2) + 's ';
        const remove = document.createElement('button'); remove.type = 'button'; remove.textContent = 'Remove';
        remove.setAttribute('aria-label', 'Remove timing for bar ' + (p.barIndex + 1));
        remove.onclick = async () => { const stamp=generation; try { await storage.ready(); if(stamp!==generation) return; if (enabled) useSynth(); saved.points = points.filter(x => x !== p); persist(); draw(); } catch(e) { message(e.message,true); } };
        li.append(remove); pointsList.append(li);
      }
      $('yt-enable').disabled = !score() || !saved?.videoId || points.length < 2;
      $('yt-synth').disabled = !enabled;
      $('yt-bar').max = Math.max(1, bars().length);
      document.querySelectorAll('.tabs-audio-source').forEach(e => { e.textContent = enabled ? 'Sound: YouTube · track mute/solo and transpose affect synth only' : 'Sound: Synth'; });
    }
    function useSynth() {
      clearInterval(timer); timer = null;
      if (player?.pauseVideo) player.pauseVideo();
      if (enabled && api() && score()) {
        api().pause(); enabled = false;
        score().applyFlatSyncPoints(original);
        api().settings.player.playerMode = alphaTab.PlayerMode.EnabledSynthesizer;
        api().updateSettings(); api().updateSyncPoints();
      }
      enabled = false; draw();
    }
    function attachHandler() {
      if (!enabled || !api()?.player?.output || !player) return;
      api().player.output.handler = {
        get backingTrackDuration() { return (player.getDuration() || 0) * 1000; },
        get playbackRate() { return player.getPlaybackRate() || 1; },
        set playbackRate(v) {
          const rates = player.getAvailablePlaybackRates();
          if (rates.length && !rates.includes(v)) {
            const nearest = rates.reduce((a,b) => Math.abs(b-v) < Math.abs(a-v) ? b : a);
            player.setPlaybackRate(nearest); message('YouTube supports ' + rates.join(', ') + '×; using ' + nearest + '×.');
          } else player.setPlaybackRate(v);
        },
        get masterVolume() { return player.getVolume() / 100; },
        set masterVolume(v) { player.setVolume(v * 100); },
        seekTo(ms) {
          const state = player.getPlayerState();
          if (state === 1 || state === 2) player.seekTo(ms / 1000, true);
          else pendingSeek = ms / 1000;
        },
        play() { open(true); player.playVideo(); if (pendingSeek !== null) { player.seekTo(pendingSeek, true); pendingSeek = null; } },
        pause() { player.pauseVideo(); }
      };
    }
    async function ensurePlayer() {
      if (playerPromise) return playerPromise;
      if (player) return player;
      playerPromise = (async () => {
        const id=saved.videoId;
        await loadYouTube();
        return new Promise((resolve, reject) => {
          const timeout = setTimeout(() => { playerPromise = null; reject(new Error('YouTube player did not become ready.')); }, 20000);
          player = new YT.Player('yt-embed', {width:'100%', height:'215', videoId:id,
            playerVars:{autoplay:0, playsinline:1, origin:location.origin}, events:{
              onReady() { clearTimeout(timeout); cuedVideoId=id; resolve(player); },
              onError(e) { clearTimeout(timeout); message('YouTube cannot play this video (' + e.data + '). Try a different upload; some videos block embedding.', true); if (enabled) useSynth(); reject(new Error('Video unavailable for embedding.')); },
              onStateChange(e) {
                clearInterval(timer); timer = null;
                if (!enabled || !api()) return;
                if (e.data === YT.PlayerState.PLAYING) {
                  api().play();
                  timer = setInterval(() => { if (enabled && api()?.player?.output?.updatePosition) api().player.output.updatePosition(player.getCurrentTime() * 1000); }, 50);
                } else if (e.data === YT.PlayerState.ENDED) api().stop();
                else if (e.data === YT.PlayerState.PAUSED) api().pause();
              },
              onPlaybackRateChange(e) { if (enabled && api()) api().playbackSpeed = e.data; }
            }});
        });
      })();
      try { return await playerPromise; } catch(e) { playerPromise = null; player?.destroy?.(); player=null; cuedVideoId=null; throw e; }
    }
    async function cue() {
      if (!storage) throw new Error('Open a tab first.');
      const stamp=generation, input=url.value;
      edits++;
      try {
      await storage.ready(); if(stamp!==generation) return false;
      const id = videoId(input);
      if (!id) throw new Error('Paste a valid YouTube URL or video ID.');
      if (!score()) throw new Error('Open a tab first.');
      if (!saved || saved.videoId !== id) { if (enabled) useSynth(); saved = {version:1, videoId:id, points:[], barCount:bars().length}; }
      url.value='https://www.youtube.com/watch?v='+id;
      open(true); await ensurePlayer(); if(stamp!==generation) return false;
      player.cueVideoById(id); cuedVideoId=id; pendingSeek = null; persist(); draw(); return true;
      } finally { edits--; }
    }
    async function enable() {
      if (!saved?.videoId || saved.points.length < 2) throw new Error('Add at least two timing points, or use the tab timing first.');
      if (saved.barCount !== bars().length) throw new Error('The tab arrangement changed. Import or mark its timing again.');
      const stamp = generation;
      await ensurePlayer(); if (stamp !== generation) return;
      if(cuedVideoId!==saved.videoId) { player.cueVideoById(saved.videoId); cuedVideoId=saved.videoId; }
      api().pause();
      score().applyFlatSyncPoints(saved.points);
      enabled = true;
      api().settings.player.playerMode = alphaTab.PlayerMode.EnabledExternalMedia;
      api().updateSettings(); attachHandler(); api().updateSyncPoints();
      player.setVolume(api().masterVolume * 100);
      open(true); draw(); message('YouTube sync ready. Use the normal Play, speed, score selection and Loop controls.');
    }
    const run = fn => async () => { try { await fn(); } catch(e) { message(e.message, true); } };
    toggle.onclick = () => { if (!panel.hidden && enabled) api().pause(); if(panel.hidden) refreshStorage(); open(panel.hidden); };
    $('yt-close').onclick = () => { if (enabled) api().pause(); if (player?.pauseVideo) player.pauseVideo(); open(false); };
    $('yt-load').onclick = run(async () => { await cue(); message('Video loaded. Import Songsterr timing or align the first bar below.'); });
    $('yt-enable').onclick = run(enable);
    $('yt-synth').onclick = () => { useSynth(); message('Synth playback restored. Your video and timing are still saved.'); };
    $('yt-tab-timing').onclick = run(async () => {
      if (!storage) throw new Error('Open a tab first.');
      const stamp=generation; await storage.ready(); if(stamp!==generation) return;
      if (!saved?.videoId) await cue();
      const list = bars(); if (!api().tickCache || !list.length) throw new Error('Wait for the score player to become ready.');
      const offset = Number($('yt-seconds').value);
      if (!Number.isFinite(offset) || offset < 0) throw new Error('Enter the video time where the first bar starts.');
      if (enabled) useSynth();
      let ms = offset * 1000;
      saved.points = list.map(b => {
        const point = {barIndex:b.barIndex, barPosition:0, barOccurence:b.barOccurence, millisecondOffset:ms};
        const lookup = b.lookup, changes = lookup.tempoChanges || [];
        let tick = lookup.start, tempo = changes[0]?.tempo || score().tempo || 120;
        for (const c of changes) { ms += Math.max(0, c.tick - tick) / 960 * 60000 / tempo; tick = Math.max(tick, c.tick); tempo = c.tempo; }
        ms += (lookup.end - tick) / 960 * 60000 / tempo;
        return point;
      });
      persist(); draw(); message('Tab tempo aligned to ' + offset.toFixed(2) + 's. Add or edit points if the recording drifts.');
    });
    async function addPoint(now) {
      if (!storage) throw new Error('Open a tab first.');
      const stamp=generation; await storage.ready(); if(stamp!==generation) return;
      if (!saved?.videoId) throw new Error('Load a video first.');
      const list = bars(), n = Number($('yt-bar').value) - 1;
      const seconds = now ? player?.getCurrentTime() : Number($('yt-seconds').value);
      if (!Number.isInteger(n) || !list[n] || !Number.isFinite(seconds) || seconds < 0) throw new Error('Choose a valid played bar and video time.');
      const b = list[n];
      const next = saved.points.filter(p => !(p.barIndex === b.barIndex && p.barOccurence === b.barOccurence));
      next.push({barIndex:b.barIndex, barOccurence:b.barOccurence, barPosition:0, millisecondOffset:seconds * 1000});
      const order = p => list.findIndex(b => b.barIndex === p.barIndex && b.barOccurence === p.barOccurence);
      next.sort((a,b) => order(a) - order(b));
      if (next.some((p,i) => i && p.millisecondOffset <= next[i-1].millisecondOffset)) throw new Error('Video times must increase in played-bar order.');
      if (enabled) useSynth(); saved.points = next; persist(); draw();
      $('yt-seconds').value = seconds.toFixed(2); $('yt-bar').value = Math.min(list.length, n + 2);
      message('Timing saved for played bar ' + (n + 1) + '.');
    }
    $('yt-mark').onclick = run(() => addPoint(true));
    $('yt-add').onclick = run(() => addPoint(false));
    $('yt-now').onclick = () => { if (player?.getCurrentTime) $('yt-seconds').value = player.getCurrentTime().toFixed(2); };
    async function getJson(path, controller) {
      const timeout = setTimeout(() => controller.abort(), 20000);
      try { const response = await fetch(apiBase() + path, {signal:controller.signal,credentials:'include'}); const data = await response.json(); if (!response.ok) throw new Error(data.error || 'Songsterr request failed.'); return data; }
      finally { clearTimeout(timeout); }
    }
    $('yt-find').onclick = run(async () => {
      searchController?.abort(); searchController = new AbortController(); const stamp = generation;
      const q = $('yt-song-search').value.trim(); if (q.length < 2) throw new Error('Enter a song title or artist.');
      message('Searching Songsterr…');
      const data = await getJson('/api/songsterr/search?q=' + encodeURIComponent(q), searchController);
      if (stamp !== generation) return;
      const list = $('yt-song-results'); list.replaceChildren();
      data.items.forEach(song => { const button = document.createElement('button'); button.type='button'; button.textContent=song.artist + ' — ' + song.title; button.onclick=run(() => loadSong(song.id)); list.append(button); });
      message(data.items.length ? 'Choose the same arrangement as your tab. A matching title is not a timing guarantee.' : 'No match found. Try fewer words, paste a Songsterr link, or use a YouTube URL.');
    });
    async function loadSong(id) {
      $('yt-song-link').value = String(id);
      sourceController?.abort(); sourceController = new AbortController(); const stamp = generation;
      message('Fetching video references and timing…');
      const data = await getJson('/api/songsterr/sync?id=' + encodeURIComponent(id), sourceController);
      if (stamp !== generation) return;
      const list = $('yt-video-results'); list.replaceChildren();
      data.videos.forEach(v => {
        const button=document.createElement('button'); button.type='button';
        const count = bars().length, compatible = [count,count+1].includes(v.points.length);
        button.textContent=(v.feature || 'Full mix') + ' · ' + v.points.length + ' timing points' + (compatible ? '' : ' · different arrangement');
        button.disabled=!compatible;
        button.onclick=run(async () => {
          const points=importedPoints(v.points,bars()); url.value='https://www.youtube.com/watch?v='+v.videoId;
          await cue(); if (stamp!==generation) return;
          saved.points=points; saved.source={songsterrId:data.id,revision:data.revision,artist:data.artist,title:data.title}; persist(); draw();
          message('Imported ' + points.length + ' points. Check the first bars, then choose Use YouTube. Matching bar counts still need a listening check.');
        }); list.append(button);
      });
      message(data.videos.length ? data.artist + ' — ' + data.title + '. Choose a compatible recording; different arrangements are disabled.' : 'No synced video found. Paste a YouTube URL and mark timing manually.');
    }
    $('yt-import-song').onclick = run(() => {
      const text=$('yt-song-link').value.trim(); const match=text.match(/(?:-s|\/)(\d+)(?:[/?#]|$)/);
      const id=/^\d+$/.test(text) ? text : match?.[1]; if(!id) throw new Error('Paste a Songsterr tab URL or numeric song ID.');
      return loadSong(id);
    });
    $('yt-import-tab').onclick = run(async () => {
      const text=$('yt-song-link').value.trim(), match=text.match(/(?:-s|\/)(\d+)(?:[/?#]|$)/);
      const id=/^\d+$/.test(text)?text:match?.[1];
      if(!id) throw new Error('Paste a Songsterr tab URL or numeric ID first.');
      const button=$('yt-import-tab'); button.disabled=true; message('Importing the Songsterr arrangement into your library…');
      try {
        const response=await fetch(apiBase()+'/api/songsterr/import',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});
        const data=await response.json(); if(!response.ok) throw new Error(data.error||'Import failed.');
        pendingImportId=id;
        await context.importTab(data);
        message('Tab imported. Use Get video & timing to choose its recording.');
      } finally { button.disabled=false; }
    });
    $('yt-export').onclick=run(() => {
      if(!saved) throw new Error('No video timing to export.');
      const blob=new Blob([JSON.stringify(saved,null,2)],{type:'application/json'}), a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='youtube-sync.json'; a.click(); setTimeout(()=>URL.revokeObjectURL(a.href),1000);
    });
    $('yt-import-file').onchange=run(async () => {
      if(!storage) throw new Error('Open a tab first.');
      const stamp=generation; await storage.ready(); if(stamp!==generation) return;
      const file=$('yt-import-file').files[0]; if(!file) return; if(file.size>2000000) throw new Error('Timing file is too large.');
      const value=JSON.parse(await file.text()), list=bars();
      if(stamp!==generation) return;
      if(!videoId(value.videoId)||!Array.isArray(value.points)||value.points.length>20000||value.barCount!==list.length) throw new Error('This timing file does not match the current tab.');
      let previous=-1;
      for(const p of value.points) { if(!list.some(b=>b.barIndex===p.barIndex&&b.barOccurence===p.barOccurence)||![0,1].includes(p.barPosition)||!Number.isFinite(p.millisecondOffset)||p.millisecondOffset<0||p.millisecondOffset<=previous) throw new Error('Invalid timing points.'); previous=p.millisecondOffset; }
      url.value='https://www.youtube.com/watch?v='+value.videoId; await cue(); if(stamp!==generation) return; saved=value; persist(); draw(); message('Timing imported. Choose Use YouTube to enable it.');
    });
    return {
      beforeLoad() { storage?.flush().catch(()=>{}); storage=null; generation++; searchController?.abort(); sourceController?.abort(); useSynth(); player?.pauseVideo?.(); pendingSeek=null; saved=null; original=[]; storageStatus.textContent=''; retrySave.hidden=true; open(false); },
      scoreLoaded(value, item) {
        original=value.exportFlatSyncPoints();
        if (!attached.has(api())) { attached.add(api()); api().playerReady.on(()=>{attachHandler(); draw(); if(pendingImportId) { const id=pendingImportId; pendingImportId=null; open(true); run(()=>loadSong(id))(); }}); }
        saved=null; url.value=''; $('yt-song-link').value='';
        $('yt-song-search').value=[value.artist,value.title || item.title].filter(Boolean).join(' ').slice(0,120);
        $('yt-song-results').replaceChildren(); $('yt-video-results').replaceChildren(); $('yt-bar').value=1; $('yt-seconds').value=0;
        message('Loading saved video and timing…'); draw(); loadStorage(item);
      }
    };
  }};
})(typeof window !== 'undefined' ? window : globalThis);
