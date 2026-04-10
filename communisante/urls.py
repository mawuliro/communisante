"""
URL configuration for CommuniSanté project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

from core.views import health

urlpatterns = [
    path('health/', health, name='health'),
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
]

# Add app URLs within i18n_patterns for language support
urlpatterns += i18n_patterns(
    path('accounts/', include('accounts.urls')),
    path('patients/', include('patients.urls')),
    path('triage/', include('triage.urls')),
    path('maternal/', include('maternal.urls')),
    path('alerts/', include('alerts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('api/', include('api.urls')),
    path('', include('core.urls')),  # Home page
)

# Development-only URLs
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)