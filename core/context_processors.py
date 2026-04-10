"""
Context processors for CommuniSanté.
Adds site-wide variables to all templates.
"""

from django.conf import settings


def site_settings(request):
    """
    Add site-wide settings to template context.
    """
    return {
        'SITE_NAME': 'CommuniSanté',
        'DEBUG': settings.DEBUG,
    }