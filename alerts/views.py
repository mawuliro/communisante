"""
Alert list and resolution (web UI).
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import ListView

from alerts.access import alert_queryset_for_user, user_can_resolve_alert
from alerts.models import Alert


class AlertListView(LoginRequiredMixin, ListView):
    model = Alert
    template_name = 'alerts/alert_list.html'
    context_object_name = 'alerts'
    paginate_by = 25

    def get_queryset(self):
        qs = alert_queryset_for_user(self.request.user).order_by('-created_at')
        status = self.request.GET.get('status')
        if status == 'open':
            qs = qs.filter(resolved=False)
        elif status == 'done':
            qs = qs.filter(resolved=True)
        sev = self.request.GET.get('severity')
        if sev in {c[0] for c in Alert.Severity.choices}:
            qs = qs.filter(severity=sev)
        at = self.request.GET.get('type')
        if at in {c[0] for c in Alert.AlertType.choices}:
            qs = qs.filter(type=at)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filter_status'] = self.request.GET.get('status', '')
        ctx['filter_severity'] = self.request.GET.get('severity', '')
        ctx['filter_type'] = self.request.GET.get('type', '')
        ctx['severity_choices'] = Alert.Severity.choices
        ctx['type_choices'] = Alert.AlertType.choices
        return ctx


class AlertResolveView(LoginRequiredMixin, View):
    """POST only: mark one alert resolved."""

    http_method_names = ['post']

    def post(self, request, pk):
        alert = get_object_or_404(Alert, pk=pk)
        if not user_can_resolve_alert(request.user, alert):
            return HttpResponseForbidden(_('You cannot resolve this alert.'))

        if alert.resolved:
            messages.info(request, _('Already resolved.'))
            return redirect('alerts:list')

        notes = (request.POST.get('notes') or '').strip()
        alert.resolved = True
        alert.resolved_by = request.user
        alert.resolved_at = timezone.now()
        if notes:
            alert.notes = (alert.notes + '\n' if alert.notes else '') + notes
        alert.save(
            update_fields=['resolved', 'resolved_by', 'resolved_at', 'notes'],
        )
        messages.success(request, _('Alert marked resolved.'))
        return redirect('alerts:list')
