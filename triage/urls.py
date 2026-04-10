from django.urls import path

from triage import views

app_name = 'triage'

urlpatterns = [
    path('', views.ProtocolListView.as_view(), name='protocol_list'),
    path(
        'protocol/<int:protocol_pk>/choose-patient/',
        views.TriagePickPatientView.as_view(),
        name='pick_patient',
    ),
    path(
        'protocol/<int:protocol_pk>/patient/<int:patient_pk>/',
        views.TriageSessionView.as_view(),
        name='session',
    ),
    path('check/<int:pk>/', views.SymptomCheckDetailView.as_view(), name='check_detail'),
]
