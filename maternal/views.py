"""
Maternal health: pregnancy register, detail, and prenatal visits (CBVs).
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView

from maternal.access import pregnancy_queryset_for_user, prenatal_visit_queryset_for_user
from maternal.forms import PregnancyForm, PrenatalVisitForm
from maternal.models import PregnancyRecord, PrenatalVisit
from maternal.services import bp_follow_up_suggested
from patients.access import patient_queryset_for_user, user_can_manage_patients


class CanManageMaternalMixin(UserPassesTestMixin):
    def test_func(self):
        return user_can_manage_patients(self.request.user)

    def handle_no_permission(self):
        messages.error(
            self.request,
            _('You do not have permission to add or change pregnancy records.'),
        )
        return redirect('maternal:pregnancy_list')


class PregnancyListView(LoginRequiredMixin, ListView):
    model = PregnancyRecord
    template_name = 'maternal/pregnancy_list.html'
    context_object_name = 'pregnancies'
    paginate_by = 20

    def get_queryset(self):
        qs = pregnancy_queryset_for_user(self.request.user).order_by('-is_active', '-last_menstrual_period')
        active = self.request.GET.get('active')
        if active == '1':
            qs = qs.filter(is_active=True)
        elif active == '0':
            qs = qs.filter(is_active=False)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filter_active'] = self.request.GET.get('active', '')
        ctx['can_manage_maternal'] = user_can_manage_patients(self.request.user)
        return ctx


class PregnancyDetailView(LoginRequiredMixin, DetailView):
    model = PregnancyRecord
    template_name = 'maternal/pregnancy_detail.html'
    context_object_name = 'pregnancy'

    def get_queryset(self):
        visits = Prefetch(
            'prenatal_visits',
            queryset=PrenatalVisit.objects.select_related(
                'recorded_by',
                'recorded_by__user',
            ).order_by('-date', '-id'),
        )
        return pregnancy_queryset_for_user(self.request.user).prefetch_related(visits)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['can_manage_maternal'] = user_can_manage_patients(self.request.user)
        ctx['bp_flags'] = []
        for v in self.object.prenatal_visits.all():
            if bp_follow_up_suggested(v.blood_pressure_systolic, v.blood_pressure_diastolic):
                ctx['bp_flags'].append(v)
        return ctx


class PregnancyCreateView(LoginRequiredMixin, CanManageMaternalMixin, CreateView):
    model = PregnancyRecord
    form_class = PregnancyForm
    template_name = 'maternal/pregnancy_form.html'

    def dispatch(self, request, *args, **kwargs):
        patient_pk = kwargs.get('patient_pk')
        if patient_pk is not None:
            get_object_or_404(patient_queryset_for_user(request.user), pk=patient_pk)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        pk = self.kwargs.get('patient_pk')
        if pk is not None:
            initial['patient'] = pk
        return initial

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['user'] = self.request.user
        return kw

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_title'] = _('New pregnancy')
        return ctx

    def form_valid(self, form):
        messages.success(self.request, _('Pregnancy record saved.'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('maternal:pregnancy_detail', kwargs={'pk': self.object.pk})


class PregnancyUpdateView(LoginRequiredMixin, CanManageMaternalMixin, UpdateView):
    model = PregnancyRecord
    form_class = PregnancyForm
    template_name = 'maternal/pregnancy_form.html'

    def get_queryset(self):
        return pregnancy_queryset_for_user(self.request.user)

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['user'] = self.request.user
        return kw

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form_title'] = _('Edit pregnancy')
        return ctx

    def form_valid(self, form):
        messages.success(self.request, _('Pregnancy record updated.'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('maternal:pregnancy_detail', kwargs={'pk': self.object.pk})


class PrenatalVisitCreateView(LoginRequiredMixin, CanManageMaternalMixin, CreateView):
    model = PrenatalVisit
    form_class = PrenatalVisitForm
    template_name = 'maternal/prenatal_visit_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.pregnancy = get_object_or_404(
            pregnancy_queryset_for_user(request.user),
            pk=kwargs['pregnancy_pk'],
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw['user'] = self.request.user
        kw['pregnancy'] = self.pregnancy
        return kw

    def form_valid(self, form):
        form.instance.pregnancy = self.pregnancy
        messages.success(self.request, _('Prenatal visit saved.'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['pregnancy'] = self.pregnancy
        return ctx

    def get_success_url(self):
        return reverse('maternal:pregnancy_detail', kwargs={'pk': self.pregnancy.pk})


class PrenatalVisitDetailView(LoginRequiredMixin, DetailView):
    model = PrenatalVisit
    template_name = 'maternal/prenatal_visit_detail.html'
    context_object_name = 'visit'

    def get_queryset(self):
        return prenatal_visit_queryset_for_user(self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['bp_alert'] = bp_follow_up_suggested(
            self.object.blood_pressure_systolic,
            self.object.blood_pressure_diastolic,
        )
        return ctx
