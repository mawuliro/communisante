"""
Role-aware home dashboard: CHW summary vs supervisor or admin district view.
"""

from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic import TemplateView

from accounts.models import District, HealthWorker
from alerts.access import alert_queryset_for_user
from alerts.models import Alert
from maternal.models import PregnancyRecord
from patients.models import Patient


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx['dashboard_role'] = 'none'

        if user.is_superuser or getattr(user, 'is_admin_user', False):
            ctx['dashboard_role'] = 'admin'
            ctx.update(self._admin_stats())
            return ctx

        if getattr(user, 'is_supervisor', False):
            ctx['dashboard_role'] = 'supervisor'
            ctx.update(self._supervisor_stats(user))
            return ctx

        hw = getattr(user, 'health_worker_profile', None)
        if hw is not None and hw.is_active:
            ctx['dashboard_role'] = 'chw'
            ctx.update(self._chw_stats(hw))
            return ctx

        return ctx

    def _chw_stats(self, hw: HealthWorker):
        patients = Patient.objects.filter(assigned_chw=hw)
        open_alerts = alert_queryset_for_user(self.request.user).filter(resolved=False)
        active_preg = PregnancyRecord.objects.filter(
            patient__assigned_chw=hw,
            is_active=True,
        )
        since = timezone.now() - timedelta(days=7)
        recent_patients = patients.filter(created_at__gte=since).count()
        return {
            'hw': hw,
            'patient_count': patients.count(),
            'open_alert_count': open_alerts.count(),
            'active_pregnancy_count': active_preg.count(),
            'recent_patient_count': recent_patients,
        }

    def _supervisor_stats(self, user):
        districts = District.objects.filter(supervisor=user).order_by('name')
        district_ids = list(districts.values_list('pk', flat=True))
        chws = HealthWorker.objects.filter(district_id__in=district_ids, is_active=True)
        patients = Patient.objects.filter(assigned_chw__district_id__in=district_ids)
        open_alerts = alert_queryset_for_user(user).filter(resolved=False)
        active_preg = PregnancyRecord.objects.filter(
            patient__assigned_chw__district_id__in=district_ids,
            is_active=True,
        )
        since = timezone.now() - timedelta(days=7)
        recent_patients = patients.filter(created_at__gte=since).count()

        district_rows = []
        for d in districts:
            chw_qs = HealthWorker.objects.filter(district=d, is_active=True)
            district_rows.append(
                {
                    'district': d,
                    'chw_count': chw_qs.count(),
                    'patient_count': Patient.objects.filter(assigned_chw__in=chw_qs).count(),
                }
            )

        return {
            'districts': districts,
            'district_rows': district_rows,
            'chw_count': chws.distinct().count(),
            'patient_count': patients.distinct().count(),
            'open_alert_count': open_alerts.count(),
            'active_pregnancy_count': active_preg.distinct().count(),
            'recent_patient_count': recent_patients,
        }

    def _admin_stats(self):
        open_alerts = Alert.objects.filter(resolved=False).count()
        return {
            'patient_count': Patient.objects.count(),
            'chw_count': HealthWorker.objects.filter(is_active=True).count(),
            'district_count': District.objects.count(),
            'open_alert_count': open_alerts,
            'active_pregnancy_count': PregnancyRecord.objects.filter(is_active=True).count(),
        }
