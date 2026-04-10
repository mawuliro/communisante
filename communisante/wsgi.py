"""
WSGI config for communisante project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Railway sets RAILWAY_ENVIRONMENT; use production settings unless overridden.
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        os.environ['DJANGO_SETTINGS_MODULE'] = 'communisante.settings.prod'
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'communisante.settings')

application = get_wsgi_application()
