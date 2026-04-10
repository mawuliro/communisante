from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import District, HealthWorker, User


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'supervisor')
    search_fields = ('name', 'region')


@admin.register(HealthWorker)
class HealthWorkerAdmin(admin.ModelAdmin):
    list_display = ('user', 'district', 'phone', 'is_active')
    list_filter = ('district', 'is_active')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone')


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Custom admin interface for User model.
    """
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'phone', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    
    fieldsets = UserAdmin.fieldsets + (
        (_('Health Worker Information'), {
            'fields': ('role', 'phone', 'language'),
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        (_('Health Worker Information'), {
            'fields': ('role', 'phone', 'language'),
        }),
    )