"""Small views that must stay outside translated URL prefixes."""

import json

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.urls import reverse
from django.utils import translation
from django.views.decorators.http import require_GET


def _precache_urls(request):
    """Absolute URLs for install-time caching (all UI languages + static shell)."""
    route_names = [
        'core:home',
        'accounts:login',
        'dashboard:home',
        'patients:list',
        'patients:create',
        'alerts:list',
        'triage:protocol_list',
        'maternal:pregnancy_list',
    ]
    urls = []
    for rel in (
        static('offline.html'),
        static('js/communisante-pwa.js'),
        static('pwa/icon-192.png'),
        static('pwa/icon-512.png'),
    ):
        urls.append(request.build_absolute_uri(rel))
    for lang_code, _ in settings.LANGUAGES:
        with translation.override(lang_code):
            for name in route_names:
                try:
                    urls.append(request.build_absolute_uri(reverse(name)))
                except Exception:
                    pass
    seen = set()
    ordered = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            ordered.append(u)
    return ordered


@require_GET
def health(request):
    """Plain 200 for load balancers (Railway, etc.). Keep minimal — no DB, no template."""
    return HttpResponse('ok', content_type='text/plain')


@require_GET
def web_manifest(request):
    """PWA manifest (install, theme, icons). Served at root so scope covers the whole app."""
    icon_192 = request.build_absolute_uri(static('pwa/icon-192.png'))
    icon_512 = request.build_absolute_uri(static('pwa/icon-512.png'))
    with translation.override(settings.LANGUAGE_CODE):
        start_path = reverse('core:home')
    start_url = request.build_absolute_uri(start_path)
    payload = {
        'name': 'CommuniSanté',
        'short_name': 'CommuniSanté',
        'description': 'Plateforme de santé communautaire — consultation partielle hors ligne.',
        'start_url': start_url,
        'scope': '/',
        'display': 'standalone',
        'orientation': 'portrait-primary',
        'background_color': '#f8fafc',
        'theme_color': '#047857',
        'lang': settings.LANGUAGE_CODE,
        'dir': 'ltr',
        'categories': ['health', 'medical', 'productivity'],
        'icons': [
            {
                'src': icon_192,
                'sizes': '192x192',
                'type': 'image/png',
                'purpose': 'any',
            },
            {
                'src': icon_512,
                'sizes': '512x512',
                'type': 'image/png',
                'purpose': 'any maskable',
            },
        ],
    }
    return HttpResponse(
        json.dumps(payload, ensure_ascii=False),
        content_type='application/manifest+json; charset=utf-8',
    )


@require_GET
def service_worker(request):
    """Network-first for HTML, precache shell + static; stale cache fallback when offline."""
    precache = _precache_urls(request)
    offline_path = static('offline.html')
    offline_url = request.build_absolute_uri(offline_path)
    body = render_to_string(
        'core/service_worker.js',
        {
            'cache_version': getattr(settings, 'PWA_CACHE_VERSION', '2'),
            'precache_json': json.dumps(precache),
            'offline_url_json': json.dumps(offline_url),
        },
    )
    return HttpResponse(
        body,
        content_type='application/javascript; charset=utf-8',
    )
