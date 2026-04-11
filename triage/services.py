"""
Rule-based triage: sum symptom weights, match first overlapping score band on the protocol.
"""

from __future__ import annotations

from django.db import transaction
from django.db.models import Prefetch, QuerySet
from django.utils.translation import gettext as _

from patients.access import health_worker_for_triage, patient_queryset_for_user
from triage.models import Symptom, SymptomCheck, SymptomProtocol, TriageRule


def active_symptoms_for_protocol(protocol: SymptomProtocol) -> QuerySet[Symptom]:
    return (
        Symptom.objects.filter(protocol=protocol, is_active=True)
        .order_by('category', 'name')
    )


def protocol_with_rules(protocol_id: int) -> SymptomProtocol | None:
    return (
        SymptomProtocol.objects.filter(pk=protocol_id, is_active=True)
        .prefetch_related(
            Prefetch(
                'triage_rules',
                queryset=TriageRule.objects.order_by('min_score'),
            ),
        )
        .first()
    )


def compute_score(symptoms: QuerySet[Symptom]) -> int:
    return sum(s.severity_weight for s in symptoms)


def resolve_rule(protocol: SymptomProtocol, score: int) -> TriageRule | None:
    rules = list(protocol.triage_rules.all())
    for rule in rules:
        if rule.min_score <= score <= rule.max_score:
            return rule
    return None


def run_triage(
    protocol: SymptomProtocol,
    symptom_ids: list[int],
) -> tuple[int, TriageRule | None, str | None]:
    """
    Returns (score, matched_rule_or_none, error_message_or_none).
    """
    allowed = set(
        active_symptoms_for_protocol(protocol).values_list('id', flat=True)
    )
    chosen = [pk for pk in symptom_ids if pk in allowed]
    symptoms = Symptom.objects.filter(pk__in=chosen, protocol=protocol)
    score = compute_score(symptoms)
    rule = resolve_rule(protocol, score)
    if rule is None:
        return score, None, _('No triage rule matches this score. Ask an administrator to review protocol bands.')
    return score, rule, None


def save_symptom_check_from_triage(
    user,
    protocol_pk: int,
    patient_pk: int,
    symptom_ids: list[int],
) -> tuple[SymptomCheck | None, str | None]:
    """
    Persist a triage session (same rules as TriageSessionView POST).
    Returns (SymptomCheck, None) on success or (None, error_message).
    """
    hw = health_worker_for_triage(user)
    if hw is None:
        return None, str(
            _(
                'Triage checks must be saved under a community health worker profile. '
                'Ask an administrator to link your account.'
            )
        )

    protocol = SymptomProtocol.objects.filter(pk=protocol_pk, is_active=True).first()
    if protocol is None:
        return None, str(_('Unknown or inactive protocol.'))

    patient = patient_queryset_for_user(user).filter(pk=patient_pk).first()
    if patient is None:
        return None, str(_('Patient not found or not accessible.'))

    proto_full = protocol_with_rules(protocol.pk)
    if proto_full is None:
        return None, str(_('Protocol configuration is incomplete.'))

    score, rule, err = run_triage(proto_full, symptom_ids)
    if err:
        return None, str(err)

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

    return check, None
