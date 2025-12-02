---
layout: default
title: Guitar Tabs
permalink: /tabs/
noindex: true
---

<div class="tabs-page">
  <!-- Search / sort -->
  <div class="tabs-controls">
    <input type="text" id="tab-search" placeholder="Search by title..." />
    <select id="tab-sort">
      <option value="title-asc">Title A to Z</option>
      <option value="title-desc">Title Z to A</option>
    </select>
  </div>

  <!-- Scroll-limited tab list -->
  <div id="tab-list"></div>

  <div class="tabs-pagination">
    <button id="tab-prev">Prev</button>
    <span id="tab-page-info"></span>
    <button id="tab-next">Next</button>
  </div>

  <hr>

  <h2>Viewer</h2>

  <p id="current-tab-title"></p>

  <div class="tabs-viewer-shell">
    <!-- LEFT: track sidebar -->
    <aside class="at-sidebar" id="track-sidebar">
      <div class="at-sidebar-title">Tracks</div>
      <div class="at-sidebar-empty">Load a tab to see tracks.</div>
      <div class="at-track-list" id="track-list"></div>
    </aside>

    <!-- RIGHT: controls + main viewer -->
    <div class="tabs-viewer-main">
      <div class="tab-controls-row">
        <div class="tab-player-controls">
          <!-- Play toggles play/pause, Stop resets to start -->
          <button id="tab-play">Play / Pause</button>
          <button id="tab-stop">Stop</button>
        </div>

        <div class="tab-speed-select">
          <label for="speed-select">Speed:</label>
          <select id="speed-select">
            <option value="0.25">0.25×</option>
            <option value="0.5">0.5×</option>
            <option value="0.75">0.75×</option>
            <option value="0.9">0.9×</option>
            <option value="1" selected>1×</option>
            <option value="1.25">1.25×</option>
            <option value="1.5">1.5×</option>
            <option value="2">2×</option>
          </select>
        </div>

        <div class="tab-layout-select">
          <label for="layout-select">Layout:</label>
          <select id="layout-select">
            <option value="page" selected>Pages</option>
            <option value="horizontal">Scroll</option>
          </select>
        </div>
      </div>

      <div class="at-wrap">
        <div class="at-viewport">
          <div class="at-main" id="alphaTab"></div>
        </div>
      </div>
    </div>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/@coderline/alphatab@1.6.0/dist/alphaTab.min.js"></script>
