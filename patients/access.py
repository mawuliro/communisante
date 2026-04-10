"""
Who may see which patients (CHW, supervisor district scope, admin).
"""

from django.db.models import QuerySet

from accounts.models import HealthWorker
from patients.models import Patient


def patient_queryset_for_user(user) -> QuerySet[Patient]:
    """Return patients the user is allowed to view in the web app."""
    if not user.is_authenticated:
        return Patient.objects.none()

    base = Patient.objects.select_related(
        'assigned_chw',
        'assigned_chw__user',
        'assigned_chw__district',
    )

    if user.is_superuser or getattr(user, 'is_admin_user', False):
        return base

    profile = getattr(user, 'health_worker_profile', None)
    if profile is not None:
        return base.filter(assigned_chw=profile)

    if getattr(user, 'is_supervisor', False):
        return base.filter(assigned_chw__district__supervisor=user).distinct()

    return Patient.objects.none()


def user_can_manage_patients(user) -> bool:
    """True if the user may open patient create/update screens."""
    if not user.is_authenticated:
        return False
    if user.is_superuser or getattr(user, 'is_admin_user', False):
        return True
    if getattr(user, 'is_supervisor', False):
        return True
    profile = getattr(user, 'health_worker_profile', None)
    return profile is not None and profile.is_active


def health_worker_for_triage(user) -> HealthWorker | None:
    """Triage sessions are attributed to one CHW profile (active only)."""
    profile = getattr(user, 'health_worker_profile', None)
    if profile is None or not profile.is_active:
        return None
    return profile


def assignable_health_workers(user) -> QuerySet[HealthWorker]:
    """CHW choices for supervisors/admins when registering a patient."""
    qs = HealthWorker.objects.filter(is_active=True).select_related('user', 'district')
    if user.is_superuser or getattr(user, 'is_admin_user', False):
        return qs.order_by('district__name', 'user__last_name')
    if getattr(user, 'is_supervisor', False):
        return qs.filter(district__supervisor=user).order_by('user__last_name')
    return HealthWorker.objects.none()
