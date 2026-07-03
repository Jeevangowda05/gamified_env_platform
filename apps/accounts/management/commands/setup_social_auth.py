import os

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = 'Configure Google/Facebook OAuth from .env variables'

    def handle(self, *args, **options):
        site = Site.objects.get_current()
        self.stdout.write(f'Site: {site.domain}')

        google_id = getattr(settings, 'GOOGLE_CLIENT_ID', '') or os.environ.get('GOOGLE_CLIENT_ID', '')
        google_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', '') or os.environ.get('GOOGLE_CLIENT_SECRET', '')
        facebook_id = getattr(settings, 'FACEBOOK_APP_ID', '') or os.environ.get('FACEBOOK_APP_ID', '')
        facebook_secret = getattr(settings, 'FACEBOOK_APP_SECRET', '') or os.environ.get('FACEBOOK_APP_SECRET', '')

        if google_id and google_secret:
            app, created = SocialApp.objects.update_or_create(
                provider='google',
                defaults={
                    'name': 'Google',
                    'client_id': google_id,
                    'secret': google_secret,
                },
            )
            app.sites.set([site.pk])
            self.stdout.write(self.style.SUCCESS(
                f'Google OAuth {"created" if created else "updated"} successfully.'
            ))
            self.stdout.write(
                f'  Redirect URI: {settings.SITE_PROTOCOL}://{settings.SITE_DOMAIN}'
                f'/accounts/auth/google/login/callback/'
            )
        else:
            self.stdout.write(self.style.WARNING(
                'Google: Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env'
            ))

        if facebook_id and facebook_secret:
            app, created = SocialApp.objects.update_or_create(
                provider='facebook',
                defaults={
                    'name': 'Facebook',
                    'client_id': facebook_id,
                    'secret': facebook_secret,
                },
            )
            app.sites.set([site.pk])
            self.stdout.write(self.style.SUCCESS(
                f'Facebook OAuth {"created" if created else "updated"} successfully.'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                'Facebook: Set FACEBOOK_APP_ID and FACEBOOK_APP_SECRET in .env'
            ))

        email_user = getattr(settings, 'EMAIL_HOST_USER', '')
        if email_user:
            self.stdout.write(self.style.SUCCESS(f'Email SMTP configured: {email_user}'))
        else:
            self.stdout.write(self.style.WARNING(
                'Email: Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env to send real emails'
            ))
