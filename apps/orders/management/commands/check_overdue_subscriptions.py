"""
Management command to check and update overdue subscription cycles.

Usage:
    python manage.py check_overdue_subscriptions

Should be run daily via cron job.
"""

from django.core.management.base import BaseCommand
from services.curation import check_and_update_overdue_cycles


class Command(BaseCommand):
    help = 'Check and update overdue subscription cycles with late fees'

    def handle(self, *args, **options):
        self.stdout.write('Checking for overdue subscriptions...')

        stats = check_and_update_overdue_cycles()

        self.stdout.write(self.style.SUCCESS(
            f"\nResults:"
            f"\n  Total Active Cycles: {stats['total_active']}"
            f"\n  Newly Marked Overdue: {stats['now_overdue']}"
            f"\n  Late Fees Updated: {stats['late_fees_updated']}"
        ))

        if stats['now_overdue'] > 0:
            self.stdout.write(self.style.WARNING(
                f"\n⚠ {stats['now_overdue']} cycles are now overdue!"
            ))
