from apps.gamification.models import UserProgress

def user_gamification(request):
    if request.user.is_authenticated:
        if getattr(request.user, 'user_type', None) != 'student':
            return {
                'user_level': 0,
                'user_points': 0,
                'user_badges': 0,
            }
        try:
            progress = UserProgress.objects.get(user=request.user)
            level = progress.get_level()
            points = progress.total_points
            # Get badges count (customize if using related name)
            badges = request.user.earned_badges.count() if hasattr(request.user, 'earned_badges') else 0
        except UserProgress.DoesNotExist:
            level = 1
            points = 0
            badges = 0
    else:
        level = 0
        points = 0
        badges = 0
    return {
        'user_level': level,
        'user_points': points,
        'user_badges': badges,
    }
