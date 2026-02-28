from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.core.models import AdminProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Designate an existing superuser as the Super Admin'

    def add_arguments(self, parser):
        parser.add_argument('--email', help='Email of the superuser to promote')
        parser.add_argument('--username', help='Username of the superuser to promote')

    def handle(self, *args, **options):
        user = None

        if options.get('username'):
            try:
                user = User.objects.get(username=options['username'])
            except User.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"No user found with username: {options['username']}"))
                return
        elif options.get('email'):
            try:
                users = User.objects.filter(email=options['email'])
                if not users.exists():
                    self.stderr.write(self.style.ERROR(f"No user found with email: {options['email']}"))
                    return
                if users.count() > 1:
                    self.stderr.write(self.style.ERROR(
                        f"Multiple users found with email: {options['email']}\n"
                        f"Please specify using --username instead:\n"
                    ))
                    for u in users:
                        self.stderr.write(f"  - {u.username}")
                    return
                user = users.first()
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error: {str(e)}"))
                return
        else:
            self.stderr.write(self.style.ERROR("Please provide either --email or --username"))
            return

        user.is_staff = True
        user.is_superuser = True
        user.save()

        profile, _ = AdminProfile.objects.get_or_create(user=user)
        profile.is_super_admin = True
        profile.is_active = True
        profile.save()

        self.stdout.write(self.style.SUCCESS(
            f"{user.email} is now the Super Admin."
        ))
