"""
Apply offline queue items from POST /sync/ (JSON) into PostgreSQL via forms and services.
"""

from __future__ import annotations

import json
from typing import Any

from django.contrib.auth import get_user_model
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from alerts.access import user_can_resolve_alert
from alerts.models import Alert
from maternal.access import pregnancy_queryset_for_user
from maternal.forms import PregnancyForm, PrenatalVisitForm
from patients.access import patient_queryset_for_user, user_can_manage_patients
from patients.forms import PatientForm
from triage.services import save_symptom_check_from_triage

User = get_user_model()


def _patient_create(user: User, payload: dict[str, Any]) -> dict[str, Any]:
    if not user_can_manage_patients(user):
        return {'ok': False, 'error': _('You do not have permission to register or edit patients.')}
    data = {k: v for k, v in payload.items() if k != 'kind'}
    form = PatientForm(data=data, user=user)
    if form.is_valid():
        patient = form.save()
        return {'ok': True, 'patient_id': patient.pk}
    return {'ok': False, 'error': _('Validation failed.'), 'field_errors': form.errors.get_json_data()}


def _patient_update(user: User, payload: dict[str, Any]) -> dict[str, Any]:
    if not user_can_manage_patients(user):
        return {'ok': False, 'error': _('You do not have permission to register or edit patients.')}
    pk = payload.get('patient_pk')
    if pk is None:
        return {'ok': False, 'error': _('Missing patient_pk.')}
    try:
        pk = int(pk)
    except (TypeError, ValueError):
        return {'ok': False, 'error': _('Invalid patient_pk.')}
    patient = patient_queryset_for_user(user).filter(pk=pk).first()
    if patient is None:
        return {'ok': False, 'error': _('Patient not found or not accessible.')}
    data = {k: v for k, v in payload.items() if k not in ('kind', 'patient_pk')}
    form = PatientForm(data=data, instance=patient, user=user)
    if form.is_valid():
        form.save()
        return {'ok': True, 'patient_id': patient.pk}
    return {'ok': False, 'error': _('Validation failed.'), 'field_errors': form.errors.get_json_data()}


def _pregnancy_create(user: User, payload: dict[str, Any]) -> dict[str, Any]:
    if not user_can_manage_patients(user):
        return {'ok': False, 'error': _('You do not have permission to add or change pregnancy records.')}
    data = {k: v for k, v in payload.items() if k != 'kind'}
    form = PregnancyForm(data=data, user=user)
    if form.is_valid():
        pregnancy = form.save()
        return {'ok': True, 'pregnancy_id': pregnancy.pk}
    return {'ok': False, 'error': _('Validation failed.'), 'field_errors': form.errors.get_json_data()}


def _pregnancy_update(user: User, payload: dict[str, Any]) -> dict[str, Any]:
    if not user_can_manage_patients(user):
        return {'ok': False, 'error': _('You do not have permission to add or change pregnancy records.')}
    pk = payload.get('pregnancy_pk')
    if pk is None:
        return {'ok': False, 'error': _('Missing pregnancy_pk.')}
    try:
        pk = int(pk)
    except (TypeError, ValueError):
        return {'ok': False, 'error': _('Invalid pregnancy_pk.')}
    pregnancy = pregnancy_queryset_for_user(user).filter(pk=pk).first()
    if pregnancy is None:
        return {'ok': False, 'error': _('Pregnancy not found or not accessible.')}
    data = {k: v for k, v in payload.items() if k not in ('kind', 'pregnancy_pk')}
    form = PregnancyForm(data=data, instance=pregnancy, user=user)
    if form.is_valid():
        form.save()
        return {'ok': True, 'pregnancy_id': pregnancy.pk}
    return {'ok': False, 'error': _('Validation failed.'), 'field_errors': form.errors.get_json_data()}


