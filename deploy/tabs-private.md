# Private tabs and YouTube sync

The existing archive stays on the tab host. All index, file, search, upload and Songsterr routes require a signed session or a configured trusted network. Missing access configuration fails closed. The static GitHub Pages player shell remains public.

Configuration is mounted at `/config/access.json`, selected by `TABS_ACCESS_CONFIG`, outside the repository. Fields: `username`, random hex `salt`, `password_hash` (PBKDF2-HMAC-SHA256, 260000 iterations), random 32-byte hex `session_key`, `home_ips`, `home_networks`, `trusted_proxies`, `tailnet_networks`, and exact `origins`. No credentials belong in the public site source. Sessions last 30 days. Only explicitly trusted proxies may supply X-Real-IP, and proxy requests never receive the tailnet bypass merely because the proxy has a tailnet address. POST requests check Origin when supplied.

Current service: Docker container `retroterminal-tabs-private` on the archive host, image `retroterminal-tabs:youtube-20261101`, source `/home/vex/tabs-youtube-sync-code`. Port 4081 is bound only to the host's Tailscale IP. Archive and data are mounted read/write; the container filesystem is read-only. Public nginx proxies this port. Its previous configuration is backed up alongside the nginx site configuration. The original native port 4080 service remains available for rollback.

Tailnet entry: `https://vex-ser.adal-fort.ts.net:11443/viewer/`. Tailscale Serve proxies to the private archive service. The normal public player first checks its session, then tries the tailnet endpoint. Browsers that block the private-network probe can use the explicit tailnet entry link. Home access follows the configured public IP; update this configuration if the ISP changes it.

From the library choose **Import Songsterr**, paste a Songsterr arrangement link, then **Import tab**. The resulting GP file is added under `uploads`, indexed, and opened. The **YouTube** panel can search Songsterr or get references and bar timing from a pasted link. Timing imports require the same played-bar count, including repeat occurrences. Different arrangements stay disabled. Check timing by ear even when counts match. A video may be removed, region restricted or disallow embedding; use another recording or a manual URL.

Manual timing supports an initial video offset plus the score's tempo map, or individual played-bar points. YouTube provides the audio in external mode; mixer, transpose, metronome and count-in apply to the synthesizer only. Returning to synth restores the score's original sync points. Video and timing settings are saved per tab in browser storage; JSON export/import moves them between browsers. No YouTube audio is downloaded.

Songsterr metadata endpoints are unofficial and may change. The GP generator is vendored under its MIT license in `scripts/songsterr_vendor`. Import is user initiated and restricted to numeric song IDs; the server fetches fixed upstream endpoints, not arbitrary user URLs.

Checks: `node --test tests/test_sync_core.cjs`; `python3.12 -m unittest discover -s tests -p 'test_*access.py' -v`. Build with `docker build -f deploy/tabs.Dockerfile .`.
