from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Alert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('type', 'related_patient', 'severity', 'resolved', 'created_at')
    list_filter = ('type', 'severity', 'resolved', 'created_at')
    search_fields = ('related_patient__first_name', 'related_patient__last_name', 'notes')
    autocomplete_fields = ('related_patient', 'related_pregnancy', 'resolved_by')
    date_hierarchy = 'created_at'
