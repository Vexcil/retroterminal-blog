# Private tabs and YouTube sync

The existing archive stays on the tab host. All index, file, search, upload and Songsterr routes require a signed session or a configured trusted network. Missing access configuration fails closed. The static GitHub Pages player shell remains public.

Configuration is mounted at `/config/access.json`, selected by `TABS_ACCESS_CONFIG`, outside the repository. The original `username`, `salt`, and PBKDF2 `password_hash` retain the Guest account. Optional `users` entries provide additional accounts; Vex uses `algorithm: "bcrypt"` and the existing service password hash, copied privately without changing the password. Existing Guest sessions remain valid. Other fields include the random `session_key`, `home_ips`, `home_networks`, `trusted_proxies`, `tailnet_networks`, and exact `origins`. No credentials belong in the public site source. Sessions last 30 days. Only explicitly trusted proxies may supply X-Real-IP, and proxy requests never receive the tailnet bypass merely because the proxy has a tailnet address. POST requests check Origin when supplied.

Current service: Docker container `retroterminal-tabs-private` on the archive host, image `retroterminal-tabs:controls-20261103`, source `/home/vex/tabs-youtube-sync-code`. Port 4081 is bound only to the host's Tailscale IP. Archive and data are mounted read/write; the container filesystem is read-only. The public `retro-edge-caddy` gateway proxies this port and overwrites X-Real-IP with the client address. The previous Caddyfile is backed up at `/home/vex/retro-edge/Caddyfile.pre-tabs-20261101`. The original native port 4080 service remains available for rollback.

Tailnet entry: `https://vex-ser.adal-fort.ts.net:11443/viewer/`. Tailscale Serve proxies through loopback port 4082 and systemd service `retro-tabs-tailnet-forward` to the private archive service. The normal public player first checks its session, then tries the tailnet endpoint. Browsers that block the private-network probe can use the explicit tailnet entry link. Home access follows the configured public IP; update this configuration if the ISP changes it.

From the library choose **Import Songsterr**, paste a Songsterr arrangement link, then **Import tab**. The resulting GP file is added under `uploads`, indexed, and opened. The **YouTube** panel can search Songsterr or get references and bar timing from a pasted link. Timing imports require the same played-bar count, including repeat occurrences. Different arrangements stay disabled. Check timing by ear even when counts match. A video may be removed, region restricted or disallow embedding; use another recording or a manual URL.

Songsterr import appears before Upload. **Import / open tab** checks the source ID before any upstream fetch or conversion. It reuses existing imports and older saved Songsterr associations, returning `alreadyExists: true` and the existing file. A `songsterr_imports` table in the existing persistent SQLite database remembers future imports even without a YouTube video. A lock covers lookup and creation, so simultaneous retries produce one file. Different Songsterr IDs remain distinct even if their titles match.

The dock's Play button shares a frame with a sliding **Synth / YT** selector directly below it. Its selected side and accessible source status follow the actual player mode. YouTube becomes selectable after a compatible recording and the score playback timeline are ready. Closing sync settings or pressing Play does not pause YouTube or reopen settings. The same iframe remains mounted in a separate mini-player; narrow screens put it below the notation in a scrollable workspace, with space to clear the floating controls. Switching to Synth pauses the video and restores the original score timing.

Opening a tab first loads its saved settings. When none exist, an idle task starts after the actual score/MIDI playback timeline is ready. It searches Songsterr by exact normalized artist and song title (with filename fallback), checks at most three exact arrangements, and requires a compatible played-bar count. A unique full mix is preferred; ambiguous arrangements or recordings require a choice. Confident matches save through the existing server store. Saved timing and new matches appear in a small bottom-right notification, above the player dock. Only **Use YouTube** switches audio; the lookup never pauses synth, opens the panel, downloads a video, or initializes the YouTube iframe. Switching tabs aborts requests and discards late results; manual searches/edits take priority. Failed matches are cached in memory for ten minutes. Timing-point DOM rows are built only when their details section is open.

Manual timing supports an initial video offset plus the score's tempo map, or individual played-bar points. YouTube provides the audio in external mode; mixer, transpose, metronome and count-in apply to the synthesizer only. Returning to synth restores the score's original sync points. No YouTube audio is downloaded.

