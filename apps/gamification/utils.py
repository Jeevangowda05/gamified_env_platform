"""
Utility functions for gamification system
"""
from django.utils import timezone
from .models import PointTransaction, UserProgress


def award_points(user, points, reason, content_type='', object_id='', transaction_type='earned'):
    """
    Award points to a user and create a transaction record
    """
    if getattr(user, 'user_type', None) != 'student':
        return None

    # Create the transaction record
    transaction = PointTransaction.objects.create(
        user=user,
        transaction_type=transaction_type,
        points=points,
        reason=reason,
        related_content_type=content_type,
        related_object_id=str(object_id)
    )
    
    # Update user progress
    progress, created = UserProgress.objects.get_or_create(user=user)
    progress.total_points += points
    
    # Update specific point categories
    if content_type == 'course':
        progress.course_points += points
    elif content_type == 'quiz':
        progress.quiz_points += points
    
    progress.update_streak()
    progress.save()
    
    # Check for badge eligibility
    progress.check_badge_eligibility()
    
    return transaction
