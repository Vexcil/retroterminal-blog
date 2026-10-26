# RetroTerminal recipe publishing

When adding or renaming a recipe in `_recipes/`, automatically include its
working shorthand URL in the same task. Read `deploy/RECIPES.md` for the current
deployment and shortener details.

- Generate `https://rtro.cc/r/<slug>` using the recipe filename without `.md`,
  hyphens, or underscores, matching `_includes/recipe-share.html`. For example,
  `boiled-cookies.md` becomes `https://rtro.cc/r/boiledcookies`. Use a unique,
  readable lowercase slug; the complete `r/<slug>` code must fit 64 characters.
- Check `deploy/recipe-shortlinks.json` and the live shortener for collisions.
  If needed, set an explicit `short_slug` in the recipe's front matter and use
  that same slug everywhere. Preserve existing shorthand URLs when renaming a
  recipe; update their destinations rather than breaking shared links.
- Register the redirect to the recipe's canonical
  `https://retroterminal.net/recipes/<filename>/` URL through the shortener's
  supported admin create/update operations. Take a SQLite backup first; never
  overwrite an unrelated link or edit the live database directly.
- Update `deploy/recipe-shortlinks.json` in the same change, preserving the
  existing recipe links and both collection aliases (`r` and `recipes`).
- Keep the shared upper-right Copy link button using that exact shorthand URL,
  including its clipboard-denied fallback. Preserve recipe privacy metadata.
- Before calling an authorized recipe publication complete, verify the live
  shorthand redirect, the destination's successful response, and the matching
  Copy link value. A generated URL or manifest entry alone is incomplete; if
  registration or verification fails, report the unfinished step explicitly.

Creating and verifying the matching short link is part of an authorized recipe
publication; do not leave it as an optional follow-up for the user.
