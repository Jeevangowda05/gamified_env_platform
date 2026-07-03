import getpass
import re
from pathlib import Path

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Configure Gmail SMTP so password-reset emails arrive in your Gmail app'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Gmail address to send from')
        parser.add_argument('--password', type=str, help='Gmail App Password (16 chars)')
        parser.add_argument('--test-to', type=str, help='Send a test email to this address')

    def handle(self, *args, **options):
        env_path = Path(settings.BASE_DIR) / '.env'
        if not env_path.exists():
            self.stdout.write(self.style.ERROR('.env file not found. Copy .env.example to .env first.'))
            return

        current_email = getattr(settings, 'EMAIL_HOST_USER', '').strip()
        default_email = current_email if re.match(r'^[^@]+@[^@]+\.[^@]+$', current_email or '') else 'jeevan30gowda@gmail.com'

        if options.get('email'):
            email = options['email'].strip()
        else:
            prompt = f'Gmail address [{default_email}]: '
            entered = input(prompt).strip()
            email = entered or default_email

        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            self.stdout.write(self.style.ERROR(f'Invalid email address: {email!r}'))
            self.stdout.write('Enter a full Gmail address like jeevan30gowda@gmail.com')
            return

        password = options.get('password')
        if not password:
            self.stdout.write('')
            self.stdout.write('Gmail App Password (NOT your normal Gmail password):')
            self.stdout.write('  1. Go to https://myaccount.google.com/apppasswords')
            self.stdout.write('  2. Create an app password for "Mail"')
            self.stdout.write('  3. Paste the 16-character password below')
            self.stdout.write('')
            password = getpass.getpass('App Password: ').strip().replace(' ', '')

        if len(password) < 16:
            self.stdout.write(self.style.WARNING('App passwords are usually 16 characters. Continuing anyway...'))

        content = env_path.read_text(encoding='utf-8')
        content = self._set_env_value(content, 'EMAIL_HOST', 'smtp.gmail.com')
        content = self._set_env_value(content, 'EMAIL_PORT', '587')
        content = self._set_env_value(content, 'EMAIL_USE_TLS', 'True')
        content = self._set_env_value(content, 'EMAIL_HOST_USER', email)
        content = self._set_env_value(content, 'EMAIL_HOST_PASSWORD', password)
        content = self._set_env_value(content, 'DEFAULT_FROM_EMAIL', f'EcoLearn Platform <{email}>')
        env_path.write_text(content, encoding='utf-8')

        self.stdout.write(self.style.SUCCESS(f'\nSaved Gmail settings to {env_path}'))
        self.stdout.write(self.style.WARNING('Restart your Django server for changes to take effect.\n'))

        test_to = options.get('test_to') or email
        if input(f'Send test email to {test_to}? [Y/n]: ').strip().lower() in ('', 'y', 'yes'):
            self._send_test(email, password, test_to)

    def _set_env_value(self, content, key, value):
        pattern = rf'^{re.escape(key)}=.*$'
        replacement = f'{key}={value}'
        if re.search(pattern, content, flags=re.MULTILINE):
            return re.sub(pattern, replacement, content, flags=re.MULTILINE)
        return content.rstrip() + f'\n{replacement}\n'

    def _send_test(self, from_email, app_password, to_email):
        import smtplib
        from email.mime.text import MIMEText

        msg = MIMEText(
            'EcoLearn email is working! Password reset codes will now arrive in your Gmail app.'
        )
        msg['Subject'] = 'EcoLearn - Email Test Successful'
        msg['From'] = f'EcoLearn Platform <{from_email}>'
        msg['To'] = to_email

        try:
            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(from_email, app_password)
                server.sendmail(from_email, [to_email], msg.as_string())
            self.stdout.write(self.style.SUCCESS(f'Test email sent to {to_email}. Check your Gmail app!'))
        except smtplib.SMTPAuthenticationError:
            self.stdout.write(self.style.ERROR(
                'Gmail rejected the login. Use an App Password, not your normal password.\n'
                'Create one at: https://myaccount.google.com/apppasswords'
            ))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f'Failed to send test email: {exc}'))
