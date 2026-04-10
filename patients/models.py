"""
Patient registration and assignment to community health workers.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from accounts.models import HealthWorker


class Patient(models.Model):
    """A person registered in the system and followed by one CHW."""

    class Sex(models.TextChoices):
        FEMALE = 'F', _('Female')
        MALE = 'M', _('Male')
        OTHER = 'O', _('Other / prefer not to say')

    first_name = models.CharField(max_length=150, verbose_name=_('first name'))
    last_name = models.CharField(max_length=150, verbose_name=_('last name'))
    age = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name=_('age'))
    sex = models.CharField(
        max_length=1,
        choices=Sex.choices,
        blank=True,
        verbose_name=_('sex'),
    )
    village = models.CharField(max_length=255, blank=True, verbose_name=_('village'))
    assigned_chw = models.ForeignKey(
        HealthWorker,
        on_delete=models.PROTECT,
        related_name='patients',
        verbose_name=_('assigned CHW'),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))

    class Meta:
        verbose_name = _('patient')
        verbose_name_plural = _('patients')
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['assigned_chw', 'created_at']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()
