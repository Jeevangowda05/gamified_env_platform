"""
Gamification views for badges, leaderboards, and point management
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, ListView, DetailView
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import (
    Badge, BadgeCategory, UserBadge, PointTransaction, 
    LeaderboardEntry, Achievement, UserAchievement,
    UserProgress  # Added UserProgress import
)

# === ADDED: Helper for dynamic badge progress and stats access ===
def get_user_progress(user):
    """Return a progress-like object for the user."""
    if getattr(user, 'user_type', None) != 'student':
        class Dummy:
            total_points = 0
            quizzes_completed = 0
            quizzes_passed = 0
            courses_completed = 0
            current_streak = 0

            @staticmethod
            def get_level():
                return 0
        return Dummy()

    try:
        # Try to get UserProgress from gamification app
        progress, created = UserProgress.objects.get_or_create(user=user)
        return progress
    except:
        # Fallback for legacy setups
        class Dummy:
            total_points = getattr(user, "total_points", 0)
            quizzes_completed = getattr(user, "quizzes_completed", 0)
            quizzes_passed = getattr(user, "quizzes_passed", 0)
            courses_completed = getattr(user, "courses_completed", 0)
            current_streak = getattr(user, "current_streak", 0)
        return Dummy()

# =========================
#   Badge List View
# =========================

class BadgeListView(LoginRequiredMixin, TemplateView):
    """Display all available badges"""
    template_name = 'gamification/badges.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get all badge categories with their badges
        categories = BadgeCategory.objects.prefetch_related('badges').all()

        # Get user's earned badges
        user_badges = set(UserBadge.objects.filter(user=user).values_list('badge_id', flat=True))

        # Organize badges by category
        badge_categories = []
        for category in categories:
            category_badges = []
            for badge in category.badges.filter(is_active=True):
                badge_data = {
                    'badge': badge,
                    'is_earned': badge.id in user_badges,
                    # Use improved badge progress below:
                    'progress': self._calculate_badge_progress(user, badge),
                }
                category_badges.append(badge_data)

            if category_badges:
                badge_categories.append({
                    'category': category,
                    'badges': category_badges,
                })

        context['badge_categories'] = badge_categories

        # User badge statistics
        context['user_badge_stats'] = {
            'total_earned': len(user_badges),
            'total_available': Badge.objects.filter(is_active=True).count(),
        }

        # --- NEW: user global progress for stat cards etc (doesn't break anything if you don't use) ---
        context['user_progress'] = get_user_progress(user)

        return context

    # Extended progress: points, quizzes_completed, quizzes_passed, courses_completed, current_streak
    def _calculate_badge_progress(self, user, badge):
        progress = get_user_progress(user)
        reqs = []
        if hasattr(badge, "required_points") and badge.required_points > 0:
            reqs.append(min(progress.total_points / badge.required_points, 1.0))
        if hasattr(badge, "quizzes_required") and badge.quizzes_required > 0:
            reqs.append(min(getattr(progress, "quizzes_completed", 0) / badge.quizzes_required, 1.0))
        if hasattr(badge, "quizzes_passed_required") and badge.quizzes_passed_required > 0:
            reqs.append(min(getattr(progress, "quizzes_passed", 0) / badge.quizzes_passed_required, 1.0))
        if hasattr(badge, "courses_required") and badge.courses_required > 0:
            reqs.append(min(getattr(progress, "courses_completed", 0) / badge.courses_required, 1.0))
        if hasattr(badge, "streak_required") and badge.streak_required > 0:
            reqs.append(min(getattr(progress, "current_streak", 0) / badge.streak_required, 1.0))
        if not reqs:
            return 0
        return int(sum(reqs) / len(reqs) * 100)

# =========================
#   ADDED: Simple Function-Based Badge View (Alternative)
# =========================

@login_required
def badges_view(request):
    """Function-based view for badges - alternative to class-based view"""
    # Get or create user progress
    progress, created = UserProgress.objects.get_or_create(user=request.user)
    
    # Get badge categories with their badges
    categories = BadgeCategory.objects.prefetch_related('badges').all()
    
    # Get user's earned badges
    earned_badges = UserBadge.objects.filter(user=request.user).select_related('badge')
    earned_badge_ids = set(earned_badges.values_list('badge_id', flat=True))
    
    # Calculate badge stats
    total_badges = Badge.objects.filter(is_active=True).count()
    earned_count = earned_badges.count()
    
    context = {
        'categories': categories,
        'earned_badges': earned_badge_ids,
        'total_badges': total_badges,
        'earned_count': earned_count,
        'user_progress': progress,
    }
    
    return render(request, 'gamification/badges.html', context)

# =========================
#   Badge Detail View
# =========================

class BadgeDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a specific badge"""
    model = Badge
    template_name = 'gamification/badge_detail.html'
    context_object_name = 'badge'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        badge = self.object
        user = self.request.user

        # Check if user has earned this badge
        try:
            user_badge = UserBadge.objects.get(user=user, badge=badge)
            context['user_badge'] = user_badge
            context['is_earned'] = True
        except UserBadge.DoesNotExist:
            context['is_earned'] = False

        context['progress'] = self._calculate_badge_progress(user, badge)

        context['recent_earners'] = UserBadge.objects.filter(
            badge=badge
        ).select_related('user').order_by('-earned_at')[:10]

        return context

    def _calculate_badge_progress(self, user, badge):
        # Can use the same logic as above for consistency or keep it per original UI
        progress = get_user_progress(user)
        reqs = []
        if hasattr(badge, "required_points") and badge.required_points > 0:
            reqs.append(min(progress.total_points / badge.required_points, 1.0))
        if hasattr(badge, "quizzes_required") and badge.quizzes_required > 0:
            reqs.append(min(getattr(progress, "quizzes_completed", 0) / badge.quizzes_required, 1.0))
        if hasattr(badge, "quizzes_passed_required") and badge.quizzes_passed_required > 0:
            reqs.append(min(getattr(progress, "quizzes_passed", 0) / badge.quizzes_passed_required, 1.0))
        if hasattr(badge, "courses_required") and badge.courses_required > 0:
            reqs.append(min(getattr(progress, "courses_completed", 0) / badge.courses_required, 1.0))
        if hasattr(badge, "streak_required") and badge.streak_required > 0:
            reqs.append(min(getattr(progress, "current_streak", 0) / badge.streak_required, 1.0))
        if not reqs:
            return 0
        return int(sum(reqs) / len(reqs) * 100)

