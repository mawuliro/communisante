from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

router = DefaultRouter()
router.register(r'patients', views.PatientViewSet, basename='patient')

app_name = 'api'

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('triage/run/', views.TriageRunAPIView.as_view(), name='triage-run'),
    path('schema/', views.PublicSchemaView.as_view(), name='api-schema'),
    path(
        'schema/swagger/',
        views.PublicSwaggerView.as_view(url_name='api:api-schema'),
        name='api-swagger',
    ),
    path('', include(router.urls)),
]
