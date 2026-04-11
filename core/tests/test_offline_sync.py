"""Tests for POST /sync/ offline queue replay."""

from __future__ import annotations

import json
from datetime import date

from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import District, HealthWorker, User
from alerts.models import Alert
from maternal.models import PregnancyRecord
from patients.models import Patient
from triage.models import Symptom, SymptomProtocol, TriageRule


class OfflineSyncViewTests(TestCase):
    def setUp(self) -> None:
        self.district = District.objects.create(name='Test District')
        self.user = User.objects.create_user('chw1', password='pass12345', role=User.Role.CHW)
        self.hw = HealthWorker.objects.create(user=self.user, district=self.district, is_active=True)
        self.patient = Patient.objects.create(
            first_name='Ada',
            last_name='Lovelace',
            age=30,
            sex='F',
            village='V1',
            assigned_chw=self.hw,
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_patient_create(self) -> None:
        body = {
            'items': [
                {
                    'id': 'id-1',
                    'kind': 'patient_create',
                    'payload': {
                        'first_name': 'New',
                        'last_name': 'Person',
                        'age': '22',
                        'sex': 'M',
                        'village': 'V2',
                        'assigned_chw': str(self.hw.pk),
                    },
                }
            ]
        }
        r = self.client.post(reverse('offline-sync'), data=json.dumps(body), content_type='application/json')
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.content.decode())
        self.assertTrue(data['ok'])
        self.assertTrue(data['results'][0]['ok'])
        p = Patient.objects.get(last_name='Person')
        self.assertEqual(p.assigned_chw_id, self.hw.pk)

    def test_pregnancy_and_prenatal_create(self) -> None:
        lmp = date(2025, 1, 1)
        body = {
            'items': [
                {
                    'id': 'p1',
                    'kind': 'pregnancy_create',
                    'payload': {
                        'patient': str(self.patient.pk),
                        'last_menstrual_period': lmp.isoformat(),
                        'risk_level': 'LOW',
                        'is_active': 'on',
                    },
                }
            ]
        }
        r = self.client.post(reverse('offline-sync'), data=json.dumps(body), content_type='application/json')
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.content.decode())
        self.assertTrue(data['ok'], data)
        preg = PregnancyRecord.objects.get(patient=self.patient)
        self.assertTrue(preg.is_active)

        body2 = {
            'items': [
                {
                    'id': 'v1',
                    'kind': 'prenatal_visit_create',
                    'payload': {
                        'pregnancy_pk': str(preg.pk),
                        'date': date(2025, 2, 1).isoformat(),
                        'blood_pressure_systolic': '120',
                        'blood_pressure_diastolic': '80',
                        'weight_kg': '60',
                        'symptoms_noted': '',
                        'notes': '',
                        'recorded_by': str(self.hw.pk),
                    },
                }
            ]
        }
        r2 = self.client.post(reverse('offline-sync'), data=json.dumps(body2), content_type='application/json')
        self.assertEqual(r2.status_code, 200)
        data2 = json.loads(r2.content.decode())
        self.assertTrue(data2['ok'], data2)
        self.assertEqual(preg.prenatal_visits.count(), 1)

    def test_triage_session(self) -> None:
        protocol = SymptomProtocol.objects.create(name='P1', description='', is_active=True)
        s1 = Symptom.objects.create(protocol=protocol, name='Cough', category='General', severity_weight=2, is_active=True)
        TriageRule.objects.create(
            protocol=protocol,
            min_score=0,
            max_score=10,
            recommendation=TriageRule.Recommendation.MONITOR,
            explanation='Test',
            next_steps='Rest',
        )
        body = {
            'items': [
                {
                    'id': 't1',
                    'kind': 'triage_session',
                    'payload': {
                        'protocol_pk': protocol.pk,
                        'patient_pk': self.patient.pk,
                        'symptom_ids': [s1.pk],
                    },
                }
            ]
        }
        r = self.client.post(reverse('offline-sync'), data=json.dumps(body), content_type='application/json')
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.content.decode())
        self.assertTrue(data['ok'], data)

    def test_alert_resolve(self) -> None:
        alert = Alert.objects.create(
            type=Alert.AlertType.HIGH_RISK,
            related_patient=self.patient,
            severity=Alert.Severity.MEDIUM,
        )
        body = {
            'items': [
                {
                    'id': 'a1',
                    'kind': 'alert_resolve',
                    'payload': {'alert_pk': str(alert.pk), 'notes': 'Seen offline'},
                }
            ]
        }
        r = self.client.post(reverse('offline-sync'), data=json.dumps(body), content_type='application/json')
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.content.decode())
        self.assertTrue(data['ok'], data)
        alert.refresh_from_db()
        self.assertTrue(alert.resolved)
        self.assertEqual(alert.resolved_by_id, self.user.pk)
        self.assertIn('Seen offline', alert.notes)

    def test_requires_auth(self) -> None:
        c = Client()
        r = c.post(
            reverse('offline-sync'),
            data=json.dumps({'items': []}),
            content_type='application/json',
        )
        self.assertEqual(r.status_code, 401)
