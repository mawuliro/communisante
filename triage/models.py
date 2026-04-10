"""
Database-driven symptom triage protocols (IMCI/ANC-inspired; editable in admin).
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from accounts.models import HealthWorker
from patients.models import Patient


class SymptomProtocol(models.Model):
    """A versioned set of symptoms and score rules (e.g. IMCI child, ANC mother)."""

    name = models.CharField(max_length=255, verbose_name=_('protocol name'))
    description = models.TextField(blank=True, verbose_name=_('description'))
    version = models.PositiveIntegerField(default=1, verbose_name=_('version'))
    is_active = models.BooleanField(default=True, verbose_name=_('active'))

    class Meta:
        verbose_name = _('symptom protocol')
        verbose_name_plural = _('symptom protocols')
        ordering = ['name', '-version']

    def __str__(self):
        return f"{self.name} v{self.version}"


class Symptom(models.Model):
    """One sign or symptom in a protocol with a weight toward the total score."""

    protocol = models.ForeignKey(
        SymptomProtocol,
        on_delete=models.CASCADE,
        related_name='symptoms',
        verbose_name=_('protocol'),
    )
    name = models.CharField(max_length=255, verbose_name=_('symptom name'))
    severity_weight = models.IntegerField(verbose_name=_('severity weight'))
    category = models.CharField(max_length=100, blank=True, verbose_name=_('category'))
    is_active = models.BooleanField(default=True, verbose_name=_('active'))

    class Meta:
        verbose_name = _('symptom')
        verbose_name_plural = _('symptoms')
        ordering = ['protocol', 'category', 'name']
        indexes = [
            models.Index(fields=['protocol', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.protocol})"


class TriageRule(models.Model):
    """Maps a score range to a recommendation (fully data-driven)."""

    class Recommendation(models.TextChoices):
        URGENT = 'URGENT', _('Urgent referral')
        TREATMENT = 'TREATMENT', _('Basic treatment')
        MONITOR = 'MONITOR', _('Monitoring')

    protocol = models.ForeignKey(
        SymptomProtocol,
        on_delete=models.CASCADE,
        related_name='triage_rules',
        verbose_name=_('protocol'),
    )
    min_score = models.IntegerField(verbose_name=_('minimum score'))
    max_score = models.IntegerField(verbose_name=_('maximum score'))
    recommendation = models.CharField(
        max_length=20,
        choices=Recommendation.choices,
        verbose_name=_('recommendation'),
    )
    explanation = models.TextField(verbose_name=_('explanation'))
    next_steps = models.TextField(verbose_name=_('next steps'))

    class Meta:
        verbose_name = _('triage rule')
        verbose_name_plural = _('triage rules')
        ordering = ['protocol', 'min_score']
        indexes = [
            models.Index(fields=['protocol', 'min_score', 'max_score']),
        ]

    def __str__(self):
        return _('%(rec)s for %(protocol)s (scores %(min)s to %(max)s)') % {
            'rec': self.get_recommendation_display(),
            'protocol': self.protocol,
            'min': self.min_score,
            'max': self.max_score,
        }

    def clean(self):
        if self.min_score > self.max_score:
            raise ValidationError(_('Minimum score cannot exceed maximum score.'))


class SymptomCheck(models.Model):
    """One triage session: selected symptoms, computed score, and outcome."""

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='symptom_checks',
        verbose_name=_('patient'),
    )
    symptoms_selected = models.ManyToManyField(
        Symptom,
        related_name='symptom_checks',
        verbose_name=_('symptoms selected'),
    )
    score = models.IntegerField(verbose_name=_('score'))
    recommendation_given = models.CharField(
        max_length=20,
        choices=TriageRule.Recommendation.choices,
        verbose_name=_('recommendation given'),
    )
    date = models.DateTimeField(auto_now_add=True, verbose_name=_('date'))
    performed_by = models.ForeignKey(
        HealthWorker,
        on_delete=models.PROTECT,
        related_name='symptom_checks',
        verbose_name=_('performed by'),
    )

    class Meta:
        verbose_name = _('symptom check')
        verbose_name_plural = _('symptom checks')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['patient', 'date']),
            models.Index(fields=['performed_by', 'date']),
        ]

    def __str__(self):
        return _('Check for %(patient)s on %(date)s') % {
            'patient': self.patient,
            'date': self.date,
        }
