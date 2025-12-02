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

  <div class="tabs-viewer-shell" id="tabs-viewer-shell">
    <!-- Track sidebar (collapsed by default) -->
    <div class="at-sidebar collapsed" id="track-sidebar">
      <div class="at-sidebar-toggle" id="track-sidebar-toggle">
        TRACKS
      </div>
      <div class="at-sidebar-inner">
        <div class="at-sidebar-title">Tracks</div>
        <div class="at-track-row at-track-row-all" data-track-index="all">
          <span class="at-track-name">All tracks</span>
        </div>
        <div id="track-list"></div>
      </div>
    </div>

    <!-- Main viewer column -->
    <div class="tabs-viewer-main">
      <div class="tab-controls-row">
        <div class="tab-player-controls">
          <button id="tab-play">Play</button>
          <button id="tab-stop">Stop</button>

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

          <button id="tab-print">Print</button>
          <button id="tab-download">Download</button>
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
  const PAGE_SIZE = 10; // show ~10 per page, rest via pagination

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

  const playBtn          = document.getElementById('tab-play');
  const stopBtn          = document.getElementById('tab-stop');
  const speedSelect      = document.getElementById('tab-speed');
  const printBtn         = document.getElementById('tab-print');
  const downloadBtn      = document.getElementById('tab-download');

  const trackSidebar     = document.getElementById('track-sidebar');
  const trackSidebarToggle = document.getElementById('track-sidebar-toggle');
  const trackListEl      = document.getElementById('track-list');
  const trackAllRow      = document.querySelector('.at-track-row-all');

  let alphaApi       = null;
  let currentScore   = null;
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

  function clearTracks() {
    if (!trackListEl) return;
    trackListEl.innerHTML = "";
    if (trackAllRow) {
      trackAllRow.classList.remove("active");
    }
  }

  function populateTracks(score) {
    if (!score || !score.tracks || !trackListEl) return;

    clearTracks();

    score.tracks.forEach(track => {
      const row = document.createElement("div");
      row.className = "at-track-row";
      row.dataset.trackIndex = String(track.index);

      const header = document.createElement("div");
      header.className = "at-track-header";

      const nameSpan = document.createElement("span");
      nameSpan.className = "at-track-name";
      nameSpan.textContent = track.name || ("Track " + (track.index + 1));

      const buttonsDiv = document.createElement("div");
      buttonsDiv.className = "at-track-buttons";

      const muteBtn = document.createElement("button");
      muteBtn.type = "button";
      muteBtn.className = "track-mute";
      muteBtn.textContent = "M";

      const soloBtn = document.createElement("button");
      soloBtn.type = "button";
      soloBtn.className = "track-solo";
      soloBtn.textContent = "S";

      buttonsDiv.appendChild(muteBtn);
      buttonsDiv.appendChild(soloBtn);

      header.appendChild(nameSpan);
      header.appendChild(buttonsDiv);

      const volWrap = document.createElement("div");
      volWrap.className = "at-track-volume";

      const volSlider = document.createElement("input");
      volSlider.type = "range";
      volSlider.min = "0";
      volSlider.max = "16";
      volSlider.value = "12";

      volWrap.appendChild(volSlider);

      row.appendChild(header);
      row.appendChild(volWrap);
      trackListEl.appendChild(row);

      // Track selection on row click (excluding buttons/slider)
      row.addEventListener("click", function(e) {
        if ((e.target && e.target.closest(".track-mute")) ||
            (e.target && e.target.closest(".track-solo")) ||
            (e.target && e.target.closest(".at-track-volume"))) {
          return;
        }

        if (!alphaApi || !currentScore) return;

        const idx = track.index;
        const selectedTrack = currentScore.tracks.find(t => t.index === idx);
        if (!selectedTrack) return;

        document
          .querySelectorAll(".at-track-row")
          .forEach(el => el.classList.remove("active"));
        row.classList.add("active");

        if (trackAllRow) {
          trackAllRow.classList.remove("active");
        }

        alphaApi.renderTracks([selectedTrack]);
      });

      // Mute toggle
      muteBtn.addEventListener("click", function(e) {
        e.stopPropagation();
        if (!alphaApi) return;
        const isMuted = muteBtn.classList.toggle("on");
        try {
          if (typeof alphaApi.setTrackMute === "function") {
            alphaApi.setTrackMute(track.index, isMuted);
          }
        } catch (err) {
          console.warn("Track mute unsupported:", err);
        }
      });

      // Solo toggle
      soloBtn.addEventListener("click", function(e) {
        e.stopPropagation();
        if (!alphaApi || !currentScore) return;

        const isSolo = soloBtn.classList.toggle("on");

        try {
          if (typeof alphaApi.setTrackSolo === "function") {
            currentScore.tracks.forEach(t => {
              alphaApi.setTrackSolo(t.index, false);
            });
            if (isSolo) {
              alphaApi.setTrackSolo(track.index, true);
            }
          }
        } catch (err) {
          console.warn("Track solo unsupported:", err);
        }
      });

      // Volume slider
      volSlider.addEventListener("input", function(e) {
        if (!alphaApi) return;
        const v = parseInt(e.target.value, 10);
        if (isNaN(v)) return;
        try {
          if (typeof alphaApi.setTrackVolume === "function") {
            alphaApi.setTrackVolume(track.index, v);
          }
        } catch (err) {
          console.warn("Track volume unsupported:", err);
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
        layoutMode: "page" // default to vertical page layout
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
  }

  function loadTab(item) {
    currentTabItem = item;
    currentTitleEl.textContent = item.title;
    createAlphaTab(item);
  }

  // Sidebar toggle (collapsed by default)
  if (trackSidebar && trackSidebarToggle) {
    trackSidebarToggle.addEventListener("click", function() {
      const collapsed = trackSidebar.classList.toggle("collapsed");
      trackSidebarToggle.textContent = collapsed ? "TRACKS" : "TRACKS ◂";
    });
  }

  // "All tracks" selector
  if (trackAllRow) {
    trackAllRow.addEventListener("click", function() {
      if (!alphaApi || !currentScore) return;

      document
        .querySelectorAll(".at-track-row")
        .forEach(el => el.classList.remove("active"));

      trackAllRow.classList.add("active");
      alphaApi.renderScore(currentScore);
    });
  }

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
      if (!alphaApi) return;
      const s = parseFloat(speedSelect.value);
      if (isNaN(s)) return;
      try {
        alphaApi.playbackSpeed = s;
      } catch (err) {
        console.warn("Playback speed set unsupported:", err);
      }
    });
  }

  // Print current tab: open a simple print window with rendered SVG
  if (printBtn) {
    printBtn.addEventListener("click", function() {
      if (!viewerContainer || !viewerContainer.innerHTML) return;

      const w = window.open("", "_blank");
      if (!w) return;

      w.document.write("<html><head><title>" +
        (currentTitleEl.textContent || "Tab") +
        "</title>");
      w.document.write("<style>body{margin:0;padding:0;background:#fff;color:#000;font-family:sans-serif;}svg{width:100%;height:auto;}</style>");
      w.document.write("</head><body>");
      w.document.write(viewerContainer.innerHTML);
      w.document.write("</body></html>");
      w.document.close();
      w.focus();
      w.print();
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

  // Search / sort / paginate wiring
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
