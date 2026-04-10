"""
Custom User model for CommuniSanté.
Extends Django's AbstractUser to add role-based permissions.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model with role-based access control.
    """
    
    class Role(models.TextChoices):
        CHW = 'CHW', _('Community Health Worker')
        SUPERVISOR = 'SUPERVISOR', _('District Supervisor')
        ADMIN = 'ADMIN', _('System Administrator')
    
    # Additional fields beyond Django's default User
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CHW,
        verbose_name=_('role')
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('phone number')
    )
    class Language(models.TextChoices):
        ENGLISH = 'en', _('English')
        FRENCH = 'fr', _('French')

    language = models.CharField(
        max_length=10,
        choices=Language.choices,
        default=Language.FRENCH,
        verbose_name=_('preferred language'),
    )
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
    
    @property
    def is_chw(self):
        """Check if user is a Community Health Worker."""
        return self.role == self.Role.CHW
    
    @property
    def is_supervisor(self):
        """Check if user is a District Supervisor."""
        return self.role == self.Role.SUPERVISOR
    
    @property
    def is_admin_user(self):
        """Check if user is a System Administrator."""
        return self.role == self.Role.ADMIN or self.is_superuser


class District(models.Model):
    """Geographic district; each has one supervising user when assigned."""

    name = models.CharField(max_length=255, verbose_name=_('district name'))
    region = models.CharField(max_length=255, blank=True, verbose_name=_('region'))
    supervisor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supervised_districts',
        verbose_name=_('supervisor'),
    )

    class Meta:
        verbose_name = _('district')
        verbose_name_plural = _('districts')
        ordering = ['name']

    def __str__(self):
        return self.name


class HealthWorker(models.Model):
    """Profile linking a login (User) to a district CHW record."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='health_worker_profile',
        verbose_name=_('user'),
    )
    district = models.ForeignKey(
        District,
        on_delete=models.PROTECT,
        related_name='health_workers',
        verbose_name=_('district'),
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('contact phone'),
    )
    is_active = models.BooleanField(default=True, verbose_name=_('active'))

    class Meta:
        verbose_name = _('health worker')
        verbose_name_plural = _('health workers')
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}, {self.district.name}"