"""Alert visibility: CHW (own patients), supervisor (district), admin (all)."""

from django.db.models import QuerySet

from alerts.models import Alert


def alert_queryset_for_user(user) -> QuerySet[Alert]:
    if not user.is_authenticated:
        return Alert.objects.none()

    base = Alert.objects.select_related(
        'related_patient',
        'related_patient__assigned_chw',
        'related_patient__assigned_chw__district',
        'related_pregnancy',
        'resolved_by',
    )

    if user.is_superuser or getattr(user, 'is_admin_user', False):
        return base

    profile = getattr(user, 'health_worker_profile', None)
    if profile is not None:
        return base.filter(related_patient__assigned_chw=profile)

    if getattr(user, 'is_supervisor', False):
        return base.filter(
            related_patient__assigned_chw__district__supervisor=user,
        ).distinct()

    return Alert.objects.none()


def user_can_resolve_alert(user, alert: Alert) -> bool:
    """Same scope as viewing the alert."""
    return alert_queryset_for_user(user).filter(pk=alert.pk).exists()
