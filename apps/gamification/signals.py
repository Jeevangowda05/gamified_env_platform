from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.db import models
from .models import PointTransaction, UserProgress


@receiver(post_delete, sender=PointTransaction)
def update_user_points_on_delete(sender, instance, **kwargs):
    """
    Automatically update UserProgress and user points when a PointTransaction is deleted.
    """
    user = instance.user

    # Recalculate points from all transactions still present!
    total_points = PointTransaction.objects.filter(user=user).aggregate(total=models.Sum('points'))['total'] or 0

    # Update UserProgress model
    progress, created = UserProgress.objects.get_or_create(user=user)
    progress.total_points = total_points
    progress.quiz_points = PointTransaction.objects.filter(user=user, related_content_type='quiz').aggregate(q=models.Sum('points'))['q'] or 0
    progress.course_points = PointTransaction.objects.filter(user=user, related_content_type='course').aggregate(c=models.Sum('points'))['c'] or 0
    progress.save()

    # Optionally update user main model if you want to sync (if total_points also tracked here)
    user.total_points = total_points
    user.save()
