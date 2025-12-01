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

  <p id="current-tab-title"></p>

  <!-- Viewer shell: track sidebar + main area -->
  <div class="tabs-viewer-shell">
    <aside class="at-sidebar" id="track-sidebar">
      <div class="at-sidebar-title">Tracks</div>
      <div class="at-sidebar-empty">Load a tab to see tracks.</div>
    </aside>

    <div class="tabs-viewer-main">
      <div class="tab-controls-row">
        <div class="tab-layout-select">
          <label for="layout-select">Layout:</label>
          <select id="layout-select">
            <option value="horizontal">Scroll</option>
            <option value="page">Pages</option>
          </select>
        </div>

        <div class="tab-player-controls">
          <button id="tab-play">Play / Pause</button>
          <button id="tab-stop">Stop</button>
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
  const layoutSelect    = document.getElementById('layout-select');
  const playBtn         = document.getElementById('tab-play');
  const stopBtn         = document.getElementById('tab-stop');
  const trackSidebar    = document.getElementById('track-sidebar');

  let alphaApi        = null;
  let currentScore    = null;
  let currentTabItem  = null;
  let currentLayout   = 'Horizontal'; // "Horizontal" or "Page"

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

  function clearTrackSidebar() {
    if (!trackSidebar) return;
    trackSidebar.innerHTML = '';

    const titleDiv = document.createElement('div');
    titleDiv.className = 'at-sidebar-title';
    titleDiv.textContent = 'Tracks';
    trackSidebar.appendChild(titleDiv);

    const empty = document.createElement('div');
    empty.className = 'at-sidebar-empty';
    empty.textContent = 'Load a tab to see tracks.';
    trackSidebar.appendChild(empty);
  }

  function buildTrackSidebar(score) {
    if (!trackSidebar) return;

    trackSidebar.innerHTML = '';

    const titleDiv = document.createElement('div');
    titleDiv.className = 'at-sidebar-title';
    titleDiv.textContent = 'Tracks';
    trackSidebar.appendChild(titleDiv);

    if (!score.tracks || score.tracks.length === 0) {
      const empty = document.createElement('div');
      empty.className = 'at-sidebar-empty';
      empty.textContent = 'No tracks available.';
      trackSidebar.appendChild(empty);
      return;
    }

    score.tracks.forEach(track => {
      const row = document.createElement('div');
      row.className = 'at-track-row';
      row.dataset.index = String(track.index);

      const icon = document.createElement('div');
      icon.className = 'at-track-icon';
      icon.textContent = '♪';

      const nameSpan = document.createElement('span');
      nameSpan.className = 'at-track-name';
      nameSpan.textContent = track.name || ('Track ' + (track.index + 1));

      row.appendChild(icon);
      row.appendChild(nameSpan);

      row.addEventListener('click', function() {
        if (!alphaApi || !currentScore) return;

        // Mark active row
        trackSidebar.querySelectorAll('.at-track-row').forEach(r => {
          r.classList.remove('active');
        });
        row.classList.add('active');

        // Render only this track
        alphaApi.renderTracks([track]);
      });

      trackSidebar.appendChild(row);
    });

    // Default: show all tracks as active "virtual" entry
    const allRow = document.createElement('div');
    allRow.className = 'at-track-row at-track-row-all active';
    allRow.textContent = 'All tracks';
    allRow.addEventListener('click', function() {
      if (!alphaApi || !currentScore) return;
      trackSidebar.querySelectorAll('.at-track-row').forEach(r => {
        r.classList.remove('active');
      });
      allRow.classList.add('active');
      alphaApi.renderScore(currentScore);
    });

    // Insert "All tracks" at top below title
    const firstTrack = trackSidebar.querySelector('.at-track-row');
    trackSidebar.insertBefore(allRow, firstTrack);
  }

  function createAlphaTab(item) {
    viewerContainer.innerHTML = '';
    currentScore = null;
    clearTrackSidebar();

    const settings = {
      file: item.file,
      display: {
        staveProfile: "tab",
        layoutMode: currentLayout // "Horizontal" or "Page"
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
      buildTrackSidebar(score);
    });
  }

  function loadTab(item) {
    currentTabItem = item;
    currentTitleEl.textContent = item.title;
    createAlphaTab(item);
  }

  // Layout toggle
  if (layoutSelect) {
    layoutSelect.addEventListener('change', function() {
      if (layoutSelect.value === 'page') {
        currentLayout = 'Page';
      } else {
        currentLayout = 'Horizontal';
      }
      if (currentTabItem) {
        createAlphaTab(currentTabItem);
      }
    });
  }

  // Playback controls
  if (playBtn) {
    playBtn.addEventListener('click', function() {
      if (!alphaApi) return;
      alphaApi.playPause();
    });
  }

  if (stopBtn) {
    stopBtn.addEventListener('click', function() {
      if (!alphaApi) return;
      alphaApi.stop();
    });
  }

  // Search / sort / paginate
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
