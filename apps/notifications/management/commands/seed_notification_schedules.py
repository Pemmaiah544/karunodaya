"""
Management command to create django-q2 Schedule entries for notifications.
Run once after deploy to set up the periodic tasks.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from django_q.models import Schedule


class Command(BaseCommand):
    help = 'Create django-q2 Schedule entries for notifications (idempotent)'

    def handle(self, *args, **options):
        interval = settings.WEEKEND_NOTIFICATION_INTERVAL_HOURS
        weekend_cron = f'0 */{interval} * * 6,0'

        # Create or get weekend schedule
        weekend_schedule, weekend_created = Schedule.objects.get_or_create(
            name='weekend_reading_notifications',
            defaults={
                'func': 'apps.notifications.tasks.send_weekend_notifications',
                'schedule_type': Schedule.CRON,
                'cron': weekend_cron,
                'repeats': -1,  # forever
            }
        )

        # Create or get weekday schedule
        weekday_schedule, weekday_created = Schedule.objects.get_or_create(
            name='weekday_reading_notifications',
            defaults={
                'func': 'apps.notifications.tasks.send_weekday_notifications',
                'schedule_type': Schedule.CRON,
                'cron': '* * * * 1-5',  # every minute, Mon–Fri
                'repeats': -1,
            }
        )

        if weekend_created:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created weekend schedule: {weekend_cron}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'✓ Weekend schedule already exists: {weekend_schedule.cron}')
            )

        if weekday_created:
            self.stdout.write(
                self.style.SUCCESS('✓ Created weekday schedule: * * * * 1-5 (every minute)')
            )
        else:
            self.stdout.write(
                self.style.WARNING('✓ Weekday schedule already exists')
            )

        self.stdout.write(
            self.style.SUCCESS('\n✓ Notification schedules initialized successfully!')
        )
        self.stdout.write(
            'View/edit schedules in Django admin under "Django Q → Schedules"'
        )
