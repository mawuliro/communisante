"""Read-only patient API + triage run endpoint (JWT). Mirrors web access rules."""

from django.db import transaction
from django.utils.translation import gettext as _
from drf_spectacular.utils import extend_schema, extend_schema_view
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from patients.access import health_worker_for_triage, patient_queryset_for_user
from triage.models import Symptom, SymptomCheck, SymptomProtocol
from triage.services import protocol_with_rules, run_triage

from .serializers import (
    PatientSerializer,
    SymptomCheckSerializer,
    TriageRunInputSerializer,
)


@extend_schema_view(
    list=extend_schema(summary='List patients visible to the authenticated user'),
    retrieve=extend_schema(summary='Patient detail'),
)
class PatientViewSet(viewsets.ReadOnlyModelViewSet):
    """CHW sees assigned patients; supervisor sees district; admin sees all."""

    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return patient_queryset_for_user(self.request.user).order_by('last_name', 'first_name')


class TriageRunAPIView(APIView):
    """POST: run rule-based triage and persist a ``SymptomCheck`` (same logic as the web UI)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=TriageRunInputSerializer,
        responses={201: SymptomCheckSerializer},
        summary='Run triage for a patient',
    )
    def post(self, request):
        ser = TriageRunInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        protocol_id = ser.validated_data['protocol_id']
        patient_id = ser.validated_data['patient_id']
        symptom_ids = ser.validated_data.get('symptom_ids') or []

        hw = health_worker_for_triage(request.user)
        if hw is None:
            return Response(
                {'detail': _('Active community health worker profile required.')},
                status=status.HTTP_403_FORBIDDEN,
            )

        patient = patient_queryset_for_user(request.user).filter(pk=patient_id).first()
        if patient is None:
            return Response({'detail': _('Patient not found.')}, status=status.HTTP_404_NOT_FOUND)

        protocol = SymptomProtocol.objects.filter(pk=protocol_id, is_active=True).first()
        if protocol is None:
            return Response({'detail': _('Protocol not found.')}, status=status.HTTP_404_NOT_FOUND)

        proto_full = protocol_with_rules(protocol.pk)
        if proto_full is None:
            return Response(
                {'detail': _('Protocol has no rules configured.')},
                status=status.HTTP_400_BAD_REQUEST,
            )

        score, rule, err = run_triage(proto_full, symptom_ids)
        if err:
            return Response({'detail': err, 'score': score}, status=status.HTTP_400_BAD_REQUEST)
        if rule is None:
            return Response(
                {'detail': _('No matching rule.'), 'score': score},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            check = SymptomCheck.objects.create(
                patient=patient,
                score=score,
                recommendation_given=rule.recommendation,
                performed_by=hw,
            )
            check.symptoms_selected.set(
                Symptom.objects.filter(pk__in=symptom_ids, protocol=protocol)
            )

        check = SymptomCheck.objects.prefetch_related('symptoms_selected').get(pk=check.pk)
        return Response(SymptomCheckSerializer(check).data, status=status.HTTP_201_CREATED)


class PublicSchemaView(SpectacularAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []


class PublicSwaggerView(SpectacularSwaggerView):
    permission_classes = [AllowAny]
    authentication_classes = []
