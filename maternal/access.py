"""
Pregnancy and visit visibility mirrors patient access (CHW, supervisor, admin).
"""

from django.db.models import QuerySet

from maternal.models import PregnancyRecord, PrenatalVisit
from patients.access import patient_queryset_for_user


def pregnancy_queryset_for_user(user) -> QuerySet[PregnancyRecord]:
    if not user.is_authenticated:
        return PregnancyRecord.objects.none()

    patient_ids = patient_queryset_for_user(user).values_list('pk', flat=True)
    return PregnancyRecord.objects.filter(patient_id__in=patient_ids).select_related(
        'patient',
        'patient__assigned_chw',
        'patient__assigned_chw__district',
    )


def prenatal_visit_queryset_for_user(user) -> QuerySet[PrenatalVisit]:
    if not user.is_authenticated:
        return PrenatalVisit.objects.none()

    preg_ids = pregnancy_queryset_for_user(user).values_list('pk', flat=True)
    return (
        PrenatalVisit.objects.filter(pregnancy_id__in=preg_ids)
        .select_related(
            'pregnancy',
            'pregnancy__patient',
            'recorded_by',
            'recorded_by__user',
        )
    )
