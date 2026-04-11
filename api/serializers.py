"""DRF serializers for mobile / integrations (scoped like the web app)."""

from rest_framework import serializers

from patients.models import Patient
from triage.models import SymptomCheck


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = (
            'id',
            'first_name',
            'last_name',
            'age',
            'sex',
            'village',
            'assigned_chw',
            'created_at',
        )
        read_only_fields = fields


class SymptomCheckSerializer(serializers.ModelSerializer):
    patient_id = serializers.IntegerField(source='patient_id', read_only=True)
    symptom_ids = serializers.SerializerMethodField()

    class Meta:
        model = SymptomCheck
        fields = (
            'id',
            'patient_id',
            'score',
            'recommendation_given',
            'date',
            'performed_by',
            'symptom_ids',
        )
        read_only_fields = fields

    def get_symptom_ids(self, obj):
        return list(obj.symptoms_selected.values_list('id', flat=True))


class TriageRunInputSerializer(serializers.Serializer):
    protocol_id = serializers.IntegerField(min_value=1)
    patient_id = serializers.IntegerField(min_value=1)
    symptom_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
        required=False,
        default=list,
    )
