"""
Rule-based triage: sum symptom weights, match first overlapping score band on the protocol.
"""

from __future__ import annotations

from django.db.models import Prefetch, QuerySet
from django.utils.translation import gettext as _

from triage.models import Symptom, SymptomProtocol, TriageRule


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
