"""Small views that must stay outside translated URL prefixes."""

import json

from django.http import HttpResponse
from django.views.decorators.http import require_GET


@require_GET
def health(request):
    """Plain 200 for load balancers (Railway, etc.). Keep minimal — no DB, no template."""
    return HttpResponse('ok', content_type='text/plain')


@require_GET
def web_manifest(request):
    """PWA manifest at site root (scope /) so install prompts work."""
    payload = {
        'name': 'CommuniSanté',
        'short_name': 'CommuniSanté',
        'start_url': '/',
        'display': 'standalone',
        'background_color': '#f8fafc',
        'theme_color': '#047857',
        'lang': 'fr',
    }
    return HttpResponse(
        json.dumps(payload, ensure_ascii=False),
        content_type='application/manifest+json',
    )


@require_GET
def service_worker(request):
    """Minimal service worker at /sw.js (full app scope). v1: no caching rules yet."""
    body = (
        '// CommuniSanté — minimal SW; extend with cache lists for 2G/offline later.\n'
        "self.addEventListener('install', function (e) { self.skipWaiting(); });\n"
        "self.addEventListener('activate', function (e) { e.waitUntil(self.clients.claim()); });\n"
    )
    return HttpResponse(body, content_type='application/javascript')
