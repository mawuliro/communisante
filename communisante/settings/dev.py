"""
Development settings for CommuniSanté.
Uses SQLite, debug tools enabled.
"""

from .base import *

# Override for development
DEBUG = True

# Broad hosts for local + LAN testing (phones on the same Wi‑Fi)
ALLOWED_HOSTS = ['*']

# SQLite is already configured in base.py - no changes needed

# Django Debug Toolbar (after SecurityMiddleware — required by the toolbar docs)
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE.insert(1, 'debug_toolbar.middleware.DebugToolbarMiddleware')
INTERNAL_IPS = ['127.0.0.1']

# Email to console (no actual emails sent)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Cache (dummy for development)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Logging for development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}