const CACHE_NAME = 'stock-query-app-cache-v1';
const urlsToCache = [
  '/',
  '512.png',
  '128.png'
  // Add other assets that you want to cache for offline access
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});
