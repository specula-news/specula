/* SPECULA service worker
 * - The page (index.html): network first, last cached copy as an offline fallback.
 * - News data (news.json / meta.json on raw.githubusercontent.com or cdn.jsdelivr.net):
 *   network first, last downloaded copy when offline — so the app still opens on a plane.
 * - Static files (icons, manifest): cache first.
 * - Everything else from other sites (article images, fonts, YouTube) goes straight to the network.
 * Bump VERSION when you change this file so old caches are cleared.
 */
const VERSION = 'specula-v23.0.0';
const CORE = ['./', 'index.html', 'manifest.json', 'favicon.svg', 'favicon.png', 'icon.png', 'apple-touch-icon.png'];
const SKIP = /\/(admin\.html)$/;
const DATA_HOSTS = /^(raw\.githubusercontent\.com|cdn\.jsdelivr\.net)$/;

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => c.addAll(CORE)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

function networkFirst(req, key, fallback) {
  return fetch(req)
    .then((res) => {
      if (res.ok) { const copy = res.clone(); caches.open(VERSION).then((c) => c.put(key, copy)); }
      return res;
    })
    .catch(() => caches.match(key)
      .then((hit) => hit || (fallback && caches.match(fallback)))
      .then((hit) => hit || Response.error()));
}

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  const key = url.origin + url.pathname; // ignore ?c=tech etc. so the cache stays small

  // News data on GitHub / jsDelivr
  if (DATA_HOSTS.test(url.hostname)) {
    if (/\/(news|meta)\.json$/.test(url.pathname)) e.respondWith(networkFirst(req, key));
    return;
  }

  if (url.origin !== self.location.origin || SKIP.test(url.pathname)) return;

  const isFresh = req.mode === 'navigate' || /\/$|\.html$|\.json$/.test(url.pathname);
  if (isFresh) { e.respondWith(networkFirst(req, key, 'index.html')); return; }

  e.respondWith(
    caches.match(key).then((hit) => hit || fetch(req).then((res) => {
      if (res.ok) { const copy = res.clone(); caches.open(VERSION).then((c) => c.put(key, copy)); }
      return res;
    }))
  );
});
