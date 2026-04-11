"""
WSGI config for communisante project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Use prod on Railway even when RAILWAY_ENVIRONMENT is missing (some projects only set DATABASE_URL / PORT).
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    _on_railway = bool(
        os.environ.get('RAILWAY_ENVIRONMENT')
        or os.environ.get('RAILWAY_PROJECT_ID')
        or os.environ.get('RAILWAY_SERVICE_ID')
    )
    if _on_railway:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'communisante.settings.prod'
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'communisante.settings')

application = get_wsgi_application()
