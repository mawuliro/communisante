"""Small views that must stay outside translated URL prefixes."""

from django.http import HttpResponse


def health(request):
    """Plain 200 for load balancers (Railway, etc.)."""
    return HttpResponse('ok', content_type='text/plain')
