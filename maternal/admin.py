from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import PregnancyRecord, PrenatalVisit


@admin.register(PregnancyRecord)
class PregnancyRecordAdmin(admin.ModelAdmin):
    list_display = (
        'patient',
        'last_menstrual_period',
        'expected_delivery_date',
        'risk_level',
        'is_active',
    )
    list_filter = ('risk_level', 'is_active')
    search_fields = ('patient__first_name', 'patient__last_name')
    autocomplete_fields = ('patient',)


@admin.register(PrenatalVisit)
class PrenatalVisitAdmin(admin.ModelAdmin):
    list_display = ('pregnancy', 'date', 'blood_pressure_systolic', 'blood_pressure_diastolic', 'weight_kg', 'recorded_by')
    list_filter = ('date', 'recorded_by__district')
    autocomplete_fields = ('pregnancy', 'recorded_by')
    date_hierarchy = 'date'
