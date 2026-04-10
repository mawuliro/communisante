"""Who may view triage history."""

from django.db.models import QuerySet

from triage.models import SymptomCheck


def symptom_check_queryset_for_user(user) -> QuerySet[SymptomCheck]:
    if not user.is_authenticated:
        return SymptomCheck.objects.none()

    base = SymptomCheck.objects.select_related(
        'patient',
        'performed_by',
        'performed_by__user',
        'performed_by__district',
    ).prefetch_related('symptoms_selected')

    if user.is_superuser or getattr(user, 'is_admin_user', False):
        return base

    profile = getattr(user, 'health_worker_profile', None)
    if profile is not None:
        return base.filter(performed_by=profile)

    if getattr(user, 'is_supervisor', False):
        return base.filter(
            patient__assigned_chw__district__supervisor=user,
        ).distinct()

    return SymptomCheck.objects.none()
