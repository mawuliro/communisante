(function () {
  'use strict';

  var DB_NAME = 'communisante-offline';
  var DB_VERSION = 1;
  var STORE = 'outbox';

  function getConfig() {
    return window.COMMUNISANTE_PWA || {};
  }

  function getCookie(name) {
    var match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? decodeURIComponent(match[2]) : '';
  }

  function openDb() {
    return new Promise(function (resolve, reject) {
      var req = indexedDB.open(DB_NAME, DB_VERSION);
      req.onerror = function () {
        reject(req.error);
      };
      req.onsuccess = function () {
        resolve(req.result);
      };
      req.onupgradeneeded = function (e) {
        var db = e.target.result;
        if (!db.objectStoreNames.contains(STORE)) {
          db.createObjectStore(STORE, { keyPath: 'id' });
        }
      };
    });
  }

  function readAll(db) {
    return new Promise(function (resolve, reject) {
      var tx = db.transaction(STORE, 'readonly');
      var store = tx.objectStore(STORE);
      var req = store.getAll();
      req.onerror = function () {
        reject(req.error);
      };
      req.onsuccess = function () {
        resolve(req.result || []);
      };
    });
  }

  function removeIds(db, ids) {
    return new Promise(function (resolve, reject) {
      var tx = db.transaction(STORE, 'readwrite');
      var store = tx.objectStore(STORE);
      ids.forEach(function (id) {
        store.delete(id);
      });
      tx.oncomplete = function () {
        resolve();
      };
      tx.onerror = function () {
        reject(tx.error);
      };
    });
  }

  function buildPayload(form, kind) {
    if (kind === 'patient_create') {
      var fd = new FormData(form);
      var payload = {};
      fd.forEach(function (v, k) {
        if (k === 'csrfmiddlewaretoken') return;
        payload[k] = v;
      });
      return { kind: kind, payload: payload };
    }
    if (kind === 'patient_update') {
      var pk = form.getAttribute('data-offline-patient-pk');
      var fd2 = new FormData(form);
      var p2 = { patient_pk: pk };
      fd2.forEach(function (v, k) {
        if (k === 'csrfmiddlewaretoken') return;
        p2[k] = v;
      });
      return { kind: kind, payload: p2 };
    }
    if (kind === 'triage_session') {
      var protocolPk = parseInt(form.getAttribute('data-offline-protocol-pk'), 10);
      var patientPk = parseInt(form.getAttribute('data-offline-patient-pk'), 10);
      var boxes = form.querySelectorAll('input[name="symptom"]:checked');
      var symptomIds = [];
      for (var i = 0; i < boxes.length; i++) {
        var n = parseInt(boxes[i].value, 10);
        if (!isNaN(n)) symptomIds.push(n);
      }
      return {
        kind: kind,
        payload: {
          protocol_pk: protocolPk,
          patient_pk: patientPk,
          symptom_ids: symptomIds,
        },
      };
    }
    return null;
  }

  function enqueue(item) {
    item.id = item.id || (crypto.randomUUID && crypto.randomUUID()) || String(Date.now()) + Math.random();
    item.createdAt = Date.now();
    return openDb().then(function (db) {
      return new Promise(function (resolve, reject) {
        var tx = db.transaction(STORE, 'readwrite');
        tx.objectStore(STORE).put(item);
        tx.oncomplete = function () {
          resolve(item.id);
        };
        tx.onerror = function () {
          reject(tx.error);
        };
      });
    });
  }

  function setBanner(online) {
    var el = document.getElementById('offline-banner');
    if (!el) return;
    el.hidden = online;
    el.setAttribute('aria-hidden', online ? 'true' : 'false');
  }

  function updatePendingBadge(count) {
    var badge = document.getElementById('offline-pending-count');
    if (!badge) return;
    if (count > 0) {
      badge.hidden = false;
      badge.textContent = String(count);
    } else {
      badge.hidden = true;
    }
  }

  function refreshPendingCount() {
    openDb()
      .then(readAll)
      .then(function (items) {
        updatePendingBadge(items.length);
      })
      .catch(function () {});
  }

  function flushQueue() {
    var cfg = getConfig();
    if (!cfg.syncUrl || !navigator.onLine) return Promise.resolve();

    var db;
    return openDb()
      .then(function (d) {
        db = d;
        return readAll(db);
      })
      .then(function (items) {
        if (!items.length) return null;
        var headers = {
          'Content-Type': 'application/json',
          'X-CSRFToken': cfg.csrfToken || getCookie('csrftoken') || '',
        };
        return fetch(cfg.syncUrl, {
          method: 'POST',
          credentials: 'same-origin',
          headers: headers,
          body: JSON.stringify({ items: items }),
        }).then(function (res) {
          return res.text().then(function (text) {
            var body = {};
            try {
              body = JSON.parse(text);
            } catch (e) {}
            return { res: res, body: body };
          });
        });
      })
      .then(function (result) {
        if (!result || !result.body) return;
        var body = result.body;
        var results = body.results || [];
        var toRemove = [];
        for (var i = 0; i < results.length; i++) {
          var r = results[i];
          if (r.ok && r.client_id) toRemove.push(r.client_id);
        }
        if (toRemove.length) {
          return removeIds(db, toRemove).then(function () {
            refreshPendingCount();
            if (typeof window.dispatchEvent === 'function') {
              window.dispatchEvent(new CustomEvent('communisante:synced'));
            }
          });
        }
        refreshPendingCount();
      })
      .catch(function () {});
  }

  document.addEventListener(
    'submit',
    function (e) {
      var form = e.target;
      if (!(form instanceof HTMLFormElement)) return;
      if (form.method.toLowerCase() !== 'post') return;
      var kind = form.getAttribute('data-offline-kind');
      if (!kind) return;
      if (navigator.onLine) return;

      e.preventDefault();
      e.stopPropagation();

      var item = buildPayload(form, kind);
      if (!item) return;

      enqueue(item)
        .then(function () {
          refreshPendingCount();
          var msgEl = document.getElementById('offline-queued-toast');
          if (msgEl) {
            msgEl.hidden = false;
            setTimeout(function () {
              msgEl.hidden = true;
            }, 4000);
          }
          if (kind === 'triage_session') {
            var boxes = form.querySelectorAll('input[name="symptom"]');
            for (var i = 0; i < boxes.length; i++) boxes[i].checked = false;
          }
        })
        .catch(function () {});
    },
    true
  );

  window.addEventListener('online', function () {
    setBanner(true);
    flushQueue();
  });
  window.addEventListener('offline', function () {
    setBanner(false);
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  function init() {
    setBanner(navigator.onLine);
    refreshPendingCount();
    flushQueue();

    var cfg = getConfig();
    if (cfg.serviceWorkerUrl && 'serviceWorker' in navigator) {
      navigator.serviceWorker.register(cfg.serviceWorkerUrl).catch(function () {});
    }
  }
})();
