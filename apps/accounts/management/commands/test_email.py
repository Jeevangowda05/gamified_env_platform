from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand

from apps.accounts.email_utils import is_smtp_configured, using_console_email


class Command(BaseCommand):
    help = 'Send a test email to verify Gmail SMTP is working'

    def add_arguments(self, parser):
        parser.add_argument('recipient', type=str, help='Email address to send test to')

    def handle(self, *args, **options):
        recipient = options['recipient']

        self.stdout.write(f'EMAIL_BACKEND: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}')
        self.stdout.write(f'SMTP configured: {is_smtp_configured()}')
        self.stdout.write(f'Using console: {using_console_email()}')

        if not is_smtp_configured():
            self.stdout.write(self.style.ERROR(
                '\nGmail is NOT configured. Run:\n  python manage.py configure_email\n'
            ))
            return

        try:
            send_mail(
                subject='EcoLearn - Test Email',
                message='If you see this in your Gmail app, email is working correctly!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f'Test email sent to {recipient}. Check your Gmail app!'))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f'Failed: {exc}'))
            self.stdout.write('Run: python manage.py configure_email')
