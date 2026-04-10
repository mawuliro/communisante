"""
Pregnancy and prenatal visit forms with CHW auto-attribution.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from accounts.models import HealthWorker
from maternal.models import PregnancyRecord, PrenatalVisit
from patients.access import assignable_health_workers, patient_queryset_for_user


class PregnancyForm(forms.ModelForm):
    class Meta:
        model = PregnancyRecord
        fields = ('patient', 'last_menstrual_period', 'risk_level', 'is_active')
        labels = {
            'patient': _('Patient'),
            'last_menstrual_period': _('Last menstrual period'),
            'risk_level': _('Risk level'),
            'is_active': _('Active pregnancy'),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields['patient'].queryset = patient_queryset_for_user(user).order_by(
            'last_name', 'first_name'
        )

    def clean_patient(self):
        patient = self.cleaned_data['patient']
        if not patient_queryset_for_user(self.user).filter(pk=patient.pk).exists():
            raise forms.ValidationError(_('You cannot open a pregnancy for this patient.'))
        return patient


class PrenatalVisitForm(forms.ModelForm):
    recorded_by = forms.ModelChoiceField(
        queryset=HealthWorker.objects.none(),
        required=True,
        label=_('Recorded by'),
    )

    class Meta:
        model = PrenatalVisit
        fields = (
            'date',
            'blood_pressure_systolic',
            'blood_pressure_diastolic',
            'weight_kg',
            'symptoms_noted',
            'notes',
            'recorded_by',
        )
        labels = {
            'date': _('Visit date'),
            'blood_pressure_systolic': _('Systolic BP'),
            'blood_pressure_diastolic': _('Diastolic BP'),
            'weight_kg': _('Weight (kg)'),
            'symptoms_noted': _('Symptoms noted'),
            'notes': _('Notes'),
        }

    def __init__(self, *args, user=None, pregnancy=None, **kwargs):
        self.user = user
        self.pregnancy = pregnancy
        super().__init__(*args, **kwargs)
        profile = getattr(user, 'health_worker_profile', None) if user else None

        if profile is not None and profile.is_active:
            self.fields['recorded_by'].queryset = HealthWorker.objects.filter(pk=profile.pk)
            self.fields['recorded_by'].initial = profile
            self.fields['recorded_by'].widget = forms.HiddenInput()
        else:
            self.fields['recorded_by'].queryset = assignable_health_workers(user)
            self.fields['recorded_by'].label_from_instance = self._label_chw

    @staticmethod
    def _label_chw(obj: HealthWorker) -> str:
        name = obj.user.get_full_name() or obj.user.username
        return f'{name} ({obj.district.name})'

    def clean_recorded_by(self):
        chw = self.cleaned_data['recorded_by']
        profile = getattr(self.user, 'health_worker_profile', None) if self.user else None
        if profile is not None and profile.is_active:
            if chw.pk != profile.pk:
                raise forms.ValidationError(_('Invalid recorder.'))
            return chw
        qs = assignable_health_workers(self.user)
        if not qs.filter(pk=chw.pk).exists():
            raise forms.ValidationError(_('You cannot attribute this visit to that health worker.'))
        return chw
