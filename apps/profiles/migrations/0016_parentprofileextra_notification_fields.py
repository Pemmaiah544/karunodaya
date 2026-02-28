# Generated migration for notification fields in ParentProfileExtra

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0015_remove_child_location_consented_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='parentprofileextra',
            name='notification_time',
            field=models.TimeField(
                blank=True,
                null=True,
                help_text='Exact time (HH:MM) for weekday reading reminders'
            ),
        ),
        migrations.AddField(
            model_name='parentprofileextra',
            name='timezone',
            field=models.CharField(
                max_length=50,
                default='Asia/Kolkata',
                help_text="Timezone for notification schedule (e.g. Asia/Kolkata)"
            ),
        ),
        migrations.AddField(
            model_name='parentprofileextra',
            name='notifications_enabled',
            field=models.BooleanField(
                default=True,
                help_text='Whether this parent wants reading reminder emails'
            ),
        ),
    ]
