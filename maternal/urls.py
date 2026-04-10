from django.urls import path

from maternal import views

app_name = 'maternal'

urlpatterns = [
    path('', views.PregnancyListView.as_view(), name='pregnancy_list'),
    path('new/', views.PregnancyCreateView.as_view(), name='pregnancy_create'),
    path(
        'patient/<int:patient_pk>/new/',
        views.PregnancyCreateView.as_view(),
        name='pregnancy_create_for_patient',
    ),
    path('<int:pk>/', views.PregnancyDetailView.as_view(), name='pregnancy_detail'),
    path('<int:pk>/edit/', views.PregnancyUpdateView.as_view(), name='pregnancy_update'),
    path(
        '<int:pregnancy_pk>/visits/new/',
        views.PrenatalVisitCreateView.as_view(),
        name='prenatal_visit_create',
    ),
    path(
        'visits/<int:pk>/',
        views.PrenatalVisitDetailView.as_view(),
        name='prenatal_visit_detail',
    ),
]
