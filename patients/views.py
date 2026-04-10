"""
Patient list, detail, and registration (class-based views).
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView

from maternal.models import PregnancyRecord

from patients.access import patient_queryset_for_user, user_can_manage_patients
from patients.forms import PatientForm
from patients.models import Patient


class PatientListView(LoginRequiredMixin, ListView):
    model = Patient
    context_object_name = 'patients'
    paginate_by = 25

    def get_queryset(self):
        qs = patient_queryset_for_user(self.request.user).order_by('last_name', 'first_name')
        q = (self.request.GET.get('q') or '').strip()
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(village__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['search_q'] = self.request.GET.get('q', '')
        ctx['can_manage_patients'] = user_can_manage_patients(self.request.user)
        return ctx


class PatientDetailView(LoginRequiredMixin, DetailView):
    model = Patient
    context_object_name = 'patient'

    def get_queryset(self):
        return patient_queryset_for_user(self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['can_manage_patients'] = user_can_manage_patients(self.request.user)
        patient = self.object
        ctx['patient_pregnancies'] = (
            PregnancyRecord.objects.filter(patient=patient)
            .order_by('-is_active', '-last_menstrual_period')[:10]
        )
        return ctx


class CanManagePatientsMixin(UserPassesTestMixin):
    def test_func(self):
        return user_can_manage_patients(self.request.user)

    def handle_no_permission(self):
        messages.error(
            self.request,
            _('You do not have permission to register or edit patients.'),
        )
        return redirect('patients:list')


class PatientCreateView(LoginRequiredMixin, CanManagePatientsMixin, CreateView):
    model = Patient
    form_class = PatientForm

    def get_success_url(self):
        return reverse('patients:detail', kwargs={'pk': self.object.pk})

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['user'] = self.request.user
        return kw

    def form_valid(self, form):
        messages.success(self.request, _('Patient saved.'))
        return super().form_valid(form)


class PatientUpdateView(LoginRequiredMixin, CanManagePatientsMixin, UpdateView):
    model = Patient
    form_class = PatientForm

    def get_success_url(self):
        return reverse('patients:detail', kwargs={'pk': self.object.pk})

    def get_queryset(self):
        return patient_queryset_for_user(self.request.user)

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['user'] = self.request.user
        return kw

    def form_valid(self, form):
        messages.success(self.request, _('Patient updated.'))
        return super().form_valid(form)
