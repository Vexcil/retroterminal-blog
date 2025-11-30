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

  <div class="tabs-viewer-layout">
    <aside class="tab-sidebar">
      <h3 class="tab-sidebar-title">Tracks</h3>
      <ul id="track-list" class="track-list">
        <!-- filled by JS -->
      </ul>
    </aside>

    <section class="tab-main-area">
      <div class="tab-toolbar">
        <div class="tab-toolbar-group">
          <button id="tab-play">Play / Pause</button>
          <button id="tab-stop">Stop</button>
        </div>

        <div class="tab-toolbar-group">
          <label for="layout-select">Layout:</label>
          <select id="layout-select">
            <option value="page">Page (vertical)</option>
            <option value="horizontal">Horizontal</option>
          </select>
        </div>

        <div class="tab-toolbar-group">
          <label for="speed-select">Speed:</label>
          <select id="speed-select">
            <option value="0.5">50%</option>
            <option value="0.75">75%</option>
            <option value="1" selected>100%</option>
            <option value="1.25">125%</option>
            <option value="1.5">150%</option>
          </select>
        </div>

        <div class="tab-toolbar-group">
          <label for="zoom-select">Zoom:</label>
          <select id="zoom-select">
            <option value="0.8">80%</option>
            <option value="1" selected>100%</option>
            <option value="1.2">120%</option>
            <option value="1.4">140%</option>
            <option value="1.6">160%</option>
          </select>
        </div>

        <div class="tab-toolbar-group">
          <button id="tab-print">Print</button>
          <a id="tab-download" href="#" target="_blank" rel="noopener" class="tab-download-link">Download</a>
        </div>
      </div>

      <p id="current-tab-title"></p>

      <div class="at-wrap">
        <div class="at-viewport">
          <div class="at-main" id="alphaTab"></div>
        </div>
      </div>
    </section>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/@coderline/alphatab@1.6.0/dist/alphaTab.min.js"></script>
<script>
(function() {
  const PAGE_SIZE = 100;

  let allTabs = [];
  let filteredTabs = [];
  let currentPage = 1;

  const searchInput      = document.getElementById('tab-search');
  const sortSelect       = document.getElementById('tab-sort');
  const listEl           = document.getElementById('tab-list');
  const pageInfoEl       = document.getElementById('tab-page-info');
  const prevBtn          = document.getElementById('tab-prev');
  const nextBtn          = document.getElementById('tab-next');

  const currentTitleEl   = document.getElementById('current-tab-title');
  const viewerContainer  = document.getElementById('alphaTab');
  const trackListEl      = document.getElementById('track-list');

  const playBtn          = document.getElementById('tab-play');
  const stopBtn          = document.getElementById('tab-stop');
  const layoutSelect     = document.getElementById('layout-select');
  const speedSelect      = document.getElementById('speed-select');
  const zoomSelect       = document.getElementById('zoom-select');
  const printBtn         = document.getElementById('tab-print');
  const downloadLink     = document.getElementById('tab-download');

  let alphaApi       = null;
  let currentScore   = null;
  let currentLayout  = 'page';    // 'page' or 'horizontal'
  let currentTabItem = null;

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

  function clearTrackList() {
    if (!trackListEl) return;
    trackListEl.innerHTML = "";
  }

  function populateTracks(score) {
    if (!trackListEl || !score || !score.tracks) return;

    clearTrackList();

    // "All tracks" row
    const allLi = document.createElement("li");
    allLi.className = "track-item track-item-active";
    allLi.dataset.mode = "all";
    allLi.textContent = "All tracks";
    trackListEl.appendChild(allLi);

    score.tracks.forEach(track => {
      const li = document.createElement("li");
      li.className = "track-item";
      li.dataset.mode = "single";
      li.dataset.index = String(track.index);
      li.textContent = track.name || ("Track " + (track.index + 1));
      trackListEl.appendChild(li);
    });
  }

  function applyZoom() {
    if (!zoomSelect || !viewerContainer) return;
    const factor = parseFloat(zoomSelect.value) || 1;
    viewerContainer.style.transform = "scale(" + factor + ")";
    viewerContainer.style.transformOrigin = "0 0";
  }

  function createAlphaTab(item) {
    viewerContainer.innerHTML = "";
    currentScore = null;
    clearTrackList();

    const viewport = document.querySelector(".at-viewport");

    // AlphaTab LayoutMode: 0 = Page, 1 = Horizontal
    const layoutModeNumeric = (currentLayout === 'page') ? 0 : 1;

    const settings = {
      file: item.file,
      display: {
        staveProfile: "tab",
        layoutMode: layoutModeNumeric
      },
      player: {
        enablePlayer: true,
        enableCursor: true,
        enableElementHighlighting: true,
        enableUserInteraction: true,
        scrollElement: viewport,
        soundFont: "https://cdn.jsdelivr.net/npm/@coderline/alphatab@latest/dist/soundfont/sonivox.sf2"
      }
    };

    alphaApi = new alphaTab.AlphaTabApi(viewerContainer, settings);

    alphaApi.scoreLoaded.on(function(score) {
      currentScore = score;
      populateTracks(score);
      applyZoom();
      // apply speed to new instance
      if (speedSelect) {
        const s = parseFloat(speedSelect.value) || 1;
        alphaApi.playbackSpeed = s;
      }
    });
  }

  function loadTab(item) {
    currentTabItem = item;
    currentTitleEl.textContent = item.title;
    if (downloadLink) {
      downloadLink.href = item.file;
    }
    createAlphaTab(item);
  }

  // Track list click: select track or all tracks
  if (trackListEl) {
    trackListEl.addEventListener("click", function(e) {
      const li = e.target.closest(".track-item");
      if (!li || !alphaApi || !currentScore) return;

      const mode = li.dataset.mode;

      // update active style
      trackListEl.querySelectorAll(".track-item").forEach(el => {
        el.classList.remove("track-item-active");
      });
      li.classList.add("track-item-active");

      if (mode === "all") {
        alphaApi.renderScore(currentScore);
      } else {
        const idx = parseInt(li.dataset.index, 10);
        if (isNaN(idx)) return;
        const track = currentScore.tracks.find(t => t.index === idx);
        if (track) {
          alphaApi.renderTracks([track]);
        }
      }
    });
  }

  // Layout toggle
  if (layoutSelect) {
    layoutSelect.value = "page";
    layoutSelect.addEventListener("change", function() {
      currentLayout = layoutSelect.value === "horizontal" ? "horizontal" : "page";
      if (currentTabItem) {
        createAlphaTab(currentTabItem);
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

  // Speed control
  if (speedSelect) {
    speedSelect.addEventListener("change", function() {
      if (!alphaApi) return;
      const s = parseFloat(speedSelect.value) || 1;
      alphaApi.playbackSpeed = s;
    });
  }

  // Zoom control
  if (zoomSelect) {
    zoomSelect.addEventListener("change", function() {
      applyZoom();
    });
  }

  // Print: print current page
  if (printBtn) {
    printBtn.addEventListener("click", function() {
      window.print();
    });
  }

  // Pagination and filters
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
