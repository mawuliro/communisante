'use strict';
const CACHE_NAME = 'communi-sante-v{{ cache_version }}';
const PRECACHE_URLS = {{ precache_json|safe }};
const OFFLINE_URL = {{ offline_url_json|safe }};

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then(function (cache) {
        return cache.addAll(PRECACHE_URLS);
      })
      .then(function () {
        return self.skipWaiting();
      })
      .catch(function () {
        return self.skipWaiting();
      })
  );
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches
      .keys()
      .then(function (keys) {
        return Promise.all(
          keys
            .filter(function (k) {
              return k !== CACHE_NAME;
            })
            .map(function (k) {
              return caches.delete(k);
            })
        );
      })
      .then(function () {
        return self.clients.claim();
      })
  );
});

self.addEventListener('fetch', function (event) {
  var req = event.request;
  if (req.method !== 'GET') {
    return;
  }
  var url;
  try {
    url = new URL(req.url);
  } catch (e) {
    return;
  }
  if (url.origin !== self.location.origin) {
    return;
  }

  var accept = req.headers.get('accept') || '';
  var isNavigate = req.mode === 'navigate' || accept.indexOf('text/html') !== -1;

  if (isNavigate) {
    event.respondWith(
      fetch(req)
        .then(function (res) {
          if (res.ok) {
            var copy = res.clone();
            caches.open(CACHE_NAME).then(function (cache) {
              cache.put(req, copy);
            });
          }
          return res;
        })
        .catch(function () {
          return caches.match(req).then(function (hit) {
            return hit || caches.match(OFFLINE_URL);
          });
        })
    );
    return;
  }

  event.respondWith(
    fetch(req).catch(function () {
      return caches.match(req);
    })
  );
});
