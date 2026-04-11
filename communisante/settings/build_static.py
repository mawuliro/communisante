"""
Minimal production-like settings for `collectstatic` only.

Railway’s build step often runs without DATABASE_URL / SECRET_KEY; loading full
`prod` then fails and static files never get collected (admin without CSS).
"""

import os

from .base import *

DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY', 'collectstatic-build-placeholder-not-for-runtime')
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

STORAGES = {
    **STORAGES,
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}
