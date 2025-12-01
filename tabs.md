---
layout: default
title: Guitar Tabs
permalink: /tabs/
noindex: true
---

<div class="tabs-page">
  <div class="tabs-controls">
    <input type="text" id="tab-search" placeholder="Search by title..." />
    <select id="tab-sort">
      <option value="title-asc">Title A to Z</option>
      <option value="title-desc">Title Z to A</option>
    </select>
  </div>

  <div id="tab-list"></div>

  <div class="tabs-pagination">
    <button id="tab-prev">Prev</button>
    <span id="tab-page-info"></span>
    <button id="tab-next">Next</button>
  </div>

  <hr>

  <h2>Viewer</h2>

  <div class="tab-controls-row">
    <div class="tab-player-controls">
      <button id="tab-play">Play</button>
      <button id="tab-stop">Stop</button>
    </div>

    <div class="tab-layout-select">
      <label for="layout-select">Layout:</label>
      <select id="layout-select">
        <option value="page" selected>Pages</option>
        <option value="horizontal">Scroll</option>
      </select>
    </div>
  </div>

  <!-- Track panel with mute / solo / volume, collapsed rows -->
  <div id="track-panel" class="track-panel"></div>

  <p id="current-tab-title"></p>
  <div class="at-wrap">
    <div class="at-viewport">
      <div class="at-main" id="alphaTab"></div>
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
  const trackPanel      = document.getElementById('track-panel');

  let alphaApi       = null;
  let currentScore   = null;
  let currentLayout  = 'page'; // default to page layout
  let currentTabItem = null;

  // simple per-track state cache for UI
  const trackState = {}; // index -> { mute: bool, solo: bool, volume: number }

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

  function buildTrackPanel(score) {
    if (!trackPanel || !score || !score.tracks) return;
    trackPanel.innerHTML = "";

    score.tracks.forEach(track => {
      const idx = track.index;

      if (!trackState[idx]) {
        trackState[idx] = {
          mute: false,
          solo: false,
          volume: 12  // mid volume by default
        };
      }

      const state = trackState[idx];

      const row = document.createElement('div');
      row.className = 'track-row collapsed';
      row.dataset.index = String(idx);

      const header = document.createElement('div');
      header.className = 'track-header';

      const icon = document.createElement('div');
      icon.className = 'track-icon';
      icon.textContent = 'TR'; // small label, no emoji

      const name = document.createElement('div');
      name.className = 'track-name';
      name.textContent = track.name || ("Track " + (idx + 1));

      header.appendChild(icon);
      header.appendChild(name);
      row.appendChild(header);

      const controls = document.createElement('div');
      controls.className = 'track-controls';

      const muteBtn = document.createElement('button');
      muteBtn.className = 'track-btn track-btn-mute';
      muteBtn.textContent = 'Mute';
      if (state.mute) muteBtn.classList.add('active');

      const soloBtn = document.createElement('button');
      soloBtn.className = 'track-btn track-btn-solo';
      soloBtn.textContent = 'Solo';
      if (state.solo) soloBtn.classList.add('active');

      const volWrap = document.createElement('div');
      volWrap.className = 'track-volume-wrap';

      const volLabel = document.createElement('span');
      volLabel.className = 'track-volume-label';
      volLabel.textContent = 'Vol';

      const volInput = document.createElement('input');
      volInput.type = 'range';
      volInput.min = '0';
      volInput.max = '16';
      volInput.value = String(state.volume);
      volInput.className = 'track-volume';

      volWrap.appendChild(volLabel);
      volWrap.appendChild(volInput);

      controls.appendChild(muteBtn);
      controls.appendChild(soloBtn);
      controls.appendChild(volWrap);

      row.appendChild(controls);
      trackPanel.appendChild(row);

      // click header to expand/collapse
      header.addEventListener('click', function() {
        row.classList.toggle('collapsed');
      });

      // mute toggle
      muteBtn.addEventListener('click', function(ev) {
        ev.stopPropagation();
        state.mute = !state.mute;
        muteBtn.classList.toggle('active', state.mute);

        if (alphaApi && typeof alphaApi.changeTrackMute === 'function') {
          alphaApi.changeTrackMute(idx, state.mute);
        }
      });

      // solo toggle
      soloBtn.addEventListener('click', function(ev) {
        ev.stopPropagation();
        state.solo = !state.solo;
        soloBtn.classList.toggle('active', state.solo);

        if (alphaApi && typeof alphaApi.changeTrackSolo === 'function') {
          alphaApi.changeTrackSolo(idx, state.solo);
        }
      });

      // volume slider
      volInput.addEventListener('input', function(ev) {
        ev.stopPropagation();
        const v = parseInt(volInput.value, 10);
        if (!isNaN(v)) {
          state.volume = v;
          if (alphaApi && typeof alphaApi.changeTrackVolume === 'function') {
            alphaApi.changeTrackVolume(idx, v);
          }
        }
      });
    });
  }

  function createAlphaTab(item) {
    viewerContainer.innerHTML = "";
    currentScore = null;

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
      buildTrackPanel(score);
    });
  }

  function loadTab(item) {
    currentTabItem = item;
    currentTitleEl.textContent = item.title;
    createAlphaTab(item);
  }

  // layout switch: page vs horizontal
  if (layoutSelect) {
    layoutSelect.value = 'page';
    layoutSelect.addEventListener('change', function() {
      currentLayout = layoutSelect.value === 'horizontal' ? 'horizontal' : 'page';
      if (currentTabItem) {
        createAlphaTab(currentTabItem);
      }
    });
  }

  // playback: separate Play and Stop
  if (playBtn) {
    playBtn.addEventListener('click', function() {
      if (!alphaApi) return;
      // play() will start or resume depending on alphaTab version
      if (typeof alphaApi.play === 'function') {
        alphaApi.play();
      } else if (typeof alphaApi.playPause === 'function') {
        alphaApi.playPause();
      }
    });
  }

  if (stopBtn) {
    stopBtn.addEventListener('click', function() {
      if (!alphaApi) return;
      if (typeof alphaApi.stop === 'function') {
        alphaApi.stop();
      }
    });
  }

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

  document.addEventListener("DOMContentLoaded", loadIndex);
})();
</script>
