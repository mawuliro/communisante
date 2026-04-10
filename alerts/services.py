"""
Create operational alerts from pregnancy and visit data (idempotent: one open alert per case).
"""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone

from alerts.models import Alert
from maternal.models import PregnancyRecord, PrenatalVisit


def _open_alert_exists(
    *,
    alert_type: str,
    pregnancy: PregnancyRecord | None,
    patient_id: int,
) -> bool:
    qs = Alert.objects.filter(
        type=alert_type,
        related_patient_id=patient_id,
        resolved=False,
    )
    if pregnancy is not None:
        qs = qs.filter(related_pregnancy_id=pregnancy.pk)
    else:
        qs = qs.filter(related_pregnancy__isnull=True)
    return qs.exists()


def generate_missed_visit_alerts() -> int:
    """
    Active pregnancies: overdue if no visit within MISSED_VISIT_THRESHOLD_DAYS of last visit,
    or no visit yet and LMP older than FIRST_ANC_OVERDUE_DAYS.
    Returns number of alerts created.
    """
    threshold = getattr(settings, 'MISSED_VISIT_THRESHOLD_DAYS', 14)
    first_contact_days = getattr(settings, 'FIRST_ANC_CONTACT_OVERDUE_DAYS', 56)
    today = timezone.localdate()
    created = 0

    qs = PregnancyRecord.objects.filter(is_active=True).select_related('patient').prefetch_related(
        Prefetch(
            'prenatal_visits',
            queryset=PrenatalVisit.objects.only('date'),
        ),
    )

    for pregnancy in qs:
        visit_dates = [v.date for v in pregnancy.prenatal_visits.all()]
        last_date = max(visit_dates) if visit_dates else None
        overdue = False
        if last_date is None:
            if pregnancy.last_menstrual_period and (today - pregnancy.last_menstrual_period).days > first_contact_days:
                overdue = True
        else:
            if (today - last_date).days > threshold:
                overdue = True

        if not overdue:
            continue

        if _open_alert_exists(
            alert_type=Alert.AlertType.MISSED_VISIT,
            pregnancy=pregnancy,
            patient_id=pregnancy.patient_id,
        ):
            continue

        with transaction.atomic():
            Alert.objects.create(
                type=Alert.AlertType.MISSED_VISIT,
                related_patient_id=pregnancy.patient_id,
                related_pregnancy=pregnancy,
                severity=Alert.Severity.MEDIUM,
                notes='',
            )
            created += 1

    return created


def generate_bp_danger_alerts() -> int:
    """Latest prenatal visit per active pregnancy: elevated BP triggers DANGER_SIGN."""
    sys_thr = getattr(settings, 'HIGH_RISK_BP_SYSTOLIC', 140)
    dia_thr = getattr(settings, 'HIGH_RISK_BP_DIASTOLIC', 90)
    created = 0

    for pregnancy in (
        PregnancyRecord.objects.filter(is_active=True)
        .select_related('patient')
        .iterator()
    ):
        latest = (
            pregnancy.prenatal_visits.order_by('-date', '-id')
            .only(
                'blood_pressure_systolic',
                'blood_pressure_diastolic',
            )
            .first()
        )
        if latest is None:
            continue
        sys_v = latest.blood_pressure_systolic
        dia_v = latest.blood_pressure_diastolic
        high = False
        if sys_v is not None and sys_v >= sys_thr:
            high = True
        if dia_v is not None and dia_v >= dia_thr:
            high = True
        if not high:
            continue

        if _open_alert_exists(
            alert_type=Alert.AlertType.DANGER_SIGN,
            pregnancy=pregnancy,
            patient_id=pregnancy.patient_id,
        ):
            continue

        with transaction.atomic():
            Alert.objects.create(
                type=Alert.AlertType.DANGER_SIGN,
                related_patient_id=pregnancy.patient_id,
                related_pregnancy=pregnancy,
                severity=Alert.Severity.HIGH,
                notes='',
            )
            created += 1

    return created


def generate_high_risk_pregnancy_alerts() -> int:
    """Active pregnancies flagged HIGH in the register."""
    created = 0
    for pregnancy in (
        PregnancyRecord.objects.filter(
            is_active=True,
            risk_level=PregnancyRecord.RiskLevel.HIGH,
        )
        .select_related('patient')
        .iterator()
    ):
        if _open_alert_exists(
            alert_type=Alert.AlertType.HIGH_RISK,
            pregnancy=pregnancy,
            patient_id=pregnancy.patient_id,
        ):
            continue

        with transaction.atomic():
            Alert.objects.create(
                type=Alert.AlertType.HIGH_RISK,
                related_patient_id=pregnancy.patient_id,
                related_pregnancy=pregnancy,
                severity=Alert.Severity.HIGH,
                notes='',
            )
            created += 1

    return created


def run_all_alert_generators() -> dict[str, int]:
    """Run generators in one batch. Returns counts per key."""
    return {
        'missed_visit': generate_missed_visit_alerts(),
        'bp_danger': generate_bp_danger_alerts(),
        'high_risk': generate_high_risk_pregnancy_alerts(),
    }
