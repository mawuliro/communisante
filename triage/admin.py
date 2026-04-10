from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Symptom, SymptomCheck, SymptomProtocol, TriageRule


class SymptomInline(admin.TabularInline):
    model = Symptom
    extra = 0


class TriageRuleInline(admin.TabularInline):
    model = TriageRule
    extra = 0


@admin.register(SymptomProtocol)
class SymptomProtocolAdmin(admin.ModelAdmin):
    list_display = ('name', 'version', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    inlines = [SymptomInline, TriageRuleInline]


@admin.register(Symptom)
class SymptomAdmin(admin.ModelAdmin):
    list_display = ('name', 'protocol', 'severity_weight', 'category', 'is_active')
    list_filter = ('protocol', 'is_active', 'category')
    search_fields = ('name', 'category')


@admin.register(TriageRule)
class TriageRuleAdmin(admin.ModelAdmin):
    list_display = ('protocol', 'min_score', 'max_score', 'recommendation')
    list_filter = ('protocol', 'recommendation')


@admin.register(SymptomCheck)
class SymptomCheckAdmin(admin.ModelAdmin):
    list_display = ('patient', 'score', 'recommendation_given', 'date', 'performed_by')
    list_filter = ('recommendation_given', 'date', 'performed_by__district')
    autocomplete_fields = ('patient', 'performed_by')
    filter_horizontal = ('symptoms_selected',)
    date_hierarchy = 'date'
