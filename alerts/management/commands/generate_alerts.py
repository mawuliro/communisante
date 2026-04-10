"""
Scheduled job: evaluate pregnancies and visits, create operational alerts.

Run daily on the server, for example:
    python manage.py generate_alerts

Railway: add a cron job or scheduled task that runs this command once per day.
"""

from django.core.management.base import BaseCommand

from alerts.services import run_all_alert_generators


class Command(BaseCommand):
    help = 'Generates missed visit, blood pressure, and high risk alerts from current data.'

    def handle(self, *args, **options):
        counts = run_all_alert_generators()
        self.stdout.write(
            self.style.SUCCESS(
                'Alerts created: missed visit=%(mv)s, BP danger=%(bp)s, high risk=%(hr)s'
                % {
                    'mv': counts['missed_visit'],
                    'bp': counts['bp_danger'],
                    'hr': counts['high_risk'],
                }
            )
        )
