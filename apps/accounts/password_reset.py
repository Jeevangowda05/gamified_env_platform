"""Two-step password reset with email OTP verification."""

import random
import string

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string

OTP_TTL = 600
OTP_LENGTH = 6
MAX_ATTEMPTS = 5


def generate_otp():
    return ''.join(random.choices(string.digits, k=OTP_LENGTH))


def mask_email(email):
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        masked_local = local[0] + '*'
    else:
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
    return f'{masked_local}@{domain}'


def mask_phone(phone):
    if not phone:
        return None
    digits = ''.join(c for c in phone if c.isdigit())
    if len(digits) < 4:
        return None
    return f'***-***-{digits[-4:]}'


def _otp_cache_key(user_id):
    return f'pwd_reset_otp:{user_id}'


def _attempts_cache_key(user_id):
    return f'pwd_reset_attempts:{user_id}'


def _verified_cache_key(user_id):
    return f'pwd_reset_verified:{user_id}'


def send_password_reset_otp(user):
    otp = generate_otp()
    cache.set(_otp_cache_key(user.id), otp, OTP_TTL)
    cache.delete(_attempts_cache_key(user.id))

    context = {
        'user': user,
        'otp': otp,
        'expiry_minutes': OTP_TTL // 60,
        'site_name': 'EcoLearn Platform',
    }
    subject = render_to_string('accounts/password_reset_otp_subject.txt', context).strip()
    message = render_to_string('accounts/password_reset_otp_email.txt', context)

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return otp


def verify_otp(user_id, otp):
    attempts = cache.get(_attempts_cache_key(user_id), 0)
    if attempts >= MAX_ATTEMPTS:
        return False, 'Too many failed attempts. Please request a new code.'

    stored = cache.get(_otp_cache_key(user_id))
    if not stored:
        return False, 'Verification code has expired. Please request a new one.'

    if stored != otp.strip():
        cache.set(_attempts_cache_key(user_id), attempts + 1, OTP_TTL)
        remaining = MAX_ATTEMPTS - (attempts + 1)
        if remaining <= 0:
            cache.delete(_otp_cache_key(user_id))
            return False, 'Too many failed attempts. Please request a new code.'
        return False, f'Invalid code. {remaining} attempt(s) remaining.'

    cache.delete(_otp_cache_key(user_id))
    cache.delete(_attempts_cache_key(user_id))
    cache.set(_verified_cache_key(user_id), True, OTP_TTL)
    return True, ''


def is_verified(user_id):
    return cache.get(_verified_cache_key(user_id)) is True


def clear_verification(user_id):
    cache.delete(_verified_cache_key(user_id))
    cache.delete(_otp_cache_key(user_id))
    cache.delete(_attempts_cache_key(user_id))
