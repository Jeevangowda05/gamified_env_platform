"""Email configuration helpers."""

from django.conf import settings

PLACEHOLDER_MARKERS = (
    'your-email',
    'your-gmail',
    'your-app-password',
    'example.com',
    'changeme',
)


def _is_placeholder(value):
    if not value:
        return True
    lowered = value.strip().lower()
    return any(marker in lowered for marker in PLACEHOLDER_MARKERS)


def is_smtp_configured():
    user = getattr(settings, 'EMAIL_HOST_USER', '')
    password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
    return not _is_placeholder(user) and not _is_placeholder(password)


def using_console_email():
    backend = getattr(settings, 'EMAIL_BACKEND', '')
    return 'console' in backend


def email_setup_hint():
    return (
        'Real email is not configured. Run: python manage.py configure_email '
        'then restart the server.'
    )
