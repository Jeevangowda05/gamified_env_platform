"""
URL configuration for core app
"""

from django.urls import path
from . import views
from .views import PublicProfileView
app_name = 'core'

urlpatterns = [
    # Main pages
    path('', views.HomeView.as_view(), name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('leaderboard/', views.LeaderboardView.as_view(), name='leaderboard'),

    # API endpoints
    path('api/dashboard/stats/', views.DashboardStatsAPIView.as_view(), name='dashboard_stats_api'),
    path('api/activity/', views.UserActivityAPIView.as_view(), name='user_activity_api'),
    path('api/notifications/', views.NotificationAPIView.as_view(), name='notifications_api'),

       # ... your existing URLs ...
    path('courses/', views.course_list, name='course_list'),
    path('course/<slug:slug>/', views.course_detail, name='course_detail'),
    path('course/<slug:slug>/enroll/', views.enroll_course, name='enroll_course'),
    path('course/<slug:slug>/learn/', views.course_learn, name='course_learn'),
    path('course/<slug:slug>/lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('course/<slug:slug>/lesson/<int:lesson_id>/complete/', views.complete_lesson, name='complete_lesson'),
    path('course/<slug:slug>/lesson/<int:lesson_id>/complete/api/', views.complete_lesson_api, name='complete_lesson_api'),
    path('course/<slug:slug>/certificate/', views.course_certificate, name='course_certificate'),  # For course details
    path('course/<slug:slug>/lesson/<int:lesson_id>/quiz/', views.submit_quiz, name='submit_quiz'),
    path('topics/', views.topic_list, name='topic_list'),
    path('topic/<slug:slug>/', views.topic_detail, name='topic_detail'),
    # Utility endpoints
    path('health/', views.health_check, name='health_check'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('user/<str:username>/', PublicProfileView.as_view(), name='public_profile'),
]
