from django.urls import path

from alerts import views

app_name = 'alerts'

urlpatterns = [
    path('', views.AlertListView.as_view(), name='list'),
    path('<int:pk>/resolve/', views.AlertResolveView.as_view(), name='resolve'),
]
