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
  <p class="tab-song-info">
    <span id="tab-song-title"></span>
    <span class="tab-song-sep">-</span>
    <span id="tab-song-artist"></span>
  </p>

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
  // show ~30 per page, rest via pagination
  const PAGE_SIZE = 30;

  let allTabs = [];
  let filteredTabs = [];
  let currentPage = 1;

  const searchInput        = document.getElementById('tab-search');
  const sortSelect         = document.getElementById('tab-sort');
  const listEl             = document.getElementById('tab-list');
  const pageInfoEl         = document.getElementById('tab-page-info');
  const prevBtn            = document.getElementById('tab-prev');
  const nextBtn            = document.getElementById('tab-next');
  const currentTitleEl     = document.getElementById('current-tab-title');
  const songTitleEl        = document.getElementById('tab-song-title');
  const songArtistEl       = document.getElementById('tab-song-artist');
  const viewerContainer    = document.getElementById('alphaTab');

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
  const trackAllRow        = document.querySelector('.at-track-row-all');

  let alphaApi       = null;
  let currentScore   = null;
  let currentTabItem = null;

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

  function setToggle(btn, on) {
    if (!btn) return;
    btn.classList.toggle("on", on);
  }

  function formatTime(seconds) {
    if (!isFinite(seconds) || seconds < 0) return "00:00";
    const s = Math.floor(seconds);
    const m = Math.floor(s / 60);
    const r = s % 60;
    return String(m).padStart(2, "0") + ":" + String(r).padStart(2, "0");
  }

  function updateSongInfo(score) {
    if (!songTitleEl || !songArtistEl) return;
    const title = (score && score.title) ? score.title : "";
    const artist = (score && score.artist) ? score.artist : "";
    songTitleEl.textContent = title || "Unknown title";
    songArtistEl.textContent = artist || "Unknown artist";
  }

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
      volSlider.max = "100";
      volSlider.value = "100";

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
          if (typeof alphaApi.changeTrackMute === "function") {
            alphaApi.changeTrackMute([track], isMuted);
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
          if (typeof alphaApi.changeTrackSolo === "function") {
            if (isSolo) {
              document
                .querySelectorAll(".track-solo")
                .forEach(btn => btn.classList.remove("on"));
              soloBtn.classList.add("on");
              alphaApi.changeTrackSolo(currentScore.tracks, false);
              alphaApi.changeTrackSolo([track], true);
            } else {
              alphaApi.changeTrackSolo([track], false);
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
          if (typeof alphaApi.changeTrackVolume === "function") {
            alphaApi.changeTrackVolume([track], v / 100);
          }
        } catch (err) {
          console.warn("Track volume unsupported:", err);
        }
      });
    });
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
      alphaApi.settings.display.layoutMode = layoutMap[uiState.layout] || alphaTab.LayoutMode.Page;
      alphaApi.settings.display.staveProfile = staveMap[uiState.staveProfile] || alphaTab.StaveProfile.Default;
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
      if (playBtn) playBtn.disabled = false;
      if (stopBtn) stopBtn.disabled = false;
      if (playerProgressEl) playerProgressEl.textContent = "Ready";
    });

    alphaApi.playerStateChanged.on(function(e) {
      if (!playBtn || !e) return;
      const isPlaying = e.state === alphaTab.synth.PlayerState.Playing;
      playBtn.textContent = isPlaying ? "Pause" : "Play";
    });

    alphaApi.playerPositionChanged.on(function(e) {
      if (!songPositionEl || !e) return;
      const now = formatTime(e.currentTime);
      const end = formatTime(e.endTime);
      songPositionEl.textContent = now + " / " + end;
    });
  }

  function createAlphaTab(item) {
    if (alphaApi) {
      try {
        alphaApi.stop();
      } catch (err) {
        console.warn("stop unsupported:", err);
      }
    }
    viewerContainer.innerHTML = "";
    currentScore = null;
    if (playBtn) playBtn.disabled = true;
    if (stopBtn) stopBtn.disabled = true;
    if (playerProgressEl) playerProgressEl.textContent = "Loading 0%";
    if (songPositionEl) songPositionEl.textContent = "00:00 / 00:00";

    const viewportEl = document.querySelector(".at-viewport");

    const settings = {
      file: item.file,
      display: {
        staveProfile: "tab",
        layoutMode: "page",        // default to vertical page layout
        autoScroll: true,          // follow playback
        autoScrollSmooth: true,    // smooth scrolling
        autoScrollOffset: 0.3      // keep cursor ~30% from top
      },
      player: {
        enablePlayer: true,
        soundFont: "https://cdn.jsdelivr.net/npm/@coderline/alphatab@latest/dist/soundfont/sonivox.sf2",
        scrollElement: viewportEl  // scroll the viewport, not the whole window
      }
    };

    alphaApi = new alphaTab.AlphaTabApi(viewerContainer, settings);
    applyDisplaySettings();
    applyPlaybackSettings();
    wirePlayerEvents();

    alphaApi.scoreLoaded.on(function(score) {
      currentScore = score;
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
  }

  function loadTab(item) {
    currentTabItem = item;
    currentTitleEl.textContent = item.title;
    if (songTitleEl) songTitleEl.textContent = item.title || "Loading...";
    if (songArtistEl) songArtistEl.textContent = "Loading...";
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
