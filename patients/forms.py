"""
Patient forms: CHWs auto-assign themselves; supervisors pick a CHW in their districts.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from accounts.models import HealthWorker
from patients.access import assignable_health_workers
from patients.models import Patient


class PatientForm(forms.ModelForm):
    assigned_chw = forms.ModelChoiceField(
        queryset=HealthWorker.objects.none(),
        required=True,
        label=_('Assigned CHW'),
    )

    class Meta:
        model = Patient
        fields = ('first_name', 'last_name', 'age', 'sex', 'village', 'assigned_chw')
        labels = {
            'first_name': _('First name'),
            'last_name': _('Last name'),
            'age': _('Age'),
            'sex': _('Sex'),
            'village': _('Village'),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        profile = getattr(user, 'health_worker_profile', None) if user else None

        if profile is not None and profile.is_active:
            self.fields['assigned_chw'].queryset = HealthWorker.objects.filter(pk=profile.pk)
            self.fields['assigned_chw'].initial = profile
            self.fields['assigned_chw'].widget = forms.HiddenInput()
        else:
            self.fields['assigned_chw'].queryset = assignable_health_workers(user)
            self.fields['assigned_chw'].label_from_instance = self._label_chw

    @staticmethod
    def _label_chw(obj: HealthWorker) -> str:
        name = obj.user.get_full_name() or obj.user.username
        return f'{name} ({obj.district.name})'

    def clean_assigned_chw(self):
        chw = self.cleaned_data['assigned_chw']
        profile = getattr(self.user, 'health_worker_profile', None) if self.user else None
        if profile is not None and profile.is_active:
            if chw.pk != profile.pk:
                raise forms.ValidationError(_('Invalid assignee.'))
            return chw
        qs = assignable_health_workers(self.user)
        if not qs.filter(pk=chw.pk).exists():
            raise forms.ValidationError(_('You cannot assign a patient to this health worker.'))
        return chw
