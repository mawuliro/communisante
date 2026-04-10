"""
Pregnancy records and prenatal visits (ANC).
"""

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from accounts.models import HealthWorker
from patients.models import Patient


def _edd_from_lmp(lmp):
    """Expected delivery date: LMP + 280 days (40 weeks), per standard antenatal dating."""
    if lmp is None:
        return None
    return lmp + timedelta(days=280)


class PregnancyRecord(models.Model):
    """One active pregnancy per patient workflow (close old record when delivery occurs)."""

    class RiskLevel(models.TextChoices):
        LOW = 'LOW', _('Low')
        MEDIUM = 'MEDIUM', _('Medium')
        HIGH = 'HIGH', _('High')

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='pregnancies',
        verbose_name=_('patient'),
    )
    last_menstrual_period = models.DateField(verbose_name=_('last menstrual period'))
    expected_delivery_date = models.DateField(
        editable=False,
        verbose_name=_('expected delivery date'),
    )
    risk_level = models.CharField(
        max_length=10,
        choices=RiskLevel.choices,
        default=RiskLevel.LOW,
        verbose_name=_('risk level'),
    )
    is_active = models.BooleanField(default=True, verbose_name=_('active'))

    class Meta:
        verbose_name = _('pregnancy record')
        verbose_name_plural = _('pregnancy records')
        ordering = ['-last_menstrual_period']
        indexes = [
            models.Index(fields=['patient', 'is_active']),
            models.Index(fields=['expected_delivery_date']),
        ]

    def __str__(self):
        return _('Pregnancy for %(patient)s (EDD %(edd)s)') % {
            'patient': self.patient,
            'edd': self.expected_delivery_date,
        }

    def clean(self):
        if self.last_menstrual_period is None:
            raise ValidationError({'last_menstrual_period': _('LMP is required.')})

    def save(self, *args, **kwargs):
        # Compute EDD before validation so ``expected_delivery_date`` is present for DB constraints
        self.expected_delivery_date = _edd_from_lmp(self.last_menstrual_period)
        self.full_clean()
        super().save(*args, **kwargs)


class PrenatalVisit(models.Model):
    """A single ANC contact visit."""

    pregnancy = models.ForeignKey(
        PregnancyRecord,
        on_delete=models.CASCADE,
        related_name='prenatal_visits',
        verbose_name=_('pregnancy'),
    )
    date = models.DateField(verbose_name=_('visit date'))
    blood_pressure_systolic = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_('blood pressure (systolic)'),
    )
    blood_pressure_diastolic = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_('blood pressure (diastolic)'),
    )
    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('weight (kg)'),
    )
    symptoms_noted = models.TextField(blank=True, verbose_name=_('symptoms noted'))
    notes = models.TextField(blank=True, verbose_name=_('notes'))
    recorded_by = models.ForeignKey(
        HealthWorker,
        on_delete=models.PROTECT,
        related_name='recorded_prenatal_visits',
        verbose_name=_('recorded by'),
    )

    class Meta:
        verbose_name = _('prenatal visit')
        verbose_name_plural = _('prenatal visits')
        ordering = ['-date', '-id']
        indexes = [
            models.Index(fields=['pregnancy', 'date']),
            models.Index(fields=['recorded_by', 'date']),
        ]

    def __str__(self):
        return _('Visit on %(date)s, %(patient)s') % {
            'date': self.date,
            'patient': self.pregnancy.patient,
        }
