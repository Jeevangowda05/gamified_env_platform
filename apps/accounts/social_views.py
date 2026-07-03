"""
Social authentication views with configuration checks.
"""

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.providers.google.views import oauth2_login as google_oauth2_login
from allauth.socialaccount.providers.facebook.views import oauth2_login as facebook_oauth2_login


def _provider_configured(provider):
    if SocialApp.objects.filter(provider=provider).exists():
        return True
    providers = getattr(settings, 'SOCIALACCOUNT_PROVIDERS', {})
    app = providers.get(provider, {}).get('APP', {})
    return bool(app.get('client_id') and app.get('secret'))


def _setup_help_message(provider):
    return (
        f'{provider.title()} login is not configured. '
        f'Add {provider.upper()}_CLIENT_ID and {provider.upper()}_CLIENT_SECRET to your .env file, '
        f'then run: python manage.py setup_social_auth'
    )


def google_login(request):
    if not _provider_configured('google'):
        messages.warning(request, _setup_help_message('google'))
        return redirect('accounts:login')
    return google_oauth2_login(request)


def facebook_login(request):
    if not _provider_configured('facebook'):
        messages.warning(request, _setup_help_message('facebook'))
        return redirect('accounts:login')
    return facebook_oauth2_login(request)
