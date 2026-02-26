# Generated migration for NotificationLog model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('profiles', '0015_remove_child_location_consented_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(
                    choices=[('WEEKDAY_REMINDER', 'Weekday Reading Reminder'), ('WEEKEND_REMINDER', 'Weekend Reading Reminder')],
                    max_length=30
                )),
                ('scheduled_date', models.DateField()),
                ('slot_key', models.CharField(max_length=10)),
                ('status', models.CharField(
                    choices=[('SENT', 'Sent Successfully'), ('FAILED', 'Failed'), ('SKIPPED', 'Skipped (no email)')],
                    max_length=10
                )),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('parent', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notification_logs',
                    to='profiles.parentprofile'
                )),
            ],
            options={
                'verbose_name': 'Notification Log',
                'verbose_name_plural': 'Notification Logs',
                'ordering': ['-sent_at'],
                'unique_together': {('parent', 'notification_type', 'scheduled_date', 'slot_key')},
            },
        ),
        migrations.AddIndex(
            model_name='notificationlog',
            index=models.Index(fields=['scheduled_date', 'notification_type'], name='notif_log_date_type_idx'),
        ),
        migrations.AddIndex(
            model_name='notificationlog',
            index=models.Index(fields=['parent', 'scheduled_date'], name='notif_log_parent_date_idx'),
        ),
    ]