Video links, sync points and Songsterr source references save automatically per arrangement in `/home/vex/tabs-host/data/youtube-sync.sqlite3` (mounted as `/data/youtube-sync.sqlite3`). This database survives container upgrades. Authenticated GET/POST `/api/youtube-sync` uses the archive-relative file path, so public and tailnet URLs refer to the same record. Writes include a revision; stale, conflicting writes receive HTTP 409 and cannot replace newer timing. Identical retries are idempotent. Each device loads timing when opening the tab and refreshes it on window focus or opening the YouTube panel while synth mode is active. Playback is never interrupted by a background refresh.

Browser storage remains a draft/backup cache. Opening a previously saved tab migrates its original v1 browser timing only if there is no server record. A server record takes precedence over an older browser copy. Failed autosaves remain pending in the local cache and show a retry button; conflicting edits remain available for JSON export, with an explicit Load server version action. The panel shows when saving finishes. JSON export/import is still available for backups.

Songsterr metadata endpoints are unofficial and may change. The GP generator is vendored under its MIT license in `scripts/songsterr_vendor`. Import is user initiated and restricted to numeric song IDs; the server fetches fixed upstream endpoints, not arbitrary user URLs.

Checks: `npm --prefix tests ci && node --test tests/*.cjs`; install the Dockerfile's Python dependencies, then `python3.12 -m unittest discover -s tests -p 'test_*.py' -v`. The player-controls regression uses a deterministic YouTube adapter and verifies that closing settings retains the connected iframe and active external playback. Build with `docker build -f deploy/tabs.Dockerfile .`.

## GameTabs search (November 12)

The **Search tabs** panel includes Songsterr, GameTabs and My library sources.
GameTabs uses its public `/tabs?search=...` listing through an authenticated Tabs
server route; it does not expose library data or credentials to GameTabs. Results
link to the exact public arrangement. Requests are bounded and limited
to the GameTabs HTTPS host; user-supplied arbitrary URLs are not fetched.

GameTabs requires login to download Guitar Pro files. Without a connected local
session, results explicitly show **Sign-in needed** and imports fail closed.
After local CLI login, the Import button uses the server-side authenticated flow.
No passwords, cookies or Google tokens belong in repository or browser assets.
The local import path is regression tested; real server login/import must still
be checked after the owner connects their account.

Songsterr verification on November 12: public search returned Chrono Trigger
results; the existing conversion code received HTTP 403 at `/api/meta/63252`.
No alternate endpoint or identity was used to evade that rejection. Existing
library playback is unaffected; new Songsterr imports cannot be called verified.

### Durable GameTabs connection

GameTabs importing runs on vex-dao, not in the assistant's cloud browser.
A dedicated `/gametabs-session` volume holds only the authenticated session
(owner-only directory and file). It must never be placed under `/data`, `/tabs`,
or GitHub Pages. The container retains its existing restart policy, archive mounts,
read-only root filesystem and authentication requirements. Session persistence
survives service upgrades and boots, but upstream session expiry or revocation
requires another one-time login. Passwords are prompted invisibly by the local
CLI and are not retained. No remote connection-management endpoint is exposed.

Connect from vex-dao's terminal:
`docker exec -it retroterminal-tabs-private python3 scripts/gametabs_bridge.py login`

This connection serves the already-authorized private Tabs users. Never add
untrusted users without reconsidering the shared upstream account scope.
GameTabs files use the site's authenticated download preparation flow and its
countdown. Imported files pass the existing Guitar Pro validation and source-ID
deduplication before entering the archive. No cloud session cookies are exported.

### Top Tabs browsing and compact cards
Selecting GameTabs now loads its genuine Top Tabs ordering automatically. The
provider currently returns 50 Top Tabs and up to 30 keyword results without
upstream pagination; Tabs presents those available lists in 20-item local pages,
with a bounded five-minute cache to keep page order stable. It does not invent
rankings or claim access to more results than the provider returns. Blank search
returns to Top Tabs. Game/song titles link to their exact GameTabs arrangement;
**Load** imports or reopens the file in Tabs. Titles occupy a full card row and
actions sit below, avoiding narrow half-screen character-by-character wrapping.
