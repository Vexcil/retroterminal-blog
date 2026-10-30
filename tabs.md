---
layout: default
title: Guitar Tabs
permalink: /tabs/
noindex: true
lightweight: true
tabs_player: true
---

<div class="tabs-page">
  <div class="tabs-library-heading">
    <p>Find a song, open a tab, and play.</p>
    <button id="tabs-return" type="button" hidden>Back to tab</button>
  </div>
  <section id="tabs-library" aria-label="Tab library">
  <div class="tabs-controls">
    <input type="text" id="tab-search" aria-label="Search by title" placeholder="Search by title..." />
    <select id="tab-sort" aria-label="Sort tabs">
      <option value="recent" selected>Most Recent</option>
      <option value="played">Most Played</option>
      <option value="title-asc">Title A to Z</option>
      <option value="title-desc">Title Z to A</option>
    </select>
    <select id="tab-folder" aria-label="Filter by folder">
      <option value="">All folders</option>
    </select>
    <button type="button" id="tab-upload-button">Upload</button>
    <input
      type="file"
      id="tab-upload-file"
      accept=".gp,.gp3,.gp4,.gp5,.gpx,.musicxml,.xml,.capx"
      hidden
    />
  </div>
  <p id="tab-upload-status" class="tabs-upload-status" aria-live="polite"></p>

  <div id="tab-list"></div>

  <div class="tabs-pagination">
    <button id="tab-prev">Prev</button>
    <span id="tab-page-info"></span>
    <button id="tab-next">Next</button>
  </div>

  </section>

  <section class="tabs-workspace" id="tabs-workspace" aria-label="Tab player">
    <div class="tabs-player-heading">
      <div class="tabs-song-heading">
        <h2 id="tab-song-title" tabindex="-1">Choose a tab to start</h2>
        <p id="tab-song-artist"></p>
      </div>
      <div class="tabs-view-actions">
        <button type="button" id="tabs-library-button">Library</button>
        <button type="button" id="tabs-expand-toggle" aria-pressed="false">Focus view</button>
      </div>
    </div>
    <div class="tabs-viewer-shell" id="tabs-viewer-shell">
    <aside class="at-sidebar" id="track-sidebar" aria-label="Tracks" hidden>
      <div id="track-sidebar-inner" class="at-sidebar-inner">
        <label class="tab-speed-label" for="tab-track">Show:
          <select id="tab-track" disabled><option>Open a tab first</option></select>
        </label>
        <p class="tabs-mixer-help">M = mute · S = solo</p>
        <div id="track-list"></div>
      </div>
    </aside>

    <!-- Main viewer column -->
    <div class="tabs-viewer-main">
      <div class="tab-controls-row">
        <div class="tab-player-controls">
          <button id="tab-play" disabled>Play</button>
          <button id="tab-stop" disabled>Stop</button>
          <span id="tab-player-progress" class="tab-player-progress">0%</span>
          <span id="tab-song-position" class="tab-song-position">00:00 / 00:00</span>
        </div>
        <div class="tab-player-controls">
          <label for="tab-speed" class="tab-speed-label">
            Speed:
            <select id="tab-speed">
              <option value="0.5">0.5x</option>
              <option value="0.75">0.75x</option>
              <option value="0.9">0.9x</option>
              <option value="1" selected>1x</option>
              <option value="1.25">1.25x</option>
              <option value="1.5">1.5x</option>
              <option value="2">2x</option>
            </select>
          </label>

          <label for="tab-master-volume" class="tab-speed-label">
            Master:
            <input id="tab-master-volume" type="range" min="0" max="100" value="100" />
          </label>
        </div>
      </div>

      <div class="tab-controls-row tab-controls-row-secondary">
        <div class="tab-player-controls">
          <button id="tab-count-in" class="tab-toggle" type="button">Count-in</button>
          <button id="tab-metronome" class="tab-toggle" type="button">Metronome</button>
          <button id="tab-loop" class="tab-toggle" type="button">Loop</button>

          <button id="tab-print">Print</button>
          <button id="tab-download">Download .GP</button>
          <button id="tab-download-midi">Download MIDI</button>
        </div>
        <div class="tab-player-controls">
          <label for="tab-zoom" class="tab-speed-label">
            Zoom:
            <select id="tab-zoom">
              <option value="50">50%</option>
              <option value="75">75%</option>
              <option value="90">90%</option>
              <option value="100" selected>100%</option>
              <option value="110">110%</option>
              <option value="125">125%</option>
              <option value="150">150%</option>
              <option value="200">200%</option>
            </select>
          </label>

          <label for="tab-layout" class="tab-speed-label">
            Layout:
            <select id="tab-layout">
              <option value="page" selected>Page</option>
              <option value="horizontal">Horizontal</option>
            </select>
          </label>

          <label for="tab-stave-profile" class="tab-speed-label">
            Staves:
            <select id="tab-stave-profile">
              <option value="default">Auto</option>
              <option value="scoretab">Score+Tab</option>
              <option value="score">Score</option>
              <option value="tab" selected>Tab</option>
              <option value="tabmixed">Tab Mixed</option>
            </select>
          </label>

          <label for="tab-transpose" class="tab-speed-label">
            Transpose:
            <select id="tab-transpose">
              <option value="-12">-12</option>
              <option value="-7">-7</option>
              <option value="-5">-5</option>
              <option value="-2">-2</option>
              <option value="0" selected>0</option>
              <option value="2">+2</option>
              <option value="5">+5</option>
              <option value="7">+7</option>
              <option value="12">+12</option>
            </select>
          </label>
        </div>
      </div>

      <div class="at-wrap">
        <div class="at-viewport" tabindex="0" role="region" aria-label="Tab notation">
          <div class="at-main" id="alphaTab"></div>
        </div>
      </div>
    </div>

    </div>
    <aside id="tab-playback-panel" class="tabs-floating-panel" aria-label="Playback and display options" hidden>
      <p class="tabs-panel-heading">Playback &amp; display</p>
      <p class="tabs-audio-source">Sound: Synth</p>
      <div id="tab-floating-options"></div>
    </aside>
    <div id="tabs-floating-dock" class="tabs-floating-dock" role="group" aria-label="Quick player controls" hidden>
      <div class="tabs-dock-primary">
      <button id="track-sidebar-toggle" type="button" aria-label="Tracks" aria-expanded="false" aria-controls="track-sidebar" aria-keyshortcuts="T" title="Tracks" disabled>Tracks</button>
      <button id="tab-playback-toggle" type="button" aria-expanded="false" aria-controls="tab-playback-panel" aria-keyshortcuts="P">Playback</button>
      <button id="tab-dock-loop" type="button" data-mirror="tab-loop" aria-pressed="false" aria-keyshortcuts="L">Loop</button>
      <button id="tab-dock-play" type="button" data-mirror="tab-play" aria-keyshortcuts="Space" disabled>Play</button>
      </div>
      <div id="tab-dock-extra" class="tabs-dock-extra" inert></div>
      <button id="tab-dock-expand" class="tabs-dock-expand" type="button" aria-expanded="false" aria-controls="tab-dock-extra" aria-label="Show more player settings" title="Show more player settings">⌃</button>
    </div>
  </section>
