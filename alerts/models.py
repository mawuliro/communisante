"""
Operational alerts for supervisors and CHWs (missed visits, danger signs, risk).
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from maternal.models import PregnancyRecord
from patients.models import Patient


class Alert(models.Model):
    """System- or user-generated alert requiring follow-up."""

    class AlertType(models.TextChoices):
        MISSED_VISIT = 'MISSED_VISIT', _('Missed visit')
        DANGER_SIGN = 'DANGER_SIGN', _('Danger sign')
        HIGH_RISK = 'HIGH_RISK', _('High risk')

    class Severity(models.TextChoices):
        LOW = 'LOW', _('Low')
        MEDIUM = 'MEDIUM', _('Medium')
        HIGH = 'HIGH', _('High')
        CRITICAL = 'CRITICAL', _('Critical')

    type = models.CharField(
        max_length=20,
        choices=AlertType.choices,
        verbose_name=_('alert type'),
    )
    related_patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='alerts',
        verbose_name=_('related patient'),
    )
    related_pregnancy = models.ForeignKey(
        PregnancyRecord,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts',
        verbose_name=_('related pregnancy'),
    )
    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        verbose_name=_('severity'),
    )
    resolved = models.BooleanField(default=False, verbose_name=_('resolved'))
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts',
        verbose_name=_('resolved by'),
    )
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name=_('resolved at'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))
    notes = models.TextField(blank=True, verbose_name=_('notes'))

    class Meta:
        verbose_name = _('alert')
        verbose_name_plural = _('alerts')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['resolved', 'severity', 'created_at']),
            models.Index(fields=['related_patient', 'created_at']),
        ]

    def __str__(self):
        return _('%(type)s, %(patient)s') % {
            'type': self.get_type_display(),
            'patient': self.related_patient,
        }
