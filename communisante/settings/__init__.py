"""
Django settings package.

By default (e.g. ``python manage.py runserver``) development settings are used.
Production should set ``DJANGO_SETTINGS_MODULE=communisante.settings.prod`` (Railway).
"""

from .dev import *  # noqa: F401, F403