</div>

<script src="https://cdn.jsdelivr.net/npm/@coderline/alphatab@1.6.0/dist/alphaTab.min.js"></script>
<script>
(function() {
  const PAGE_SIZE = 50;
  const primaryApiUrl = {{ site.tabs_api_url | default: "https://tabs.retroterminal.net/api/tabs" | jsonify }};
  const playApiUrl = {{ site.tabs_play_api_url | default: "https://tabs.retroterminal.net/api/play" | jsonify }};
  const primaryIndexUrl = {{ site.tabs_index_url | default: "https://tabs.retroterminal.net/data/tabs.json" | jsonify }};
  const fileBaseUrl = {{ site.tabs_file_base_url | default: "" | jsonify }};
  const uploadUrl = {{ site.tabs_upload_url | default: "https://tabs.retroterminal.net/upload" | jsonify }};

  let allTabs = [];
  let filteredTabs = [];
  let currentPage = 1;
  let totalTabs = 0;
  let useRemoteApi = false;
  let searchDebounce = null;
  let indexRequestController = null;

  const searchInput        = document.getElementById('tab-search');
  const sortSelect         = document.getElementById('tab-sort');
  const folderSelect       = document.getElementById('tab-folder');
  const listEl             = document.getElementById('tab-list');
  const pageInfoEl         = document.getElementById('tab-page-info');
  const prevBtn            = document.getElementById('tab-prev');
  const nextBtn            = document.getElementById('tab-next');
  const uploadInput        = document.getElementById('tab-upload-file');
  const uploadBtn          = document.getElementById('tab-upload-button');
  const uploadStatusEl     = document.getElementById('tab-upload-status');
  const songTitleEl        = document.getElementById('tab-song-title');
  const songArtistEl       = document.getElementById('tab-song-artist');
  const viewerContainer    = document.getElementById('alphaTab');
  const scoreViewport      = document.querySelector('.at-viewport');
  const viewerExpandBtn    = document.getElementById('tabs-expand-toggle');

  const playBtn            = document.getElementById('tab-play');
  const stopBtn            = document.getElementById('tab-stop');
  const speedSelect        = document.getElementById('tab-speed');
  const masterVolumeInput  = document.getElementById('tab-master-volume');
  const printBtn           = document.getElementById('tab-print');
  const downloadBtn        = document.getElementById('tab-download');
  const downloadMidiBtn    = document.getElementById('tab-download-midi');
  const countInBtn         = document.getElementById('tab-count-in');
  const metronomeBtn       = document.getElementById('tab-metronome');
  const loopBtn            = document.getElementById('tab-loop');
  const zoomSelect         = document.getElementById('tab-zoom');
  const layoutSelect       = document.getElementById('tab-layout');
  const staveProfileSelect = document.getElementById('tab-stave-profile');
  const transposeSelect    = document.getElementById('tab-transpose');
  const playerProgressEl   = document.getElementById('tab-player-progress');
  const songPositionEl     = document.getElementById('tab-song-position');

  const trackSidebar       = document.getElementById('track-sidebar');
  const trackSidebarToggle = document.getElementById('track-sidebar-toggle');
  const trackListEl        = document.getElementById('track-list');
  const trackSelect        = document.getElementById('tab-track');
  const floatingDock       = document.getElementById('tabs-floating-dock');
  const playbackPanel      = document.getElementById('tab-playback-panel');
  const playbackToggle     = document.getElementById('tab-playback-toggle');
  const floatingOptions    = document.getElementById('tab-floating-options');
  const dockExtra          = document.getElementById('tab-dock-extra');
  const dockExpand         = document.getElementById('tab-dock-expand');
  const workspace          = document.getElementById('tabs-workspace');
  const libraryBtn         = document.getElementById('tabs-library-button');
  const returnBtn          = document.getElementById('tabs-return');
  const library            = document.getElementById('tabs-library');
  let focusPreferred = true;
  try { focusPreferred = localStorage.getItem('retroterminal.tabs.focus') !== 'false'; } catch (_) {}

  let alphaApi       = null;
  let currentScore   = null;
  let currentTabItem = null;
  let currentTabPlayReported = false;
  let tabLoadController = null;
  let isPlaying = false;
  let clearanceFrame = null;

  const uiState = {
    countIn: false,
    metronome: false,
    loop: false,
    playbackSpeed: 1,
    masterVolume: 1,
    zoom: 1,
    layout: "page",
    staveProfile: "tab",
    transpose: 0
  };

  function updateScoreScrollRoom() {
    // Leave enough room after the final system for it to reach the top too.
    // Keep this outside alphaTab's render surface so score coordinates stay intact.
    let space = 0;
    if (currentScore && uiState.layout === 'page') {
      const lastBar = alphaApi.boundsLookup?.findMasterBarByIndex(currentScore.masterBars.length - 1);
      space = Math.max(0, lastBar
        ? scoreViewport.clientHeight + lastBar.visualBounds.y - 12 - viewerContainer.offsetHeight
        : scoreViewport.clientHeight - 24);
    }
    scoreViewport.style.setProperty('--tabs-score-tail-space', space + 'px');
  }

  function keepPlayingMeasureClear() {
    if (!isPlaying || !currentScore || uiState.layout !== 'page' || workspace.classList.contains('score-pending')) return;
    const cursor = viewerContainer.querySelector('.at-cursor-bar');
    if (!cursor) return;
    const bar = cursor.getBoundingClientRect();
    const viewport = scoreViewport.getBoundingClientRect();
    if (!bar.width || !bar.height || bar.bottom <= viewport.top || bar.top >= viewport.bottom) return;
    const covered = [floatingDock, trackSidebar, playbackPanel].some(panel => {
      if (panel.hidden) return false;
      const rect = panel.getBoundingClientRect();
      return rect.width && rect.height && bar.right > rect.left - 12 && bar.left < rect.right + 12 &&
        bar.bottom > rect.top - 12 && bar.top < rect.bottom + 12;
    });
    if (!covered) return;
    const top = Math.min(scoreViewport.scrollHeight - scoreViewport.clientHeight,
      Math.max(0, scoreViewport.scrollTop + bar.top - viewport.top - scoreViewport.clientTop - 12));
    if (Math.abs(top - scoreViewport.scrollTop) < 2) return;
    scoreViewport.scrollTo({ top, behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' });
  }

  function scheduleMeasureClearance() {
    if (clearanceFrame !== null) return;
    // alphaTab positions its playback cursor and performs its normal scrolling first.
    clearanceFrame = requestAnimationFrame(() => {
      clearanceFrame = null;
      keepPlayingMeasureClear();
    });
  }

  function setToggle(btn, on) {
    if (!btn) return;
    btn.classList.toggle("on", on);
    btn.setAttribute("aria-pressed", String(on));
  }

  function setUploadStatus(message, kind) {
    if (!uploadStatusEl) return;
    uploadStatusEl.textContent = message || "";
    uploadStatusEl.classList.remove("success", "error", "working");
    if (kind) {
      uploadStatusEl.classList.add(kind);
    }
  }

  function isAbsoluteUrl(value) {
    return /^https?:\/\//i.test(value || "");
  }

  function resolveTabFileUrl(filePath) {
    if (!filePath) return "";
    if (isAbsoluteUrl(filePath)) return filePath;

    const base = fileBaseUrl || window.location.origin;

    try {
      return new URL(filePath, base).toString();
    } catch (err) {
      console.warn("Unable to resolve tab file URL:", filePath, err);
      return filePath;
    }
  }

  function normalizeTabItem(item) {
    return {
      title: item && item.title ? item.title : "Untitled tab",
      file: resolveTabFileUrl(item && item.file ? item.file : ""),
      folder: item && item.folder ? item.folder : "Root",
      folder_path: item && item.folder_path ? item.folder_path : "",
      modified_at: item && item.modified_at ? item.modified_at : 0,
      play_count: item && item.play_count ? item.play_count : 0
    };
  }

  function upsertTabItem(item) {
    if (!item || !item.file) return;

    const existingIndex = allTabs.findIndex(function(entry) {
      return entry.file === item.file;
    });

    if (existingIndex >= 0) {
      allTabs[existingIndex] = item;
    } else {
      allTabs.push(item);
    }
  }

  function buildApiUrl(page) {
    const url = new URL(primaryApiUrl, window.location.origin);
    url.searchParams.set("page", String(page));
    url.searchParams.set("page_size", String(PAGE_SIZE));
    url.searchParams.set("sort", sortSelect.value || "title-asc");
    url.searchParams.set("search", searchInput.value || "");
    url.searchParams.set("folder", folderSelect.value || "");
    return url.toString();
  }

  function syncFolderOptions(folders) {
    if (!folderSelect || !Array.isArray(folders) || folders.length === 0) return;

    const selected = folderSelect.value || "";
    const options = ['<option value="">All folders</option>'].concat(
      folders.map(function(folder) {
        const escaped = String(folder)
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;")
          .replace(/"/g, "&quot;");
        return '<option value="' + escaped + '">' + escaped + '</option>';
      })
    );

    folderSelect.innerHTML = options.join("");
    folderSelect.value = folders.includes(selected) ? selected : "";
  }

  function formatTime(milliseconds) {
    if (!isFinite(milliseconds) || milliseconds < 0) return "00:00";
    const s = Math.floor(milliseconds / 1000);
    const m = Math.floor(s / 60);
    const r = s % 60;
    return String(m).padStart(2, "0") + ":" + String(r).padStart(2, "0");
  }

  function updateSongInfo(score) {
    songTitleEl.textContent = (score && score.title) || (currentTabItem && currentTabItem.title) || "Untitled tab";
    songArtistEl.textContent = (score && score.artist) || "";
    songTitleEl.title = currentTabItem ? currentTabItem.title : "";
  }

  function setViewerFocused(focused, remember) {
    workspace.classList.toggle("focused", focused);
    document.body.classList.toggle("tabs-focus", focused);
    document.querySelectorAll('.site-header, footer, .post-title, .tabs-library-heading, #tabs-library').forEach(element => { element.inert = focused; });
    viewerExpandBtn.textContent = focused ? "Page view" : "Focus view";
    viewerExpandBtn.setAttribute("aria-pressed", String(focused));
    setTracksOpen(false);
    setPlaybackOpen(false);
    setDockExpanded(false);
    if (remember) {
      focusPreferred = focused;
      try { localStorage.setItem('retroterminal.tabs.focus', String(focused)); } catch (_) {}
    }
  }

  function showLibrary() {
    setViewerFocused(false);
    library.scrollIntoView({ block: "start" });
    searchInput.focus({ preventScroll: true });
  }

  function selectTrack(value) {
    if (!alphaApi || !currentScore) return;
    const tracks = value === "all" ? currentScore.tracks : currentScore.tracks.filter(t => String(t.index) === value);
    if (!tracks.length) return;
    alphaApi.renderTracks(tracks);
    trackSelect.value = value;
    trackListEl.querySelectorAll('.at-track-select').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.trackIndex === value));
    });
  }

  async function loadIndex() {
    listEl.textContent = "Loading tab index...";
    if (primaryApiUrl) {
      try {
        useRemoteApi = true;
        await fetchRemotePage(1);
        return;
      } catch (err) {
        useRemoteApi = false;
        console.warn("Remote tabs API unavailable, falling back to static index.", err);
      }
    }

    const sources = [];
    if (primaryIndexUrl) sources.push(primaryIndexUrl);

    let lastError = null;

    for (const sourceUrl of sources) {
      try {
        const data = await fetchIndexJson(sourceUrl, 30000);
        allTabs = data.map(normalizeTabItem);
        totalTabs = allTabs.length;
        syncFolderOptions(
          Array.from(new Set(allTabs.map(function(item) { return item.folder; }))).sort()
        );
        filteredTabs = allTabs.slice();
        applyFiltersAndRender();
        return;
      } catch (err) {
        lastError = err;
        console.warn("Error loading tabs index from", sourceUrl, err);
      }
    }

    console.error("Failed to load any tabs index.", lastError);
    listEl.textContent = "Failed to load tab index.";
  }

  async function fetchIndexJson(url, timeoutMs) {
    const controller = new AbortController();
    const timeout = setTimeout(function() { controller.abort(); }, timeoutMs);
    try {
      const response = await fetch(url, {
        cache: "no-store",
        mode: isAbsoluteUrl(url) ? "cors" : "same-origin",
        signal: controller.signal
      });
      if (!response.ok) throw new Error("HTTP " + response.status);
      return await response.json();
    } finally {
      clearTimeout(timeout);
    }
  }

  async function fetchRemotePage(page) {
    if (indexRequestController) indexRequestController.abort();
    const controller = new AbortController();
    indexRequestController = controller;
    const timeout = setTimeout(() => controller.abort(), 12000);
    listEl.setAttribute('aria-busy', 'true');
    try {
      const response = await fetch(buildApiUrl(page), { cache: "no-store", mode: "cors", signal: controller.signal });
      if (!response.ok) throw new Error("HTTP " + response.status);
      const payload = await response.json();
      if (controller !== indexRequestController) return;
      filteredTabs = (payload.items || []).map(normalizeTabItem);
      totalTabs = typeof payload.total === "number" ? payload.total : filteredTabs.length;
      currentPage = typeof payload.page === "number" ? payload.page : page;
      syncFolderOptions(payload.folders || []);
      renderPage();
    } catch (error) {
      if (controller !== indexRequestController) return;
      throw error;
    } finally {
      clearTimeout(timeout);
      if (controller === indexRequestController) listEl.removeAttribute('aria-busy');
    }
  }

  async function uploadTab() {
    if (!uploadInput || !uploadInput.files || uploadInput.files.length === 0) {
      setUploadStatus("", "");
      return;
    }

    const file = uploadInput.files[0];
    const formData = new FormData();
    formData.append("file", file, file.name);

    if (uploadBtn) uploadBtn.disabled = true;
    setUploadStatus("Uploading...", "working");

    try {
      const response = await fetch(uploadUrl, {
        method: "POST",
        body: formData
      });
      const payload = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(payload.error || ("Upload failed with HTTP " + response.status));
      }

      setUploadStatus(payload.message || "Upload complete.", "success");
      uploadInput.value = "";

      if (payload.file) {
        const uploadedItem = normalizeTabItem({
          title: payload.title || file.name,
          file: payload.file
        });
        if (useRemoteApi) {
          await fetchRemotePage(currentPage);
        } else {
          upsertTabItem(uploadedItem);
          totalTabs = allTabs.length;
          applyFiltersAndRender();
        }
        loadTab(uploadedItem);
      }
    } catch (err) {
      setUploadStatus(err.message || "Upload failed.", "error");
    } finally {
      if (uploadBtn) uploadBtn.disabled = false;
    }
  }

  function applyFiltersAndRender() {
    if (useRemoteApi) {
      fetchRemotePage(1).catch(function(err) {
        console.error("Failed to fetch remote tabs page:", err);
        listEl.textContent = "Failed to load tabs.";
      });
      return;
    }

    const q = (searchInput.value || "").toLowerCase();
    const folder = folderSelect ? (folderSelect.value || "") : "";

    filteredTabs = allTabs.filter(item =>
      item.title.toLowerCase().includes(q) &&
      (!folder || item.folder === folder)
    );

    const sortVal = sortSelect.value;
    filteredTabs.sort((a, b) => {
      if (sortVal === "recent") {
        const delta = (b.modified_at || 0) - (a.modified_at || 0);
        if (delta !== 0) return delta;
      }
      if (sortVal === "played") {
        const delta = (b.play_count || 0) - (a.play_count || 0);
        if (delta !== 0) return delta;
      }
      const ta = a.title.toLowerCase();
      const tb = b.title.toLowerCase();
      if (sortVal !== "title-desc") {
        if (ta < tb) return -1;
        if (ta > tb) return 1;
        return 0;
      }
      if (ta < tb) return sortVal === "title-asc" ? -1 : 1;
      if (ta > tb) return sortVal === "title-asc" ?  1 : -1;
      return 0;
    });

    const maxPage = Math.max(1, Math.ceil(filteredTabs.length / PAGE_SIZE));
    if (currentPage > maxPage) currentPage = maxPage;
    totalTabs = filteredTabs.length;

    renderPage();
  }

  function renderPage() {
    listEl.innerHTML = "";

    if (filteredTabs.length === 0) {
      listEl.textContent = "No tabs found.";
      pageInfoEl.textContent = "";
      prevBtn.disabled = true;
      nextBtn.disabled = true;
      return;
    }

    const maxPage = Math.max(1, Math.ceil(totalTabs / PAGE_SIZE));
    const start   = useRemoteApi ? 0 : (currentPage - 1) * PAGE_SIZE;
    const end     = useRemoteApi ? filteredTabs.length : Math.min(start + PAGE_SIZE, filteredTabs.length);
    const slice   = useRemoteApi ? filteredTabs : filteredTabs.slice(start, end);

    const ul = document.createElement("ul");
    ul.className = "tab-list-ul";

    slice.forEach(item => {
      const li = document.createElement("li");
      li.className = "tab-list-item";

      const titleSpan = document.createElement("span");
      titleSpan.className = "tab-title";
      titleSpan.textContent = item.title;
      titleSpan.title = item.folder_path || item.folder || item.title;

      const btn = document.createElement("button");
      btn.textContent = "View";
      btn.setAttribute("aria-label", "Open " + item.title);
      btn.addEventListener("click", function() {
        loadTab(item);
      });

      li.appendChild(titleSpan);
      li.appendChild(btn);
      ul.appendChild(li);
    });

    listEl.appendChild(ul);
    listEl.scrollTop = 0;

    pageInfoEl.textContent = "Page " + currentPage + " of " + maxPage;
    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= maxPage;
  }

  function clearTracks() {
    trackListEl.replaceChildren();
    trackSelect.replaceChildren(new Option('Loading tracks...', ''));
    trackSelect.disabled = true;
    trackSidebarToggle.disabled = true;
    setTracksOpen(false);
  }

  function populateTracks(score) {
    clearTracks();
    if (!score || !score.tracks || !score.tracks.length) return;
    trackSelect.replaceChildren();
    score.tracks.forEach(track => {
      const name = track.name || ("Track " + (track.index + 1));
      trackSelect.add(new Option(name, String(track.index)));
      const row = document.createElement('div');
      row.className = 'at-track-row';
      const header = document.createElement('div');
      header.className = 'at-track-header';
      const select = document.createElement('button');
      select.type = 'button';
      select.className = 'at-track-select';
      select.textContent = name;
      select.title = name;
      select.dataset.trackIndex = String(track.index);
      select.setAttribute('aria-label', 'Show ' + name);
      select.setAttribute('aria-pressed', 'false');
      select.addEventListener('click', () => {
        selectTrack(String(track.index));
        setTracksOpen(false);
        trackSidebarToggle.focus();
      });
      const buttons = document.createElement('div');
      buttons.className = 'at-track-buttons';
      const mute = document.createElement('button');
      mute.type = 'button';
      mute.textContent = 'M';
      mute.setAttribute('aria-label', 'Mute ' + name);
      setToggle(mute, false);
      mute.addEventListener('click', () => {
        const on = mute.getAttribute('aria-pressed') !== 'true';
        setToggle(mute, on);
        alphaApi.changeTrackMute([track], on);
      });
      const solo = document.createElement('button');
      solo.type = 'button';
      solo.textContent = 'S';
      solo.className = 'track-solo';
      solo.setAttribute('aria-label', 'Solo ' + name);
      setToggle(solo, false);
      solo.addEventListener('click', () => {
        const on = solo.getAttribute('aria-pressed') !== 'true';
        trackListEl.querySelectorAll('.track-solo').forEach(button => setToggle(button, false));
        alphaApi.changeTrackSolo(currentScore.tracks, false);
        setToggle(solo, on);
        if (on) alphaApi.changeTrackSolo([track], true);
      });
      buttons.append(mute, solo);
      header.append(select, buttons);
      const volume = document.createElement('input');
      volume.type = 'range';
      volume.min = '0';
      volume.max = '100';
      volume.value = '100';
      volume.setAttribute('aria-label', name + ' volume');
      volume.addEventListener('input', () => alphaApi.changeTrackVolume([track], Number(volume.value) / 100));
      const volumeWrap = document.createElement('div');
      volumeWrap.className = 'at-track-volume';
      volumeWrap.append(volume);
      row.append(header, volumeWrap);
      trackListEl.append(row);
    });
    trackSelect.add(new Option('All tracks', 'all'));
    trackSelect.disabled = false;
    trackSidebarToggle.disabled = false;
    floatingDock.hidden = false;
    selectTrack(String(score.tracks[0].index));
  }

  function applyDisplaySettings() {
    if (!alphaApi) return;

    const layoutMap = {
      page: alphaTab.LayoutMode.Page,
      horizontal: alphaTab.LayoutMode.Horizontal
    };

    const staveMap = {
      default: alphaTab.StaveProfile.Default,
      scoretab: alphaTab.StaveProfile.ScoreTab,
      score: alphaTab.StaveProfile.Score,
      tab: alphaTab.StaveProfile.Tab,
      tabmixed: alphaTab.StaveProfile.TabMixed
    };

    try {
      alphaApi.settings.display.scale = uiState.zoom;
      alphaApi.settings.display.layoutMode = layoutMap[uiState.layout] ?? alphaTab.LayoutMode.Page;
      alphaApi.settings.display.staveProfile = staveMap[uiState.staveProfile] ?? alphaTab.StaveProfile.Default;
      alphaApi.updateSettings();
      alphaApi.render();
    } catch (err) {
      console.warn("Display settings update unsupported:", err);
    }
  }

  function applyPlaybackSettings() {
    if (!alphaApi) return;

    try {
      alphaApi.playbackSpeed = uiState.playbackSpeed;
    } catch (err) {
      console.warn("Playback speed set unsupported:", err);
    }

    try {
      alphaApi.masterVolume = uiState.masterVolume;
    } catch (err) {
      console.warn("Master volume set unsupported:", err);
    }

    try {
      alphaApi.isLooping = uiState.loop;
    } catch (err) {
      console.warn("Looping unsupported:", err);
    }

    try {
      alphaApi.countInVolume = uiState.countIn ? 1 : 0;
    } catch (err) {
      console.warn("Count-in unsupported:", err);
    }

    try {
      alphaApi.metronomeVolume = uiState.metronome ? 1 : 0;
    } catch (err) {
      console.warn("Metronome unsupported:", err);
    }
  }

  function applyTranspose() {
    if (!alphaApi || !currentScore) return;
    try {
      if (typeof alphaApi.changeTrackTranspositionPitch === "function") {
        alphaApi.changeTrackTranspositionPitch(currentScore.tracks, uiState.transpose);
      }
    } catch (err) {
      console.warn("Transpose unsupported:", err);
    }
  }

  function wirePlayerEvents() {
    if (!alphaApi) return;

    if (playerProgressEl) {
      playerProgressEl.textContent = "Loading 0%";
    }

    if (songPositionEl) {
      songPositionEl.textContent = "00:00 / 00:00";
    }

    if (alphaApi.soundFontLoad && alphaApi.soundFontLoad.on) {
      alphaApi.soundFontLoad.on(function(e) {
        if (playerProgressEl && e && typeof e.percentage === "number") {
          playerProgressEl.textContent = "Loading " + e.percentage + "%";
        }
      });
    }

    if (alphaApi.soundFontLoaded && alphaApi.soundFontLoaded.on) {
      alphaApi.soundFontLoaded.on(function() {
        if (playerProgressEl && playerProgressEl.textContent.indexOf("Loading") === 0) {
          playerProgressEl.textContent = "SoundFont loaded";
        }
      });
    }

    alphaApi.playerReady.on(function() {
      if (playBtn) playBtn.disabled = !currentScore;
      if (stopBtn) stopBtn.disabled = !currentScore;
      if (playerProgressEl) playerProgressEl.textContent = "Ready";
    });

    alphaApi.playerStateChanged.on(function(e) {
      if (!playBtn || !e) return;
      isPlaying = e.state === alphaTab.synth.PlayerState.Playing;
      playBtn.textContent = isPlaying ? "Pause" : "Play";
      if (isPlaying && currentTabItem) reportPlay(currentTabItem);
    });

    alphaApi.playedBeatChanged.on(scheduleMeasureClearance);

    alphaApi.playerPositionChanged.on(function(e) {
      if (!songPositionEl || !e || !currentScore) return;
      const now = formatTime(e.currentTime);
      const end = formatTime(e.endTime);
      const position = now + " / " + end;
      if (songPositionEl.textContent !== position) {
        songPositionEl.textContent = position;
      }
    });
  }

  function createAlphaTab() {
    if (alphaApi) return alphaApi;
    const viewportEl = document.querySelector(".at-viewport");

    const settings = {
      core: {
        useWorkers: true,
        enableLazyLoading: true
      },
      display: {
        scale: uiState.zoom,
        staveProfile: uiState.staveProfile,
        layoutMode: uiState.layout,
        padding: [16, 12],
        systemPaddingTop: 4,
        systemPaddingBottom: 8
      },
      player: {
        enablePlayer: true,
        soundFont: "https://cdn.jsdelivr.net/npm/@coderline/alphatab@1.6.0/dist/soundfont/sonivox.sf2",
        bufferTimeInMilliseconds: 1000,
        scrollElement: viewportEl,
        scrollMode: "offscreen",
        nativeBrowserSmoothScroll: true
      }
    };

    alphaApi = new alphaTab.AlphaTabApi(viewerContainer, settings);
    applyPlaybackSettings();
    wirePlayerEvents();

    alphaApi.scoreLoaded.on(function(score) {
      // Some Guitar Pro exports attach empty lyric lines to every beat.
      // They reserve full lyric staves despite containing no visible content.
      for (const track of score.tracks) {
        for (const staff of track.staves) {
          for (const bar of staff.bars) {
            for (const voice of bar.voices) {
              for (const beat of voice.beats) {
                if (Array.isArray(beat.lyrics) && beat.lyrics.every(line => !String(line || '').trim())) beat.lyrics = null;
              }
            }
          }
        }
      }
      currentScore = score;
      if (alphaApi.isReadyForPlayback) {
        playBtn.disabled = false;
        stopBtn.disabled = false;
        playerProgressEl.textContent = 'Ready';
      }
      populateTracks(score);
      updateSongInfo(score);
      applyTranspose();

      // Reset speed on new score
      if (speedSelect && speedSelect.value) {
        const s = parseFloat(speedSelect.value);
        if (!isNaN(s)) {
          try {
            alphaApi.playbackSpeed = s;
          } catch (err) {
            console.warn("Playback speed set unsupported:", err);
          }
        }
      }
    });

    alphaApi.renderFinished.on(function() {
      if (!currentScore) return;
      workspace.classList.remove('score-pending');
      viewerContainer.removeAttribute('aria-busy');
      updateScoreScrollRoom();
      scheduleMeasureClearance();
    });

    alphaApi.error.on(function(error) {
      console.error("Tab player error:", error);
      currentScore = null;
      playBtn.disabled = true;
      stopBtn.disabled = true;
      workspace.classList.add('score-pending');
      trackSidebarToggle.disabled = true;
      setTracksOpen(false);
      viewerContainer.removeAttribute('aria-busy');
      if (playerProgressEl) playerProgressEl.textContent = "Unable to load tab.";
    });
    return alphaApi;
  }

  async function loadTab(item) {
    if (tabLoadController) tabLoadController.abort();
    const controller = new AbortController();
    tabLoadController = controller;
    const api = createAlphaTab();
    workspace.classList.add('score-pending');
    viewerContainer.setAttribute('aria-busy', 'true');
    api.stop();
    if (api.player) api.player.resetChannelStates();
    currentScore = null;
    clearTracks();
    const viewport = document.querySelector(".at-viewport");
    if (viewport) {
      viewport.scrollTop = 0;
      viewport.scrollLeft = 0;
    }
    if (playBtn) {
      playBtn.disabled = true;
      playBtn.textContent = "Play";
    }
    if (stopBtn) stopBtn.disabled = true;
    if (playerProgressEl) playerProgressEl.textContent = "Loading tab...";
    if (songPositionEl) songPositionEl.textContent = "00:00 / 00:00";
    currentTabItem = item;
    currentTabPlayReported = false;
    returnBtn.hidden = false;
    setViewerFocused(focusPreferred);
    if (!focusPreferred) workspace.scrollIntoView({ block: 'start' });
    songTitleEl.focus({ preventScroll: true });
    if (songTitleEl) songTitleEl.textContent = item.title || "Loading...";
    if (songArtistEl) songArtistEl.textContent = "";
    try {
      const response = await fetch(item.file, { signal: controller.signal });
      if (!response.ok) throw new Error("HTTP " + response.status);
      const data = await response.arrayBuffer();
      if (controller.signal.aborted) return;
      if (!api.load(data)) throw new Error("Unsupported tab file.");
    } catch (error) {
      if (controller.signal.aborted) return;
      console.error("Unable to load tab:", error);
      viewerContainer.removeAttribute('aria-busy');
      if (playerProgressEl) playerProgressEl.textContent = "Unable to load tab. Try another tab from the library.";
    }
  }

  function reportPlay(item) {
    if (!item || !item.file || currentTabPlayReported) return;
    currentTabPlayReported = true;

    fetch(playApiUrl, {
      method: "POST",
      mode: "cors",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ file: item.file })
    }).then(function(response) {
      if (!response.ok) throw new Error('HTTP ' + response.status);
    }).catch(function(err) {
      console.warn("Failed to report play:", err);
      currentTabPlayReported = false;
    });
  }

  function setTracksOpen(open) {
    if (open && !currentScore) return;
    trackSidebar.hidden = !open;
    trackSidebarToggle.setAttribute('aria-expanded', String(open));
    if (open) {
      setPlaybackOpen(false);
      setDockExpanded(false);
    }
  }
  function setDockExpanded(expanded) {
    floatingDock.classList.toggle('expanded', expanded);
    dockExtra.inert = !expanded;
    dockExpand.setAttribute('aria-expanded', String(expanded));
    dockExpand.setAttribute('aria-label', expanded ? 'Hide extra player settings' : 'Show more player settings');
    dockExpand.title = expanded ? 'Hide extra player settings' : 'Show more player settings';
    dockExpand.textContent = expanded ? '⌄' : '⌃';
  }
  dockExpand.addEventListener('click', () => {
    const expanded = !floatingDock.classList.contains('expanded');
    setTracksOpen(false);
    setPlaybackOpen(false);
    setDockExpanded(expanded);
  });
  const dockResizeObserver = new ResizeObserver(entries => {
    workspace.style.setProperty('--tabs-dock-height', entries[0].target.getBoundingClientRect().height + 'px');
    scheduleMeasureClearance();
  });
  dockResizeObserver.observe(floatingDock);
  const scoreResizeObserver = new ResizeObserver(() => {
    updateScoreScrollRoom();
    scheduleMeasureClearance();
  });
  scoreResizeObserver.observe(scoreViewport);
  function setPlaybackOpen(open) {
    playbackPanel.hidden = !open;
    playbackToggle.setAttribute('aria-expanded', String(open));
    if (open) {
      setTracksOpen(false);
      setDockExpanded(false);
      syncFloatingControls();
    }
  }
  function syncFloatingControls() {
    workspace.querySelectorAll('[data-mirror]').forEach(control => {
      const source = document.getElementById(control.dataset.mirror);
      if (!source) return;
      control.disabled = source.disabled;
      if (source.matches('input, select')) {
        control.value = source.value;
        if (source.id === 'tab-master-volume') control.style.setProperty('--volume-fill', source.value + '%');
      } else {
        control.textContent = source.textContent;
      }
      const pressed = source.getAttribute('aria-pressed');
      if (pressed !== null) control.setAttribute('aria-pressed', pressed);
    });
  }
  // Mirror existing controls so both locations use the same player state.
  workspace.querySelectorAll('.tabs-viewer-main > .tab-controls-row').forEach(row => {
    const copy = row.cloneNode(true);
    copy.querySelectorAll('[id]').forEach(control => {
      const sourceId = control.id;
      control.id = 'floating-' + sourceId;
      control.dataset.mirror = sourceId;
      if (['tab-play', 'tab-loop', 'tab-print', 'tab-download', 'tab-download-midi'].includes(sourceId)) control.remove();
    });
    copy.querySelectorAll('label[for]').forEach(label => { label.htmlFor = 'floating-' + label.htmlFor; });
    if (row.classList.contains('tab-controls-row-secondary')) dockExtra.append(copy);
    else floatingOptions.append(copy);
  });
  let forwardingControl = false;
  workspace.addEventListener('click', event => {
    const control = event.target.closest('button[data-mirror]');
    if (!control) return;
    forwardingControl = true;
    try { document.getElementById(control.dataset.mirror).click(); }
    finally { forwardingControl = false; }
    syncFloatingControls();
  }, true);
  for (const eventName of ['input', 'change']) {
    workspace.addEventListener(eventName, event => {
      const control = event.target.closest('input[data-mirror], select[data-mirror]');
      if (!control) {
        syncFloatingControls();
        return;
      }
      const source = document.getElementById(control.dataset.mirror);
      source.value = control.value;
      source.dispatchEvent(new Event(eventName, { bubbles: true }));
      syncFloatingControls();
    });
  }
  const controlObserver = new MutationObserver(syncFloatingControls);
  workspace.querySelectorAll('.tabs-viewer-main > .tab-controls-row').forEach(row => {
    controlObserver.observe(row, { subtree: true, childList: true, attributes: true, attributeFilter: ['disabled', 'aria-pressed'] });
  });
  syncFloatingControls();
  playbackToggle.addEventListener('click', event => {
    event.stopPropagation();
    setPlaybackOpen(playbackPanel.hidden);
  });
  playbackPanel.addEventListener('click', event => event.stopPropagation());
  trackSidebarToggle.addEventListener('click', event => {
    event.stopPropagation();
    setTracksOpen(trackSidebar.hidden);
  });
  trackSidebar.addEventListener('click', event => event.stopPropagation());
  floatingDock.addEventListener('click', event => event.stopPropagation());
  document.addEventListener('click', () => {
    if (forwardingControl) return;
    if (!trackSidebar.hidden) setTracksOpen(false);
    if (!playbackPanel.hidden) setPlaybackOpen(false);
    if (floatingDock.classList.contains('expanded')) setDockExpanded(false);
  });
  trackSelect.addEventListener('change', () => {
    selectTrack(trackSelect.value);
    setTracksOpen(false);
    trackSidebarToggle.focus();
  });
  viewerExpandBtn.addEventListener('click', () => setViewerFocused(!workspace.classList.contains('focused'), true));
  libraryBtn.addEventListener('click', showLibrary);
  returnBtn.addEventListener('click', () => {
    setViewerFocused(true);
    songTitleEl.focus({ preventScroll: true });
  });
  document.addEventListener('keydown', event => {
    const target = event.target instanceof Element ? event.target : null;
    const editing = target && (target.isContentEditable || target.closest('input, textarea, select, [role="textbox"]'));
    if (currentScore && !editing && !event.ctrlKey && !event.metaKey && !event.altKey && !event.isComposing && !event.defaultPrevented) {
      const key = event.key.toLowerCase();
      if ([' ', 't', 'p', 'l'].includes(key)) {
        event.preventDefault();
        if (event.repeat) return;
        if (key === ' ') document.getElementById('tab-dock-play').click();
        else if (key === 't') setTracksOpen(trackSidebar.hidden);
        else if (key === 'p') setPlaybackOpen(playbackPanel.hidden);
        else if (key === 'l') document.getElementById('tab-dock-loop').click();
        return;
      }
    }
    if (event.key !== 'Escape') return;
    if (!trackSidebar.hidden) {
      setTracksOpen(false);
      trackSidebarToggle.focus();
    } else if (!playbackPanel.hidden) {
      setPlaybackOpen(false);
      playbackToggle.focus();
    } else if (floatingDock.classList.contains('expanded')) {
      setDockExpanded(false);
      dockExpand.focus();
    } else if (workspace.classList.contains('focused')) {
      setViewerFocused(false);
      viewerExpandBtn.focus();
    }
  });

  window.addEventListener("pagehide", function(event) {
    if (event.persisted) return;
    if (tabLoadController) tabLoadController.abort();
    if (indexRequestController) indexRequestController.abort();
    controlObserver.disconnect();
    dockResizeObserver.disconnect();
    scoreResizeObserver.disconnect();
    if (clearanceFrame !== null) cancelAnimationFrame(clearanceFrame);
    if (alphaApi) {
      alphaApi.destroy();
      alphaApi = null;
    }
  });

  // Playback controls
  if (playBtn) {
    playBtn.addEventListener("click", function() {
      if (!alphaApi) return;
      try {
        alphaApi.playPause();
      } catch (err) {
        console.warn("playPause unsupported:", err);
      }
    });
  }

  if (stopBtn) {
    stopBtn.addEventListener("click", function() {
      if (!alphaApi) return;
      try {
        alphaApi.stop();
      } catch (err) {
        console.warn("stop unsupported:", err);
      }
    });
  }

  // Playback speed
  if (speedSelect) {
    speedSelect.addEventListener("change", function() {
      const s = parseFloat(speedSelect.value);
      if (isNaN(s)) return;
      uiState.playbackSpeed = s;
      if (alphaApi) {
        try {
          alphaApi.playbackSpeed = s;
        } catch (err) {
          console.warn("Playback speed set unsupported:", err);
        }
      }
    });
  }

  // Master volume
  if (masterVolumeInput) {
    masterVolumeInput.addEventListener("input", function() {
      const v = parseInt(masterVolumeInput.value, 10);
      if (isNaN(v)) return;
      uiState.masterVolume = Math.max(0, Math.min(1, v / 100));
      masterVolumeInput.style.setProperty('--volume-fill', String(v) + '%');
      if (alphaApi) {
        try {
          alphaApi.masterVolume = uiState.masterVolume;
        } catch (err) {
          console.warn("Master volume set unsupported:", err);
        }
      }
    });
  }

  // Count-in / metronome / loop
  if (countInBtn) {
    countInBtn.addEventListener("click", function() {
      uiState.countIn = !uiState.countIn;
      setToggle(countInBtn, uiState.countIn);
      if (alphaApi) {
        try {
          alphaApi.countInVolume = uiState.countIn ? 1 : 0;
        } catch (err) {
          console.warn("Count-in unsupported:", err);
        }
      }
    });
    setToggle(countInBtn, uiState.countIn);
  }

  if (metronomeBtn) {
    metronomeBtn.addEventListener("click", function() {
      uiState.metronome = !uiState.metronome;
      setToggle(metronomeBtn, uiState.metronome);
      if (alphaApi) {
        try {
          alphaApi.metronomeVolume = uiState.metronome ? 1 : 0;
        } catch (err) {
          console.warn("Metronome unsupported:", err);
        }
      }
    });
    setToggle(metronomeBtn, uiState.metronome);
  }

  if (loopBtn) {
    loopBtn.addEventListener("click", function() {
      uiState.loop = !uiState.loop;
      setToggle(loopBtn, uiState.loop);
      if (alphaApi) {
        try {
          alphaApi.isLooping = uiState.loop;
        } catch (err) {
          console.warn("Looping unsupported:", err);
        }
      }
    });
    setToggle(loopBtn, uiState.loop);
  }

  // Zoom / layout / stave profile / transpose
  if (zoomSelect) {
    zoomSelect.addEventListener("change", function() {
      const z = parseInt(zoomSelect.value, 10);
      if (isNaN(z)) return;
      uiState.zoom = z / 100;
      applyDisplaySettings();
    });
  }

  if (layoutSelect) {
    layoutSelect.addEventListener("change", function() {
      uiState.layout = layoutSelect.value || "page";
      applyDisplaySettings();
    });
  }

  if (staveProfileSelect) {
    staveProfileSelect.addEventListener("change", function() {
      uiState.staveProfile = staveProfileSelect.value || "default";
      applyDisplaySettings();
    });
  }

  if (transposeSelect) {
    transposeSelect.addEventListener("change", function() {
      const t = parseInt(transposeSelect.value, 10);
      if (isNaN(t)) return;
      uiState.transpose = t;
      applyTranspose();
    });
  }

  // Print current tab
  if (printBtn) {
    printBtn.addEventListener("click", function() {
      if (!alphaApi) return;
      try {
        if (typeof alphaApi.print === "function") {
          alphaApi.print();
        }
      } catch (err) {
        console.warn("print unsupported:", err);
      }
    });
  }

  // Download current tab file
  if (downloadBtn) {
    downloadBtn.addEventListener("click", function() {
      if (!currentTabItem || !currentTabItem.file) return;
      const a = document.createElement("a");
      a.href = currentTabItem.file;
      a.download = (currentTabItem.title || "tab");
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    });
  }

  // Download MIDI
  if (downloadMidiBtn) {
    downloadMidiBtn.addEventListener("click", function() {
      if (!alphaApi) return;
      try {
        if (typeof alphaApi.downloadMidi === "function") {
          alphaApi.downloadMidi();
        }
      } catch (err) {
        console.warn("Download MIDI unsupported:", err);
      }
    });
  }

  // Search / sort / paginate wiring
  searchInput.addEventListener("input", function() {
    currentPage = 1;
    if (useRemoteApi) {
      window.clearTimeout(searchDebounce);
      searchDebounce = window.setTimeout(function() {
        applyFiltersAndRender();
      }, 200);
      return;
    }
    applyFiltersAndRender();
  });

  sortSelect.addEventListener("change", function() {
    currentPage = 1;
    applyFiltersAndRender();
  });

  if (folderSelect) {
    folderSelect.addEventListener("change", function() {
      currentPage = 1;
      applyFiltersAndRender();
    });
  }

  prevBtn.addEventListener("click", function() {
    if (currentPage > 1) {
      if (useRemoteApi) {
        fetchRemotePage(currentPage - 1).catch(function(err) {
          console.error("Failed to fetch previous tabs page:", err);
        });
        return;
      }
      currentPage--;
      renderPage();
    }
  });

  nextBtn.addEventListener("click", function() {
    const maxPage = Math.max(1, Math.ceil(totalTabs / PAGE_SIZE));
    if (currentPage < maxPage) {
      if (useRemoteApi) {
        fetchRemotePage(currentPage + 1).catch(function(err) {
          console.error("Failed to fetch next tabs page:", err);
        });
        return;
      }
      currentPage++;
      renderPage();
    }
  });

  if (uploadBtn) {
    uploadBtn.addEventListener("click", function() {
      if (uploadBtn.disabled || !uploadInput) return;
      uploadInput.click();
    });
  }

  if (uploadInput) {
    uploadInput.addEventListener("change", function() {
      uploadTab();
    });
  }

  document.addEventListener("DOMContentLoaded", loadIndex);
})();
</script>
