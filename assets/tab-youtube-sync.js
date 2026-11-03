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
  const lookupMisses=new Map();
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
    const songsterrPanel = $('tab-songsterr-panel'), songsterrToggle = $('tab-songsterr-toggle');
    const songsterrStatus = $('songsterr-status'), songsterrResults = $('songsterr-results');
    const videoPanel = $('tab-youtube-player'), playbackControl = document.querySelector('.tabs-playback-control');
    const status = $('yt-status'), url = $('yt-url'), pointsList = $('yt-points');
    const apiBase = () => context.getApiBase();
    let player, playerPromise, timer, enabled = false, saved = null, original = [], generation = 0, pendingSeek = null;
    let searchController, sourceController, nextSongsterrId, knownSongsterrId, storage, cuedVideoId, edits=0;
    let catalogController, importing = false;
    let catalogSource='songsterr', catalogArtist=null, catalogPage=1, catalogQuery='';
    let autoController,autoIdle,autoTimer,autoAttempted=false,noticeChoices=null;
    const attached = new WeakSet();
    const api = () => context.getApi(), score = () => context.getScore();
    const bars = () => score() ? timeline(api(), score()) : [];
    const storageStatus = $('yt-storage-status'), retrySave = $('yt-retry-save');
    const notice=$('tab-sync-notice'),noticeTitle=$('tab-sync-notice-title'),noticeText=$('tab-sync-notice-text');
    const message = (text, error) => { status.textContent = text; status.classList.toggle('is-error', !!error); };
    const catalogMessage = (text, error) => { songsterrStatus.textContent = text; songsterrStatus.classList.toggle('is-error', !!error); };
    function open(value) {
      if(value) openCatalog(false);
      panel.hidden = !value; toggle.setAttribute('aria-expanded', String(value));
      if(value) draw();
      // The iframe stays mounted in its own visible player when settings close.
      videoPanel.hidden = !player || (!value && !enabled);
    }
    function openCatalog(value) {
      if(value) open(false);
      else { catalogController?.abort(); catalogController=null; songsterrResults.setAttribute('aria-busy','false'); }
      songsterrPanel.hidden = !value; songsterrToggle.setAttribute('aria-expanded', String(value));
      if(value) { songsterrPanel.scrollIntoView({block:'nearest'}); $('songsterr-query').focus({preventScroll:true}); }
    }
    songsterrToggle.onclick = () => openCatalog(songsterrPanel.hidden);
    $('songsterr-close').onclick = () => { openCatalog(false); songsterrToggle.focus({preventScroll:true}); };
    songsterrPanel.addEventListener('keydown', event => {
      if(event.key==='Escape') { event.preventDefault(); event.stopPropagation(); openCatalog(false); songsterrToggle.focus({preventScroll:true}); }
    });
    function stopDiscovery(manual=false) {
      autoController?.abort();
      if(autoIdle!==undefined && root.cancelIdleCallback) root.cancelIdleCallback(autoIdle);
      clearTimeout(autoTimer); autoIdle=undefined;
      if(manual) { autoAttempted=true; notice.hidden=true; noticeChoices=null; }
    }
    function showNotice(choices=null,existing=false) {
      noticeChoices=choices;
      noticeTitle.textContent=choices?'Matching Songsterr recordings found':existing?'Saved YouTube sync ready':'YouTube sync found on Songsterr';
      noticeText.textContent=[score()?.artist,score()?.title || context.getItem()?.title].filter(Boolean).join(' — ').slice(0,120);
      $('tab-sync-notice-use').hidden=!!choices;
      $('tab-sync-notice-details').textContent=choices?'Choose':'Details';
      notice.hidden=false;
    }
    function readyTimeline() {
      const first=api()?.tickCache?.masterBars?.[0];
      return api()?.isReadyForPlayback && first && score()?.masterBars[first.masterBar.index]===first.masterBar;
    }
    function maybeDiscover() {
      if(autoAttempted || !storage?.readyForEdits || !score() || !readyTimeline() || edits) return;
      autoAttempted=true;
      if(saved) {
        if(saved.points.length>=2 && saved.barCount===bars().length) showNotice(null,true);
        return;
      }
      const stamp=generation;
      const task=async()=>{
        if(stamp!==generation || saved || !storage?.readyForEdits) return;
        autoController=new AbortController(); const controller=autoController;
        const wanted=RetroTabDiscovery.identity(score(),context.getItem()), count=bars().length;
        if(!wanted && !knownSongsterrId) return;
        const missKey=(knownSongsterrId || wanted.query)+'|'+count;
        if((lookupMisses.get(missKey)||0)>Date.now()) return;
        message('Looking for a synced recording in the background…');
        try {
          const result=await RetroTabDiscovery.discover({wanted,count,knownId:knownSongsterrId,signal:controller.signal,
            request:path=>getJson(path,controller)});
          if(controller.signal.aborted || stamp!==generation || saved || !storage?.readyForEdits) return;
          if(result.kind==='match') {
            const {source,video}=result;
            saved={version:1,videoId:video.videoId,barCount:count,points:importedPoints(video.points,bars()),
              source:{songsterrId:source.id,revision:source.revision,artist:source.artist,title:source.title}};
            url.value='https://www.youtube.com/watch?v='+video.videoId;
            $('yt-song-link').value=String(source.id);
            persist(); draw(); showNotice();
            message('Matching Songsterr video and timing found. Your current audio is unchanged. Choose Use YouTube when ready, and check the first bars.');
          } else if(result.kind==='choices') {
            showNotice(result.songs);
            message('Several recordings could fit this tab. Choose one from the notification or search below.');
          } else {
            if(lookupMisses.size>=50) lookupMisses.delete(lookupMisses.keys().next().value);
            lookupMisses.set(missKey,Date.now()+600000);
            message('No confident video/timing match found. You can search Songsterr or paste your own YouTube link.');
          }
        } catch(error) {
          if(error.name!=='AbortError' && stamp===generation && !saved)
            message('Automatic Songsterr lookup is unavailable. You can still use synth or search manually.');
        }
      };
      // Metadata requests start after score/MIDI readiness, without loading YouTube or changing playback.
      if(root.requestIdleCallback) autoIdle=root.requestIdleCallback(()=>{autoIdle=undefined;task();},{timeout:2000});
      else autoTimer=setTimeout(task,750);
    }
    $('tab-sync-notice-close').onclick=()=>{notice.hidden=true;};
    $('tab-sync-notice-use').onclick=async()=>{try { await enable(); notice.hidden=true; } catch(e) { message(e.message,true); open(true); }};
    $('tab-sync-notice-details').onclick=()=>{open(true); if(noticeChoices) renderSongs(noticeChoices); notice.hidden=true;};
    pointsList.closest('details').addEventListener('toggle',()=>{if(pointsList.closest('details').open) draw();});
    $('tab-songsterr-open').onclick = () => openCatalog(true);
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
          message(value?'Saved video and timing loaded. Choose Use YouTube.':'Find the matching Songsterr tab, or paste a YouTube URL. Changes save automatically to the server.'); draw(); maybeDiscover();
        },
        onStatus(state) {
          if(!isCurrent()) return;
          const labels={loading:'Loading saved timing…',saving:'Saving to server…',saved:'Saved on server · available on all devices',empty:'Video links and timing save automatically across your devices.',error:'Server save unavailable. Keep this tab open and retry, or export a backup.',conflict:'Another device changed this timing. Export your local copy or load the server version.'};
          storageStatus.textContent=labels[state]; storageStatus.classList.toggle('is-error',['error','conflict'].includes(state));
          retrySave.hidden=!['error','conflict'].includes(state);
          retrySave.textContent=state==='conflict'?'Load server version':'Retry server save';
          if(!notice.hidden && ['error','conflict'].includes(state)) noticeText.textContent='This timing could not be saved. Open Details to retry or review the server version.';
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
      const points = saved?.points || [], played=bars();
      $('yt-point-count').textContent = points.length + ' timing points · ' + played.length + ' played bars';
      for (const p of (!panel.hidden && pointsList.closest('details').open ? points : [])) {
        const li = document.createElement('li');
        li.textContent = 'Bar ' + (p.barIndex + 1) + (p.barOccurence ? ' (repeat ' + (p.barOccurence + 1) + ')' : '') + ': ' + (p.millisecondOffset / 1000).toFixed(2) + 's ';
        const remove = document.createElement('button'); remove.type = 'button'; remove.textContent = 'Remove';
        remove.setAttribute('aria-label', 'Remove timing for bar ' + (p.barIndex + 1));
        remove.onclick = async () => { stopDiscovery(true); const stamp=generation; try { await storage.ready(); if(stamp!==generation) return; if (enabled) useSynth(); saved.points = points.filter(x => x !== p); persist(); draw(); } catch(e) { message(e.message,true); } };
        li.append(remove); pointsList.append(li);
      }
      $('yt-enable').disabled = !readyTimeline() || !saved?.videoId || points.length < 2 || saved.barCount !== played.length;
      $('yt-enable').title = $('yt-enable').disabled ? 'Open YouTube sync settings to choose a recording and timing' : 'Use the linked YouTube recording';
      $('yt-synth').disabled = !score();
      $('yt-enable').setAttribute('aria-pressed', String(enabled));
      $('yt-synth').setAttribute('aria-pressed', String(!enabled));
      playbackControl.dataset.source = enabled ? 'youtube' : 'synth';
      $('tab-audio-source-status').textContent = 'Playback source: ' + (enabled ? 'YouTube' : 'Synth');
      videoPanel.hidden = !player || (panel.hidden && !enabled);
      $('yt-bar').max = Math.max(1, played.length);
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
        play() { videoPanel.hidden = false; player.playVideo(); if (pendingSeek !== null) { player.seekTo(pendingSeek, true); pendingSeek = null; } },
        pause() { player.pauseVideo(); }
      };
    }
    async function ensurePlayer() {
      if (playerPromise) return playerPromise;
      if (player) return player;
      playerPromise = (async () => {
        const id=saved.videoId;
        await loadYouTube();
        videoPanel.hidden = false;
        return new Promise((resolve, reject) => {
          const timeout = setTimeout(() => { playerPromise = null; reject(new Error('YouTube player did not become ready.')); }, 20000);
          player = new YT.Player('yt-embed', {width:'100%', height:'215', videoId:id,
            playerVars:{autoplay:0, playsinline:1, origin:location.origin}, events:{
              onReady() { clearTimeout(timeout); cuedVideoId=id; resolve(player); },
              onError(e) { clearTimeout(timeout); if (enabled) useSynth(); open(true); message('YouTube cannot play this video (' + e.data + '). Try a different upload; some videos block embedding.', true); reject(new Error('Video unavailable for embedding.')); },
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
      try { return await playerPromise; } catch(e) {
        playerPromise = null; player?.destroy?.(); player=null; cuedVideoId=null; videoPanel.hidden=true;
        if (!$('yt-embed')) { const mount=document.createElement('div'); mount.id='yt-embed'; videoPanel.append(mount); }
        throw e;
      }
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
      if (!readyTimeline()) throw new Error('Wait for the tab player to become ready.');
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
      draw(); message('YouTube sync ready. Use the normal Play, speed, score selection and Loop controls.');
    }
    const run = fn => async () => { try { await fn(); } catch(e) { message(e.message, true); } };
    toggle.onclick = () => { if(panel.hidden) refreshStorage(); open(panel.hidden); };
    $('yt-close').onclick = () => { open(false); };
    $('yt-open-settings').onclick = () => open(true);
    $('yt-load').onclick = run(async () => { stopDiscovery(true); await cue(); message('Video loaded. Import Songsterr timing or align the first bar below.'); });
    $('yt-enable').onclick = run(async()=>{if(enabled) return; stopDiscovery(true);await enable();});
    $('yt-synth').onclick = () => { if(!enabled) return; useSynth(); message('Synth playback restored. Your video and timing are still saved.'); };
    $('yt-tab-timing').onclick = run(async () => {
      stopDiscovery(true);
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
      stopDiscovery(true);
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
    const catalogRun = fn => async event => {
      event?.preventDefault();
      try { await fn(); } catch(error) { if(error.name!=='AbortError') catalogMessage(error.message,true); }
    };
    function updateCatalog() {
      const local=catalogSource==='library';
      songsterrPanel.querySelector('.yt-heading strong').textContent=local?'Search my library':'Search Songsterr';
      $('songsterr-source').setAttribute('aria-pressed',String(!local));
      $('library-source').setAttribute('aria-pressed',String(local));
      $('songsterr-direct-import').hidden=local;
      $('songsterr-artist-filter').hidden=!catalogArtist;
      $('songsterr-artist-name').textContent=catalogArtist?.name || '';
      songsterrResults.setAttribute('aria-label',local?'My library results':'Songsterr results');
    }
    function bindArtist(element, artist, artistId) {
      element.classList.add('tabs-artist-link');
      element.setAttribute('aria-label','Search '+artist+' tabs on Songsterr');
      element.setAttribute('title','Search '+artist+' tabs on Songsterr');
      element.onclick=catalogRun(async()=>{
        catalogArtist={name:artist,id:artistId}; catalogSource='songsterr';
        $('songsterr-query').value=artist; updateCatalog(); openCatalog(true);
        await searchCatalog(1);
      });
      if(element.tagName.toLowerCase()==='text') {
        element.setAttribute('role','button'); element.setAttribute('tabindex','0');
        element.onkeydown=event=>{if(['Enter',' '].includes(event.key)) {event.preventDefault();event.stopPropagation();element.onclick();}};
      }
      return element;
    }
    function artistButton(artist, artistId) {
      const button=document.createElement('button'); button.type='button'; button.textContent=artist;
      return bindArtist(button,artist,artistId);
    }
    async function searchCatalog(page=1, query=$('songsterr-query').value.trim()) {
      if(query.length<2) throw new Error('Enter a song title or artist.');
      if(catalogArtist && query!==catalogArtist.name) catalogArtist=null;
      catalogPage=page; catalogQuery=query; updateCatalog();
      const local=catalogSource==='library', artist=catalogArtist;
      catalogController?.abort(); const controller=catalogController=new AbortController();
      songsterrResults.replaceChildren(); songsterrResults.setAttribute('aria-busy','true');
      $('songsterr-pagination').hidden=true;
      catalogMessage(local?'Searching your library…':'Searching Songsterr…');
      try {
        const params=new URLSearchParams(local?{search:query,page,page_size:20,sort:'title-asc',search_field:artist?'artist':'all',artist_exact:artist?'1':'0'}:{q:query,page});
        if(!local && artist) { params.set('artist',artist.name); if(artist.id) params.set('artist_id',artist.id); }
        const data=await getJson((local?'/api/tabs?':'/api/songsterr/search?')+params,controller);
        if(controller.signal.aborted) return;
        if(!local && artist && data.artist_id) catalogArtist.id=data.artist_id;
        data.items.forEach(song => {
          const row=document.createElement('div'), title=document.createElement('div'), name=document.createElement('span'), button=document.createElement('button');
          const labels=local?RetroTabDiscovery.catalogIdentity(song):{artist:song.artist,song_title:song.title};
          row.className='songsterr-result'; title.className='catalog-song';
          if(labels.artist) title.append(artistButton(labels.artist,song.artist_id));
          name.textContent=labels.song_title; title.append(name);
          button.type='button'; button.textContent=local?'Open tab':'Import / open';
          button.setAttribute('aria-label',(local?'Open ':'Import or open ')+(labels.artist?labels.artist+' — ':'')+labels.song_title);
          button.onclick=catalogRun(()=>local?context.openTab(song):importSong(String(song.id),button,catalogMessage));
          row.append(title,button); songsterrResults.append(row);
        });
        $('songsterr-pagination').hidden=!data.items.length;
        $('songsterr-prev').disabled=page<=1; $('songsterr-next').disabled=!data.has_more;
        $('songsterr-page').textContent='Page '+page;
        catalogMessage(data.items.length ? (local?data.total+' tabs in your library. Choose one to open.':'Choose an arrangement to open. Tabs already in your library are reused.') : 'No tabs found'+(local?' in your library. Try Songsterr or another artist.':'. Try another search or paste a Songsterr link below.'));
      } catch(error) {
        if(catalogController===controller) throw error.name==='AbortError' ? new Error('Search timed out. Try again.') : error;
      } finally { if(catalogController===controller) songsterrResults.setAttribute('aria-busy','false'); }
    }
    $('songsterr-search-form').onsubmit = catalogRun(()=>searchCatalog(1));
    $('songsterr-query').oninput=()=>{if(catalogArtist && $('songsterr-query').value.trim()!==catalogArtist.name) {catalogArtist=null;updateCatalog();}};
    for(const source of ['songsterr','library']) $(source+'-source').onclick=catalogRun(async()=>{
      catalogSource=source; updateCatalog();
      if($('songsterr-query').value.trim().length>=2) await searchCatalog(1);
      else { songsterrResults.replaceChildren(); $('songsterr-pagination').hidden=true; }
    });
    $('songsterr-artist-clear').onclick=catalogRun(()=>{catalogArtist=null;updateCatalog();return searchCatalog(1);});
    $('songsterr-prev').onclick=catalogRun(()=>searchCatalog(Math.max(1,catalogPage-1),catalogQuery));
    $('songsterr-next').onclick=catalogRun(()=>searchCatalog(catalogPage+1,catalogQuery));
    function songsterrId(text) {
      text=text.trim();
      const match=text.match(/(?:-s|\/)(\d+)(?:[/?#]|$)/);
      const id=/^\d+$/.test(text)?text:match?.[1];
      if(!id) throw new Error('Paste a Songsterr tab URL or numeric song ID.');
      return id;
    }
    $('songsterr-link-form').onsubmit=catalogRun(()=>importSong(songsterrId($('songsterr-link').value),$('songsterr-link-import'),catalogMessage));
    $('yt-find').onclick = run(async () => {
      stopDiscovery(true);
      searchController?.abort(); searchController = new AbortController(); const stamp = generation;
      const q = $('yt-song-search').value.trim(); if (q.length < 2) throw new Error('Enter a song title or artist.');
      message('Searching Songsterr…');
      const data = await getJson('/api/songsterr/search?q=' + encodeURIComponent(q), searchController);
      if (stamp !== generation) return;
      renderSongs(data.items);
      message(data.items.length ? 'Choose the same arrangement as your tab. A matching title is not a timing guarantee.' : 'No match found. Try fewer words, paste a Songsterr link, or use a YouTube URL.');
    });
    function renderSongs(items) {
      const list=$('yt-song-results'); list.replaceChildren();
      items.forEach(song=>{
        const row=document.createElement('div'), button=document.createElement('button'); row.className='yt-song-result';
        if(song.artist) row.append(artistButton(song.artist,song.artist_id));
        button.type='button';button.textContent=song.title;button.onclick=run(()=>loadSong(song.id));row.append(button);list.append(row);
      });
    }
    async function loadSong(id) {
      stopDiscovery(true);
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
    async function importSong(id, button, report=message) {
      if(importing) return;
      stopDiscovery(true);
      importing=true; button.disabled=true; report('Opening the Songsterr arrangement in your library…');
      try {
        const response=await fetch(apiBase()+'/api/songsterr/import',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});
        const data=await response.json(); if(!response.ok) throw new Error(data.error||'Import failed.');
        nextSongsterrId=id;
        await context.importTab(data);
        report(data.alreadyExists ? 'Already in your library. Opened the existing tab without importing a duplicate.' : 'Tab imported. A synced recording will be checked in the background.');
      } finally { importing=false; button.disabled=false; }
    }
    $('yt-import-tab').onclick = run(()=>importSong(songsterrId($('yt-song-link').value),$('yt-import-tab')));
    $('yt-export').onclick=run(() => {
      if(!saved) throw new Error('No video timing to export.');
      const blob=new Blob([JSON.stringify(saved,null,2)],{type:'application/json'}), a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='youtube-sync.json'; a.click(); setTimeout(()=>URL.revokeObjectURL(a.href),1000);
    });
    $('yt-import-file').onchange=run(async () => {
      stopDiscovery(true);
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
      artistButton, bindArtist,
      beforeLoad() { stopDiscovery(); autoAttempted=false; notice.hidden=true; noticeChoices=null; knownSongsterrId=nextSongsterrId; nextSongsterrId=null; storage?.flush().catch(()=>{}); storage=null; generation++; searchController?.abort(); sourceController?.abort(); useSynth(); player?.pauseVideo?.(); pendingSeek=null; saved=null; original=[]; storageStatus.textContent=''; retrySave.hidden=true; open(false); openCatalog(false); },
      scoreLoaded(value, item) {
        original=value.exportFlatSyncPoints();
        if (!attached.has(api())) { attached.add(api()); api().playerReady.on(()=>{attachHandler(); draw(); maybeDiscover();}); }
        saved=null; url.value=''; $('yt-song-link').value='';
        $('yt-song-search').value=[value.artist,value.title || item.title].filter(Boolean).join(' ').slice(0,120);
        $('yt-song-results').replaceChildren(); $('yt-video-results').replaceChildren(); $('yt-bar').value=1; $('yt-seconds').value=0;
        message('Loading saved video and timing…'); draw(); loadStorage(item);
      }
    };
  }};
})(typeof window !== 'undefined' ? window : globalThis);
