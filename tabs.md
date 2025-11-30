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
    <div class="tab-track-select">
      <label for="track-select">Track:</label>
      <select id="track-select">
        <option value="all">All tracks</option>
      </select>
    </div>

    <div class="tab-player-controls">
      <button id="tab-play">Play / Pause</button>
      <button id="tab-stop">Stop</button>
    </div>

    <div class="tab-layout-select">
      <label for="layout-select">Layout:</label>
      <select id="layout-select">
        <option value="horizontal">Scroll</option>
        <option value="page">Pages</option>
      </select>
    </div>
  </div>

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

  const searchInput = document.getElementById('tab-search');
  const sortSelect = document.getElementById('tab-sort');
  const listEl = document.getElementById('tab-list');
  const pageInfoEl = document.getElementById('tab-page-info');
  const prevBtn = document.getElementById('tab-prev');
  const nextBtn = document.getElementById('tab-next');
  const currentTitleEl = document.getElementById('current-tab-title');
  const viewerContainer = document.getElementById('alphaTab');
  const trackSelect = document.getElementById('track-select');
  const playBtn = document.getElementById('tab-play');
  const stopBtn = document.getElementById('tab-stop');
  const layoutSelect = document.getElementById('layout-select');

  let alphaApi = null;
  let currentScore = null;
  let currentLayout = 'horizontal'; // 'horizontal' or 'page'
  let currentTabItem = null;        // remember which file is loaded

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
      if (ta > tb) return sortVal === "title-asc" ? 1 : -1;
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
    const start = (currentPage - 1) * PAGE_SIZE;
    const end = Math.min(start + PAGE_SIZE, filteredTabs.length);
    const slice = filteredTabs.slice(start, end);

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

  function clearTrackSelect() {
    if (!trackSelect) return;
    trackSelect.innerHTML = "";

    const optAll = document.createElement("option");
    optAll.value = "all";
    optAll.textContent = "All tracks";
    trackSelect.appendChild(optAll);
  }

  function populateTracks(score) {
    if (!trackSelect || !score || !score.tracks) return;

    clearTrackSelect();

    score.tracks.forEach(track => {
      const opt = document.createElement("option");
      opt.value = String(track.index);   // stable index per score
      opt.textContent = track.name || ("Track " + (track.index + 1));
      trackSelect.appendChild(opt);
    });
  }

  function buildLayoutConfig() {
    if (currentLayout === 'page') {
      // Page mode, tune these numbers if you want shorter/taller pages
      return {
        mode: 'page',
        pageFormat: 'a4',
        margin: 10,
        stretchForce: 0
      };
    } else {
      // Classic scrolling layout
      return 'horizontal';
    }
  }

  function createAlphaTab(item) {
    viewerContainer.innerHTML = "";
    currentScore = null;

    alphaApi = new alphaTab.AlphaTabApi(viewerContainer, {
      file: item.file,
      layout: buildLayoutConfig(),
      display: {
        staveProfile: "tab"
      },
      player: {
        enablePlayer: true,
        soundFont: "https://cdn.jsdelivr.net/npm/@coderline/alphatab@latest/dist/soundfont/sonivox.sf2"
      }
    });

    alphaApi.scoreLoaded.on(function(score) {
      currentScore = score;
      populateTracks(score);
    });
  }

  function loadTab(item) {
    currentTabItem = item;
    currentTitleEl.textContent = item.title;
    createAlphaTab(item);
  }

  // Track selection handler
  if (trackSelect) {
    trackSelect.addEventListener("change", function() {
      if (!alphaApi || !currentScore) return;

      const val = trackSelect.value;

      if (val === "all") {
        alphaApi.renderScore(currentScore);
      } else {
        const idx = parseInt(val, 10);
        if (isNaN(idx)) return;

        const track = currentScore.tracks.find(t => t.index === idx);
        if (track) {
          alphaApi.renderTracks([track]);
        }
      }
    });
  }

  // Playback controls
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

  // Layout mode toggle: Scroll vs Pages
  if (layoutSelect) {
    layoutSelect.addEventListener("change", function() {
      currentLayout = layoutSelect.value; // 'horizontal' or 'page'

      // If a tab is already loaded, rebuild it with the new layout
      if (currentTabItem) {
        createAlphaTab(currentTabItem);
      }
    });
  }

  // Filters
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