# =========================
#   Point History View
# =========================

class PointHistoryView(LoginRequiredMixin, TemplateView):
    """Display user's point transaction history"""
    template_name = 'gamification/point_history.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Pull all real transactions (not fake data)
        transactions = PointTransaction.objects.filter(user=user).order_by('-created_at')[:50]
        context['transactions'] = transactions

        # Calculate totals using actual transaction objects
        earned_points = PointTransaction.objects.filter(
            user=user, 
            transaction_type='earned'
        ).aggregate(total=Sum('points'))['total'] or 0

        bonus_points = PointTransaction.objects.filter(
            user=user, 
            transaction_type='bonus'
        ).aggregate(total=Sum('points'))['total'] or 0

        # Use real user progress object for point stats
        progress = get_user_progress(user)
        context['point_stats'] = {
            'total_points': progress.total_points,
            'earned_points': earned_points,
            'bonus_points': bonus_points,
            'transactions_count': transactions.count(),
        }
        # Add additional breakdown (useful for dashboard chart)
        context['point_breakdown'] = {
            'course_points': progress.course_points,
            'quiz_points': progress.quiz_points,
            'total_points': progress.total_points,
        }
        return context

# =========================
#   API Views
# =========================

class BadgeListAPIView(generics.ListAPIView):
    """API endpoint to list all badges"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        categories = BadgeCategory.objects.prefetch_related('badges').all()
        user_badges = set(UserBadge.objects.filter(user=user).values_list('badge_id', flat=True))

        data = []
        for category in categories:
            category_data = {
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'icon': category.icon,
                'color': category.color,
                'badges': []
            }
            for badge in category.badges.filter(is_active=True):
                progress = get_user_progress(user)
                total_pct = 0
                reqs = []
                if hasattr(badge, "required_points") and badge.required_points > 0:
                    reqs.append(min(progress.total_points / badge.required_points, 1.0))
                if hasattr(badge, "quizzes_required") and badge.quizzes_required > 0:
                    reqs.append(min(getattr(progress, "quizzes_completed", 0) / badge.quizzes_required, 1.0))
                if hasattr(badge, "quizzes_passed_required") and badge.quizzes_passed_required > 0:
                    reqs.append(min(getattr(progress, "quizzes_passed", 0) / badge.quizzes_passed_required, 1.0))
                if hasattr(badge, "courses_required") and badge.courses_required > 0:
                    reqs.append(min(getattr(progress, "courses_completed", 0) / badge.courses_required, 1.0))
                if hasattr(badge, "streak_required") and badge.streak_required > 0:
                    reqs.append(min(getattr(progress, "current_streak", 0) / badge.streak_required, 1.0))
                if reqs:
                    total_pct = int(sum(reqs) / len(reqs) * 100)
                badge_data = {
                    'id': badge.id,
                    'name': badge.name,
                    'description': badge.description,
                    'badge_type': badge.badge_type,
                    'rarity': badge.rarity,
                    'points_reward': getattr(badge, 'points_reward', 0),
                    'is_earned': badge.id in user_badges,
                    'required_points': getattr(badge, 'required_points', 0),
                    'user_progress': total_pct,
                }
                category_data['badges'].append(badge_data)
            if category_data['badges']:
                data.append(category_data)

        return Response(data)

class LeaderboardAPIView(APIView):
    """API endpoint for leaderboard data"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        leaderboard_type = request.GET.get('type', 'weekly')
        limit = int(request.GET.get('limit', 50))

        # UPDATED: Use UserProgress for leaderboard ranking
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Get users with their progress
        users_with_progress = []
        users = User.objects.filter(is_active=True, user_type='student', show_on_leaderboard=True)
        
        for user in users:
            progress = get_user_progress(user)
            users_with_progress.append({
                'user': user,
                'total_points': progress.total_points
            })
        
        # Sort by points and limit
        users_with_progress.sort(key=lambda x: x['total_points'], reverse=True)
        users_with_progress = users_with_progress[:limit]

        leaderboard_data = []
        for rank, user_data in enumerate(users_with_progress, 1):
            user = user_data['user']
            progress = get_user_progress(user)
            user_info = {
                'rank': rank,
                'user_id': user.id,
                'username': user.username,
                'full_name': getattr(user, 'get_full_name', lambda: user.username)(),
                'points': progress.total_points,
                'level': progress.get_level() if hasattr(progress, 'get_level') else 1,
                'institution': getattr(user, 'institution', ''),
            }
            leaderboard_data.append(user_info)

        # Get current user's position
        user_rank_data = None
        for entry in leaderboard_data:
            if entry['user_id'] == request.user.id:
                user_rank_data = {
                    'rank': entry['rank'],
                    'points': entry['points'],
                }
                break

        return Response({
            'leaderboard': leaderboard_data,
            'user_position': user_rank_data,
            'type': leaderboard_type,
            'total_participants': len(leaderboard_data)
        })

# =========================
#   ADDED: Dashboard View (Bonus)
# =========================

@login_required
def dashboard_view(request):
    """Dashboard view showing user's gamification stats"""
    progress = get_user_progress(request.user)
    
    # Get recent earned badges
    recent_badges = UserBadge.objects.filter(
        user=request.user
    ).select_related('badge').order_by('-earned_at')[:5]
    
    # Get progress on next badge
    next_badge = None
    all_badges = Badge.objects.filter(is_active=True)
    earned_badge_ids = set(UserBadge.objects.filter(user=request.user).values_list('badge_id', flat=True))
    
    for badge in all_badges:
        if badge.id not in earned_badge_ids:
            next_badge = badge
            break
    
    context = {
        'user_progress': progress,
        'recent_badges': recent_badges,
        'next_badge': next_badge,
        'total_earned_badges': len(earned_badge_ids),
        'total_available_badges': all_badges.count(),
    }
    
    return render(request, 'gamification/dashboard.html', context)
