from django import forms
from apps.profiles.models import ParentProfileExtra

# Timezone choices for Indian + common international users
TIMEZONE_CHOICES = [
    ('Asia/Kolkata', 'India Standard Time (IST, UTC+5:30)'),
    ('Asia/Dubai', 'UAE Standard Time (UTC+4)'),
    ('Asia/Singapore', 'Singapore Time (UTC+8)'),
    ('Europe/London', 'British Time (UTC+0/+1)'),
    ('America/New_York', 'US Eastern Time (UTC-5/-4)'),
    ('America/Los_Angeles', 'US Pacific Time (UTC-8/-7)'),
    ('Australia/Sydney', 'Australian Eastern Time (UTC+10/+11)'),
]


class NotificationPreferenceForm(forms.ModelForm):
    """
    Allows parents to set their preferred weekday notification time
    and opt in/out of notifications.
    """
    notification_time = forms.TimeField(
        widget=forms.TimeInput(
            attrs={
                'type': 'time',  # HTML5 time picker
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg '
                         'focus:ring-2 focus:ring-primary-500 outline-none',
            }
        ),
        required=False,
        help_text="Choose what time you'd like to receive weekday reading reminders (leave blank to disable weekday reminders)"
    )
    timezone = forms.ChoiceField(
        choices=TIMEZONE_CHOICES,
        initial='Asia/Kolkata',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg '
                     'focus:ring-2 focus:ring-primary-500 outline-none'
        }),
        required=False,
    )
    notifications_enabled = forms.BooleanField(
        required=False,
        label='Receive reading reminders',
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-gray-300 text-primary-500 focus:ring-primary-500'
        })
    )

    class Meta:
        model = ParentProfileExtra
        fields = ['notifications_enabled', 'notification_time', 'timezone']
