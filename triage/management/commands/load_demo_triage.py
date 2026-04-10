"""
Create a demo child-style triage protocol (illustration only, not a clinical standard).
"""

from django.core.management.base import BaseCommand

from triage.models import Symptom, SymptomProtocol, TriageRule


class Command(BaseCommand):
    help = 'Loads a demo triage protocol when none named "Demo child triage" exists.'

    def handle(self, *args, **options):
        if SymptomProtocol.objects.filter(name='Demo child triage').exists():
            self.stdout.write(self.style.WARNING('Demo protocol already loaded.'))
            return

        protocol = SymptomProtocol.objects.create(
            name='Demo child triage',
            description=(
                'Illustration for training. Replace with a validated local protocol '
                'and weights agreed with your district medical officer.'
            ),
            version=1,
            is_active=True,
        )

        rows = [
            ('General', 'Cough', 2),
            ('General', 'Mild fever', 3),
            ('Danger signs', 'Fast breathing', 8),
            ('Danger signs', 'Not able to drink or breastfeed', 12),
            ('Danger signs', 'Convulsions', 20),
            ('Danger signs', 'Very sleepy or unconscious', 15),
        ]
        for category, name, weight in rows:
            Symptom.objects.create(
                protocol=protocol,
                name=name,
                severity_weight=weight,
                category=category,
                is_active=True,
            )

        TriageRule.objects.create(
            protocol=protocol,
            min_score=0,
            max_score=5,
            recommendation=TriageRule.Recommendation.MONITOR,
            explanation=(
                'Signs suggest mild illness. Continue care at home and watch for danger signs.'
            ),
            next_steps=(
                'Teach the caregiver when to return. Follow your local IMCI counseling cards.'
            ),
        )
        TriageRule.objects.create(
            protocol=protocol,
            min_score=6,
            max_score=14,
            recommendation=TriageRule.Recommendation.TREATMENT,
            explanation=(
                'The child needs assessment and treatment that a CHW can often provide on site.'
            ),
            next_steps=(
                'Give first-line treatment per national guidelines and review within 48 hours.'
            ),
        )
        TriageRule.objects.create(
            protocol=protocol,
            min_score=15,
            max_score=999,
            recommendation=TriageRule.Recommendation.URGENT,
            explanation=(
                'Danger signs are present or the score is high. Refer urgently to a higher level facility.'
            ),
            next_steps=(
                'Arrange transport, keep the child warm, and document symptoms for the referral note.'
            ),
        )

        self.stdout.write(self.style.SUCCESS('Demo triage protocol created.'))
