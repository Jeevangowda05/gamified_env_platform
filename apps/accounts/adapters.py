"""
Custom adapters for django-allauth social authentication.
"""

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()


class EcoLearnAccountAdapter(DefaultAccountAdapter):
    pass


class EcoLearnSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        if not user.username:
            email = data.get('email', '')
            base_username = email.split('@')[0] if email else 'user'
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f'{base_username}{counter}'
                counter += 1
            user.username = username
        if not user.first_name:
            user.first_name = data.get('first_name', '') or data.get('name', '').split()[0] if data.get('name') else ''
        if not user.last_name:
            parts = data.get('name', '').split() if data.get('name') else []
            user.last_name = data.get('last_name', '') or (' '.join(parts[1:]) if len(parts) > 1 else '')
        user.user_type = user.user_type or 'student'
        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        if not user.user_type:
            user.user_type = 'student'
            user.save(update_fields=['user_type'])
        return user