<script>
(function() {
  const PAGE_SIZE = 100;

  let allTabs = [];
  let filteredTabs = [];
  let currentPage = 1;

  const searchInput     = document.getElementById('tab-search');
  const sortSelect      = document.getElementById('tab-sort');
  const listEl          = document.getElementById('tab-list');
  const pageInfoEl      = document.getElementById('tab-page-info');
  const prevBtn         = document.getElementById('tab-prev');
  const nextBtn         = document.getElementById('tab-next');
  const currentTitleEl  = document.getElementById('current-tab-title');
  const viewerContainer = document.getElementById('alphaTab');
  const playBtn         = document.getElementById('tab-play');
  const stopBtn         = document.getElementById('tab-stop');
  const layoutSelect    = document.getElementById('layout-select');
  const speedSelect     = document.getElementById('speed-select');
  const trackSidebar    = document.getElementById('track-sidebar');
  const trackListEl     = document.getElementById('track-list');

  let alphaApi       = null;
  let currentScore   = null;
  let currentLayout  = 'page';  // 'page' or 'horizontal'
  let currentTabItem = null;

  /* =====================
     Index + list rendering
     ===================== */

  function loadIndex() {
    fetch('{{ "/assets/data/tabs.json" | relative_url }}', { cache: "no-store" })
      .then(r => r.json())
      .then(data => {
        allTabs = data;
        filteredTabs = allTabs.slice();
        applyFiltersAndRender();
      })
      .catch(err => {
        console.error("Error loading tabs index:", err);
        listEl.textContent = "Failed to load tab index.";
      });
  }

  function applyFiltersAndRender() {
    const q = (searchInput.value || "").toLowerCase();

    filteredTabs = allTabs.filter(item =>
      item.title.toLowerCase().includes(q)
    );

    const sortVal = sortSelect.value;
    filteredTabs.sort((a, b) => {
      const ta = a.title.toLowerCase();
      const tb = b.title.toLowerCase();
      if (ta < tb) return sortVal === "title-asc" ? -1 : 1;
      if (ta > tb) return sortVal === "title-asc" ?  1 : -1;
      return 0;
    });

    const maxPage = Math.max(1, Math.ceil(filteredTabs.length / PAGE_SIZE));
    if (currentPage > maxPage) currentPage = maxPage;

    renderPage();
  }

  function renderPage() {
    listEl.innerHTML = "";

    if (filteredTabs.length === 0) {
      listEl.textContent = "No tabs found.";
      pageInfoEl.textContent = "";
      return;
    }

    const maxPage = Math.max(1, Math.ceil(filteredTabs.length / PAGE_SIZE));
    const start   = (currentPage - 1) * PAGE_SIZE;
    const end     = Math.min(start + PAGE_SIZE, filteredTabs.length);
    const slice   = filteredTabs.slice(start, end);

    const ul = document.createElement("ul");
    ul.className = "tab-list-ul";

    slice.forEach(item => {
      const li = document.createElement("li");
      li.className = "tab-list-item";

      const titleSpan = document.createElement("span");
      titleSpan.className = "tab-title";
      titleSpan.textContent = item.title;

      const btn = document.createElement("button");
      btn.textContent = "View";
      btn.addEventListener("click", function() {
        loadTab(item);
      });

      li.appendChild(titleSpan);
      li.appendChild(btn);
      ul.appendChild(li);
    });

    listEl.appendChild(ul);

    pageInfoEl.textContent = "Page " + currentPage + " of " + maxPage;
    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= maxPage;
  }

  /* ================
     Track side panel
     ================ */

  function clearTrackSidebar() {
    if (!trackListEl) return;
    trackListEl.innerHTML = "";
    const empty = trackSidebar.querySelector(".at-sidebar-empty");
    if (empty) empty.style.display = "block";
  }

  function populateTracks(score) {
    if (!trackListEl || !score || !score.tracks) return;

    trackListEl.innerHTML = "";
    const empty = trackSidebar.querySelector(".at-sidebar-empty");
    if (empty) empty.style.display = "none";

    // "All tracks" row
    const allRow = document.createElement("div");
    allRow.className = "at-track-row at-track-row-all active";
    allRow.textContent = "All tracks";
    allRow.dataset.trackIndex = "all";
    allRow.addEventListener("click", function() {
      setActiveTrackRow(allRow);
      if (!alphaApi || !currentScore) return;
      alphaApi.renderScore(currentScore);
    });
    trackListEl.appendChild(allRow);

    // One row per track, collapsed by default
    score.tracks.forEach(track => {
      const row = document.createElement("div");
      row.className = "at-track-row";
      row.dataset.trackIndex = String(track.index);

      const nameSpan = document.createElement("span");
      nameSpan.className = "at-track-name";
      nameSpan.textContent = track.name || ("Track " + (track.index + 1));

      // controls wrapper (hidden until row "opened")
      const controls = document.createElement("div");
      controls.className = "at-track-controls";

      const muteBtn = document.createElement("button");
      muteBtn.type = "button";
      muteBtn.textContent = "Mute";
      muteBtn.className = "at-track-btn at-track-btn-mute";

      const soloBtn = document.createElement("button");
      soloBtn.type = "button";
      soloBtn.textContent = "Solo";
      soloBtn.className = "at-track-btn at-track-btn-solo";

      const volLabel = document.createElement("span");
      volLabel.className = "at-track-vol-label";
      volLabel.textContent = "Vol";

      const volSlider = document.createElement("input");
      volSlider.type = "range";
      volSlider.min = "0";
      volSlider.max = "1";
      volSlider.step = "0.05";
      volSlider.value = "1";
      volSlider.className = "at-track-volume";

      // clicking the row itself toggles "open" and selects the track
      row.addEventListener("click", function(e) {
        // ignore clicks on buttons/slider so their handlers work
        if (e.target.closest(".at-track-controls")) return;

        const idx = track.index;
        setActiveTrackRow(row);
        if (!alphaApi || !currentScore) return;
        const t = currentScore.tracks.find(t => t.index === idx);
        if (t) alphaApi.renderTracks([t]);
        row.classList.toggle("open");
      });

      // Mute / Solo / Volume hooks
      muteBtn.addEventListener("click", function(e) {
        e.stopPropagation();
        // TODO: wire to AlphaTab per-track mute API
        // Example placeholder:
        // alphaApi.setTrackMute(track.index, !isMuted);
        console.log("Mute track", track.index);
      });

      soloBtn.addEventListener("click", function(e) {
        e.stopPropagation();
        // TODO: wire to AlphaTab per-track solo API
        // Example placeholder:
        // alphaApi.setTrackSolo(track.index, !isSolo);
        console.log("Solo track", track.index);
      });

      volSlider.addEventListener("input", function(e) {
        e.stopPropagation();
        const val = parseFloat(volSlider.value);
        // TODO: wire to AlphaTab per-track volume API
        // Example placeholder:
        // alphaApi.setTrackVolume(track.index, val);
        console.log("Volume track", track.index, val);
      });

      controls.appendChild(muteBtn);
      controls.appendChild(soloBtn);
      controls.appendChild(volLabel);
      controls.appendChild(volSlider);

      row.appendChild(nameSpan);
      row.appendChild(controls);
      trackListEl.appendChild(row);
    });
  }

  function setActiveTrackRow(row) {
    if (!row) return;
    const rows = trackListEl.querySelectorAll(".at-track-row");
    rows.forEach(r => r.classList.remove("active"));
    row.classList.add("active");
  }

  /* ======================
     AlphaTab initialization
     ====================== */

  function createAlphaTab(item) {
    viewerContainer.innerHTML = "";
    currentScore = null;
    clearTrackSidebar();

    const settings = {
      file: item.file,
      display: {
        staveProfile: "tab",
        layoutMode: currentLayout === "page" ? "page" : "horizontal"
      },
      player: {
        enablePlayer: true,
        soundFont: "https://cdn.jsdelivr.net/npm/@coderline/alphatab@latest/dist/soundfont/sonivox.sf2",
        scrollElement: document.querySelector(".at-viewport")
      }
    };

    alphaApi = new alphaTab.AlphaTabApi(viewerContainer, settings);

    alphaApi.scoreLoaded.on(function(score) {
      currentScore = score;
      populateTracks(score);
      // reset playback speed UI
      if (speedSelect) speedSelect.value = "1";
    });
  }

  function loadTab(item) {
    currentTabItem = item;
    currentTitleEl.textContent = item.title;
    createAlphaTab(item);
  }

  /* =====================
     Controls / interactions
     ===================== */

  // Search/sort
  searchInput.addEventListener("input", function() {
    currentPage = 1;
    applyFiltersAndRender();
  });

  sortSelect.addEventListener("change", function() {
    currentPage = 1;
    applyFiltersAndRender();
  });

  prevBtn.addEventListener("click", function() {
    if (currentPage > 1) {
      currentPage--;
      renderPage();
    }
  });

  nextBtn.addEventListener("click", function() {
    const maxPage = Math.max(1, Math.ceil(filteredTabs.length / PAGE_SIZE));
    if (currentPage < maxPage) {
      currentPage++;
      renderPage();
    }
  });

  // Layout: pages vs scroll
  if (layoutSelect) {
    layoutSelect.addEventListener("change", function() {
      currentLayout = layoutSelect.value === "horizontal" ? "horizontal" : "page";
      if (currentTabItem) {
        createAlphaTab(currentTabItem);
      }
    });
  }

  // Playback:
  // Play button toggles play/pause, so "pause without reset" is built in.
  if (playBtn) {
    playBtn.addEventListener("click", function() {
      if (!alphaApi) return;
      alphaApi.playPause();
    });
  }

  if (stopBtn) {
    stopBtn.addEventListener("click", function() {
      if (!alphaApi) return;
      alphaApi.stop();
    });
  }

  // Playback speed dropdown
  if (speedSelect) {
    speedSelect.addEventListener("change", function() {
      if (!alphaApi) return;
      const val = parseFloat(speedSelect.value);
      if (!isNaN(val)) {
        // This assumes AlphaTab exposes playbackSpeed on the api.
        // If this line throws, swap it for the correct API from the docs
        // (e.g. alphaApi.setPlaybackSpeed(val)).
        alphaApi.playbackSpeed = val;
      }
    });
  }

  document.addEventListener("DOMContentLoaded", loadIndex);
})();
</script>
