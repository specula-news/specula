self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open('specula-store').then((cache) => cache.addAll([
      '/',
      '/index.html',
      '/icon.png'
    ]))
  );
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((response) => response || fetch(e.request))
  );
});