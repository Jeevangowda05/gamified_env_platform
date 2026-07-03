"""
Signals for accounts app
"""

from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from .models import User, UserProfile
from django.contrib.auth.signals import user_logged_in
from django.utils import timezone
from apps.gamification.models import UserProgress, PointTransaction


@receiver(post_migrate)
def ensure_site_domain(sender, **kwargs):
    if sender.name != 'apps.accounts':
        return
    try:
        from django.conf import settings
        from django.contrib.sites.models import Site

        domain = getattr(settings, 'SITE_DOMAIN', '127.0.0.1:8000')
        site, _ = Site.objects.get_or_create(
            pk=settings.SITE_ID,
            defaults={'domain': domain, 'name': 'EcoLearn Platform'},
        )
        if site.domain != domain or site.name != 'EcoLearn Platform':
            site.domain = domain
            site.name = 'EcoLearn Platform'
            site.save(update_fields=['domain', 'name'])
    except Exception:
        pass

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance)



@receiver(user_logged_in)
def give_daily_login_bonus(sender, user, request, **kwargs):
    if getattr(user, 'user_type', None) != 'student':
        return

    today = timezone.now().date()
    progress, _ = UserProgress.objects.get_or_create(user=user)

    if progress.last_login_bonus_date != today:
        # Award bonus points (e.g., 25)
        PointTransaction.objects.create(
            user=user,
            transaction_type='bonus',
            points=25,
            reason='Daily Login Bonus',
            related_content_type='login',
            related_object_id=''
        )
        progress.total_points += 25
        progress.last_login_bonus_date = today
        progress.save()
