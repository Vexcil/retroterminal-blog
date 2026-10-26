# Recipe short links

The recipe collection is published at `https://retroterminal.net/recipes/`.
`https://rtro.cc/recipes` and `https://rtro.cc/r` both redirect there.

Every recipe uses `https://rtro.cc/r/<slug>` for its Copy link button. The
shared include removes hyphens and underscores from the Jekyll document slug;
for example, `_recipes/boiled-cookies.md` uses `r/boiledcookies`. An explicit
`short_slug` in recipe front matter can preserve a link when renaming a file.

`recipe-shortlinks.json` records the current shortener destinations. When adding
or renaming recipes, register or update the corresponding link in the existing
rtro.cc admin interface as part of publication, and keep this manifest current.
Do not overwrite an unrelated existing short code.

The shortener runs on vex-dao at `/home/vex/rtro-shortener/app.py`, managed by
the user service `rtro-shortener.service`. It accepts existing single-part
codes and recipe codes prefixed with `r/`. Its supported admin create/update
operations also work through its loopback endpoint at port 18766. Back up
the application and SQLite database with the SQLite backup API before changes.

The recipe sharing assets load only on recipe documents. When clipboard access
is unavailable, the button reveals and selects the same short URL for manual
copying. Recipe pages retain their `noindex, nofollow` metadata.
