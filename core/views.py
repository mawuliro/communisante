"""Small views that must stay outside translated URL prefixes."""

from django.http import HttpResponse
from django.views.decorators.http import require_GET


@require_GET
def health(request):
    """Plain 200 for load balancers (Railway, etc.). Keep minimal — no DB, no template."""
    return HttpResponse('ok', content_type='text/plain')