def _prenatal_visit_create(user: User, payload: dict[str, Any]) -> dict[str, Any]:
    if not user_can_manage_patients(user):
        return {'ok': False, 'error': _('You do not have permission to add or change pregnancy records.')}
    try:
        pregnancy_pk = int(payload['pregnancy_pk'])
    except (KeyError, TypeError, ValueError):
        return {'ok': False, 'error': _('Invalid pregnancy reference.')}
    pregnancy = pregnancy_queryset_for_user(user).filter(pk=pregnancy_pk).first()
    if pregnancy is None:
        return {'ok': False, 'error': _('Pregnancy not found or not accessible.')}
    data = {k: v for k, v in payload.items() if k not in ('kind', 'pregnancy_pk')}
    form = PrenatalVisitForm(data=data, user=user, pregnancy=pregnancy)
    if form.is_valid():
        visit = form.save(commit=False)
        visit.pregnancy = pregnancy
        visit.save()
        return {'ok': True, 'prenatal_visit_id': visit.pk}
    return {'ok': False, 'error': _('Validation failed.'), 'field_errors': form.errors.get_json_data()}


def _alert_resolve(user: User, payload: dict[str, Any]) -> dict[str, Any]:
    pk = payload.get('alert_pk')
    if pk is None:
        return {'ok': False, 'error': _('Missing alert_pk.')}
    try:
        pk = int(pk)
    except (TypeError, ValueError):
        return {'ok': False, 'error': _('Invalid alert_pk.')}
    alert = Alert.objects.filter(pk=pk).first()
    if alert is None:
        return {'ok': False, 'error': _('Alert not found.')}
    if not user_can_resolve_alert(user, alert):
        return {'ok': False, 'error': _('You cannot resolve this alert.')}
    if alert.resolved:
        return {'ok': True, 'alert_id': alert.pk, 'already_resolved': True}
    notes = (payload.get('notes') or '').strip()
    alert.resolved = True
    alert.resolved_by = user
    alert.resolved_at = timezone.now()
    if notes:
        alert.notes = (alert.notes + '\n' if alert.notes else '') + notes
    alert.save(update_fields=['resolved', 'resolved_by', 'resolved_at', 'notes'])
    return {'ok': True, 'alert_id': alert.pk}


def _triage_session(user: User, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        protocol_pk = int(payload['protocol_pk'])
        patient_pk = int(payload['patient_pk'])
    except (KeyError, TypeError, ValueError):
        return {'ok': False, 'error': _('Invalid protocol or patient.')}
    raw = payload.get('symptom_ids') or []
    try:
        symptom_ids = [int(x) for x in raw]
    except (TypeError, ValueError):
        return {'ok': False, 'error': _('Invalid symptom list.')}

    check, err = save_symptom_check_from_triage(user, protocol_pk, patient_pk, symptom_ids)
    if err:
        return {'ok': False, 'error': str(err)}
    return {'ok': True, 'symptom_check_id': check.pk}


def apply_offline_item(user: User, item: dict[str, Any]) -> dict[str, Any]:
    kind = item.get('kind')
    payload = item.get('payload')
    if not kind or not isinstance(payload, dict):
        return {'ok': False, 'error': _('Invalid item.')}
    if kind == 'patient_create':
        return _patient_create(user, payload)
    if kind == 'patient_update':
        return _patient_update(user, payload)
    if kind == 'triage_session':
        return _triage_session(user, payload)
    if kind == 'pregnancy_create':
        return _pregnancy_create(user, payload)
    if kind == 'pregnancy_update':
        return _pregnancy_update(user, payload)
    if kind == 'prenatal_visit_create':
        return _prenatal_visit_create(user, payload)
    if kind == 'alert_resolve':
        return _alert_resolve(user, payload)
    return {'ok': False, 'error': _('Unknown sync kind.')}


@require_POST
def offline_sync_view(request: HttpRequest) -> JsonResponse:
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'authentication_required'}, status=401)

    try:
        body = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'invalid_json'}, status=400)

    items = body.get('items')
    if not isinstance(items, list):
        return JsonResponse({'ok': False, 'error': 'items_required'}, status=400)

    results: list[dict[str, Any]] = []
    for raw in items:
        if not isinstance(raw, dict):
            results.append({'client_id': None, 'ok': False, 'error': _('Invalid item shape.')})
            continue
        client_id = raw.get('id')
        out = apply_offline_item(request.user, raw)
        out['client_id'] = client_id
        results.append(out)

    all_ok = all(r.get('ok') for r in results)
    return JsonResponse(
        {'ok': all_ok, 'results': results},
        encoder=DjangoJSONEncoder,
    )
