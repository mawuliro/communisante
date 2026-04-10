"""
Triage protocol picker, symptom checklist, and saved check result.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import DetailView, ListView

from patients.access import health_worker_for_triage, patient_queryset_for_user
from patients.models import Patient
from triage.access import symptom_check_queryset_for_user
from triage.models import SymptomCheck, SymptomProtocol
from triage.services import (
    active_symptoms_for_protocol,
    protocol_with_rules,
    resolve_rule,
    run_triage,
)


class CanUseTriageUiMixin(UserPassesTestMixin):
    """Running a new check requires an active health worker profile."""

    def test_func(self):
        return health_worker_for_triage(self.request.user) is not None

    def handle_no_permission(self):
        messages.error(
            self.request,
            _('Triage checks must be saved under a community health worker profile. Ask an administrator to link your account.'),
        )
        return redirect('patients:list')


class ProtocolListView(LoginRequiredMixin, ListView):
    model = SymptomProtocol
    template_name = 'triage/protocol_list.html'
    context_object_name = 'protocols'

    def get_queryset(self):
        return SymptomProtocol.objects.filter(is_active=True).order_by('name', '-version')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['can_run_triage'] = health_worker_for_triage(self.request.user) is not None
        return ctx


class TriagePickPatientView(LoginRequiredMixin, ListView):
    """Pick which patient this protocol applies to before opening the checklist."""

    model = Patient
    template_name = 'triage/pick_patient.html'
    context_object_name = 'patients'
    paginate_by = 25

    def dispatch(self, request, *args, **kwargs):
        self.protocol = get_object_or_404(SymptomProtocol, pk=kwargs['protocol_pk'], is_active=True)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return patient_queryset_for_user(self.request.user).order_by('last_name', 'first_name')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['protocol'] = self.protocol
        ctx['can_run_triage'] = health_worker_for_triage(self.request.user) is not None
        return ctx


class TriageSessionView(LoginRequiredMixin, CanUseTriageUiMixin, View):
    """GET: show checklist. POST: score, save SymptomCheck, redirect to result."""

    template_name = 'triage/triage_session.html'

    def get(self, request, protocol_pk, patient_pk):
        protocol = get_object_or_404(SymptomProtocol, pk=protocol_pk, is_active=True)
        patient = get_object_or_404(patient_queryset_for_user(request.user), pk=patient_pk)
        symptoms = active_symptoms_for_protocol(protocol)
        grouped = {}
        for s in symptoms:
            key = s.category or _('General')
            grouped.setdefault(key, []).append(s)
        return self._render(request, protocol, patient, grouped, errors=None)

    def post(self, request, protocol_pk, patient_pk):
        protocol = get_object_or_404(SymptomProtocol, pk=protocol_pk, is_active=True)
        patient = get_object_or_404(patient_queryset_for_user(request.user), pk=patient_pk)
        hw = health_worker_for_triage(request.user)
        raw_ids = request.POST.getlist('symptom')
        try:
            symptom_ids = [int(x) for x in raw_ids if str(x).strip().isdigit()]
        except (TypeError, ValueError):
            symptom_ids = []

        proto_full = protocol_with_rules(protocol.pk)
        if proto_full is None:
            raise Http404

        score, rule, err = run_triage(proto_full, symptom_ids)
        symptoms = active_symptoms_for_protocol(protocol)
        grouped = {}
        for s in symptoms:
            key = s.category or _('General')
            grouped.setdefault(key, []).append(s)

        if err:
            messages.error(request, err)
            return self._render(request, protocol, patient, grouped, errors=[str(err)])

        with transaction.atomic():
            check = SymptomCheck.objects.create(
                patient=patient,
                score=score,
                recommendation_given=rule.recommendation,
                performed_by=hw,
            )
            check.symptoms_selected.set(
                Symptom.objects.filter(pk__in=symptom_ids, protocol=protocol)
            )

        messages.success(request, _('Triage saved.'))
        return redirect('triage:check_detail', pk=check.pk)

    def _render(self, request, protocol, patient, grouped, errors):
        from django.shortcuts import render

        return render(
            request,
            self.template_name,
            {
                'protocol': protocol,
                'patient': patient,
                'grouped_symptoms': grouped,
                'errors': errors or [],
            },
        )


class SymptomCheckDetailView(LoginRequiredMixin, DetailView):
    model = SymptomCheck
    template_name = 'triage/check_detail.html'
    context_object_name = 'check'

    def get_queryset(self):
        return symptom_check_queryset_for_user(self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        check = self.object
        resolved_rule = None
        first = check.symptoms_selected.first()
        if first is not None:
            loaded = protocol_with_rules(first.protocol_id)
            if loaded is not None:
                resolved_rule = resolve_rule(loaded, check.score)
        ctx['resolved_rule'] = resolved_rule
        return ctx
