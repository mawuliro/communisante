from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'age', 'sex', 'village', 'assigned_chw', 'created_at')
    list_filter = ('sex', 'assigned_chw__district')
    search_fields = ('first_name', 'last_name', 'village')
    autocomplete_fields = ('assigned_chw',)
    date_hierarchy = 'created_at'
