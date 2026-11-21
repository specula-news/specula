# SPECULA — AI-Powered Global News Aggregator

![Version](https://img.shields.io/badge/version-23.0.0-f6a93b)
![Python](https://img.shields.io/badge/backend-python-blue)
![Frontend](https://img.shields.io/badge/frontend-HTML%2FJS-orange)
![License](https://img.shields.io/badge/license-MIT-green)

**SPECULA** is a fully automated news aggregator. Every four hours a GitHub Action fetches
70+ RSS feeds and YouTube channels and publishes the result on GitHub. The website at
<https://specula-news.netlify.app> is a static page on Netlify that loads that data straight from GitHub.

Topics: Geopolitics · Tech · EV · Energy · Science · Economy · Construction · Gaming · news-channel video · YouTubers.

---

## ⚙️ How it works (v23)

```
            every 4 h                                   loads at runtime
 GitHub Actions ──────────▶ `data` branch on GitHub ◀──────────────────── visitor's browser
 (generator.py)             news.json · meta.json ·                          ▲
                            status.json                                      │ static files, only
                                                                             │ redeployed when site/ changes
                            `main` branch ── site/ ─────────────▶ Netlify ───┘
```

- **All updates happen on GitHub.** The *Update News* workflow writes `news.json`, `meta.json` and
  `status.json` to the **`data` branch** (one commit, force-pushed, so the repo never grows).
  It never commits to `main`.
- **Netlify only hosts the static site** in `site/`. `netlify.toml` tells Netlify to skip any commit
  that doesn't change `site/`, so news updates, `sources.py` edits and the daily backup cost **zero
  deploys**. (On Netlify's credit plans each production deploy costs 15 of the 300 free monthly credits —
  the old setup deployed 6–7 times a day.)
- **The page fetches the news from GitHub** — `raw.githubusercontent.com` first, with **jsDelivr** as an
  automatic backup (the workflow refreshes jsDelivr's cache after every run). The service worker keeps the
  last copy for offline use.
- The data location is one line in `site/index.html`:
  ```html
  <meta name="specula-data" content="specula-news/specula@data">
  ```
  Change it if your GitHub user or repo name is different. **The repository must be public**
  (raw.githubusercontent.com and jsDelivr can't read private repos).

---

## ✨ Features

### The news site (`site/index.html`)
- **Ember look** (warm near-black, amber, coral & green; Fraunces + Manrope) with dark & light modes — the V22
  cyan look is still one click away as **Classic** (pill at the top, Preferences, or press <kbd>c</kbd>).
- **Sidebar navigation** with icons and new-story counts (horizontal category pills on phones).
- Lead story + “Just in” panel, video rail, **Articles / Videos tabs with counts**, filter chips, Mixed / Newest sort.
- **Grid or list layout** — the list view shows each story as a row with a freshness bar and Save / Share / Hide.
- **Search** (press <kbd>/</kbd>), built-in video player, **Read Later** that survives feed updates, hide sources.
- **New since your last visit** badges, read-state, shareable URLs, keyboard shortcuts (<kbd>?</kbd>).
- **PWA**: installable, works offline with the last downloaded feed, “Fresh stories are in” refreshes in place.

### The generator (`generator.py`)
- RSS/Atom + YouTube (channel RSS for exact publish times, `yt-dlp` as fallback). Shorts are skipped.
- Image finding: feed media → enclosure → inline image → article page (OpenGraph, Twitter card, JSON-LD, …), or a fixed method per source.
- **Cache**: images, translations and YouTube channel IDs are reused from the previous run (read from the `data` branch).
- **Swedish headlines translated** to English (original kept and shown on hover).
- **Resilient**: if a source fails, its previous stories stay up; if everything fails, nothing is published.
- Writes a **health report** (`status.json`) that the admin panel uses to show which sources work.

### The admin panel (`site/admin.html`)
- Sign in with a GitHub token; edit everything in `sources.py` without touching code.
- Health per source, add source with RSS discovery, feed test, image finder, pause, move between folders.
- **Run update** starts the GitHub Action and follows it until it's done.
- Edit or upload repo files. Saving a file in `site/` triggers one Netlify deploy; anything else doesn't.

---

## 📁 Files

| Path | What it is |
|---|---|
| `site/` | **The website — the only folder Netlify publishes.** |
| `site/index.html` | The whole site (design + code). Edit this directly — there is no build step any more. |
| `site/admin.html` | Admin panel (not indexed by search engines). |
| `site/service-worker.js` | Offline support / PWA (also caches the GitHub data). |
| `site/manifest.json`, icons, `og-image.jpg` | App & browser icons, social preview image. |
| `site/robots.txt`, `site/sitemap.xml`, `site/google…html`, `site/404.html` | Search engines and the “not found” page. |
| `generator.py` | Fetches all sources and writes the data files (`--out data`). |
| `sources.py` | The list of sources (edited by hand or from the admin panel). |
| `debug_logic.py` | Image-detection diagnostics for one URL (run via the “Debug URL Logic” Action). |
| `netlify.toml` | Publish `site/`, skip deploys when `site/` didn't change. |
| `.github/workflows/` | `main.yml` (update every 4 h → `data` branch), `daily_full_backup.yml`, `cleanup.yml`, `debug_url.yml`. |
| **`data` branch** | `news.json`, `meta.json`, `status.json` — written by the workflow, don't edit. |

---

## 🚚 Switching an existing v22 repo to v23 (one time)

1. Replace the repo contents with this version (keep `.git`). With git:
   ```bash
   git clone https://github.com/specula-news/specula.git && cd specula
   git rm -r -q .                    # remove the old files from the index
   # copy the new files in here (unzip), then:
   git add -A && git commit -m "v23: static site on Netlify, news data on GitHub" && git push
   ```
   The old root files (`index.html`, `template.html`, `news.json`, `status.json`, `admin.html`, …) must be gone
   from the repo root — they now live in `site/` or on the `data` branch.
2. Check the `<meta name="specula-data" …>` line in `site/index.html` matches your `owner/repo`.
3. GitHub → **Actions → Update News → Run workflow**. This creates the `data` branch
   (the first run takes a bit longer because the image cache starts empty).
4. Netlify deploys once for this push (because `site/` changed). Nothing to change in the Netlify UI —
   `netlify.toml` sets the publish folder. If you once set a *Publish directory* or *Build command* in the UI,
   the file overrides it.
5. Open the site. From now on news updates arrive without any Netlify deploys.

---

## 🛠️ Run locally
```bash
pip install -r requirements.txt
python generator.py                  # full run → data/news.json, data/meta.json, data/status.json
python -m http.server 8000           # then open http://localhost:8000/site/?data=/data/
```
`?data=` only works on localhost; the real site always reads from GitHub.

```bash
python generator.py --only Electrek Feber   # test some sources, writes nothing
python generator.py --no-scrape             # faster: never download article pages for images
```

### Admin panel token
1. GitHub → **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**.
2. Repository access: **Only select repositories → specula**.
3. Permissions: **Contents: Read and write** and **Actions: Read and write**.
4. Open `/admin.html` on the site, paste the token. Untick “Remember on this device” on shared computers.

### Source fields (`sources.py`)
```python
{"url": "https://electrek.co/feed/", "source_name": "Electrek", "cat": "ev", "type": "web", "lang": "en"}
```
`cat`: geopolitics, tech, ev, energy, science, economy, construction, gaming, youtubers ·
`type`: web or video · `lang`: en or sv (sv headlines are translated) ·
optional: `filter_tag` (global, eu, sweden, china, india / geo, tech, energy, ev, gaming),
`image_strategy`, `channel_id`, `disabled: true`.

---

## 🧯 Troubleshooting
- **Site says “Feed unavailable”** — the `data` branch doesn't exist yet (run *Update News* once), the repo is
  private, or the `specula-data` meta tag points at the wrong `owner/repo`.
- **New stories take a few minutes to show** — GitHub's raw file CDN caches for ~5 minutes. That's normal.
- **A source shows “Error” in the admin panel** — open *Test*. “Not an RSS/Atom feed” means the URL is a web page:
  delete it and re-add the homepage with *Add source* to find the real feed.
- **Wrong or missing pictures for a source** — use *Images* on its card, pick the method that shows the right
  picture, then *Save* and *Run update*.
- **Netlify deployed when it shouldn't have** — check that `netlify.toml` is in the repo root; the deploy log shows
  “ignore command returned exit code 0” for skipped commits.

---

## 📜 Changelog
See **System history** in the site footer (click the version number).
