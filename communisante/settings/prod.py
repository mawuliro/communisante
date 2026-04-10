"""
Production settings for CommuniSanté.
Uses PostgreSQL, security enabled.
"""

import os

import environ
from .base import *

# Initialize environment variables
env = environ.Env()

# Read .env file if it exists (Railway uses environment variables directly)
environ.Env.read_env(BASE_DIR / '.env')

# Override for production
DEBUG = False

# Security settings
SECRET_KEY = env('SECRET_KEY')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['.railway.app', '.up.railway.app'])

# HTTPS POST (login, forms) behind Railway TLS
_csrf = list(env.list('CSRF_TRUSTED_ORIGINS', default=[]))
_railway_public = os.environ.get('RAILWAY_PUBLIC_DOMAIN', '').strip()
if _railway_public:
    _origin = f'https://{_railway_public}'
    if _origin not in _csrf:
        _csrf.append(_origin)
CSRF_TRUSTED_ORIGINS = _csrf

# Railway (and similar) terminate TLS; the app sees HTTP unless we trust the proxy.
# Without this, SECURE_SSL_REDIRECT loops forever (browser HTTPS → edge → app HTTP → redirect to HTTPS).
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# Database - PostgreSQL (from Railway's DATABASE_URL)
DATABASES = {
    'default': env.db(),
}

# Security middleware enhancements
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Static files - WhiteNoise handles them
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Email (configure for production - use SendGrid or similar)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.sendgrid.net')
EMAIL_PORT = env('EMAIL_PORT', default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='apikey')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')

# Africa's Talking SMS
AFRICASTALKING_USERNAME = env('AFRICASTALKING_USERNAME', default='')
AFRICASTALKING_API_KEY = env('AFRICASTALKING_API_KEY', default='')

# Sentry error tracking
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

if env('SENTRY_DSN', default=None):
    sentry_sdk.init(
        dsn=env('SENTRY_DSN'),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
    )

# CORS - restrict to your app origin (merge Railway public URL when present)
_cors = list(
    env.list(
        'CORS_ALLOWED_ORIGINS',
        default=[],
    )
)
if _railway_public:
    _cors_origin = f'https://{_railway_public}'
    if _cors_origin not in _cors:
        _cors.append(_cors_origin)
CORS_ALLOWED_ORIGINS = _cors

# LocMem avoids running createcachetable on a fresh Postgres (swap for Redis later)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'communisante-prod',
    }
}