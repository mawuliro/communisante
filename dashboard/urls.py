from django.urls import path

from dashboard import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='home'),
    path('reports/districts.csv', views.DistrictCsvExportView.as_view(), name='report_district_csv'),
    path('reports/high-risk.pdf', views.HighRiskPdfExportView.as_view(), name='report_high_risk_pdf'),
]
