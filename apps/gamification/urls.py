"""
URL configuration for gamification app
"""

from django.urls import path
from . import views

app_name = 'gamification'

urlpatterns = [
    # Badge URLs (FIXED - removed duplicate)
    path('badges/', views.badges_view, name='badges'),  # Use ONLY function-based view
    path('badges/<int:pk>/', views.BadgeDetailView.as_view(), name='badge_detail'),
    
    # Point URLs
    path('points/', views.PointHistoryView.as_view(), name='point_history'),

    # API URLs
    path('api/badges/', views.BadgeListAPIView.as_view(), name='badges_api'),
    path('api/leaderboard/', views.LeaderboardAPIView.as_view(), name='leaderboard_api'),
]
