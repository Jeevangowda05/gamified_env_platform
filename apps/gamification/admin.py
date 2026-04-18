"""
Admin configuration for gamification app
"""

from django.contrib import admin
from .models import (
    BadgeCategory, Badge, UserBadge, PointTransaction, 
    LeaderboardEntry, Achievement, UserAchievement,
    UserProgress
)


@admin.register(BadgeCategory)
class BadgeCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'color', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'category', 'badge_type', 'rarity', 'points_reward', 'is_active'
    )
    list_filter = ('category', 'badge_type', 'rarity', 'is_active', 'is_hidden')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'earned_count')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'badge_type')
        }),
        ('Visual Design', {
            'fields': ('icon', 'icon_class', 'rarity')
        }),
        ('Requirements', {
            'fields': (
                'required_points', 
                'required_actions', 
                'required_streak',
                'quizzes_required', 
                'courses_required', 
                'quizzes_passed_required', 
                'streak_required'
            )
        }),
        ('Rewards & Status', {
            'fields': ('points_reward', 'is_active', 'is_hidden')
        }),
        ('Statistics', {
            'fields': ('earned_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'earned_at', 'is_showcased')
    list_filter = ('badge__category', 'badge__rarity', 'is_showcased', 'earned_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'badge__name')
    readonly_fields = ('earned_at',)


@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'points', 'reason', 'created_at')
    list_filter = ('transaction_type', 'created_at', 'related_content_type')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'reason')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'


@admin.register(LeaderboardEntry)
class LeaderboardEntryAdmin(admin.ModelAdmin):
    list_display = ('rank', 'user', 'leaderboard_type', 'points', 'institution', 'updated_at')
    list_filter = ('leaderboard_type', 'institution', 'period_start', 'period_end')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ['leaderboard_type', 'rank']


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('name', 'points_reward', 'is_active', 'is_rare', 'created_at')
    list_filter = ('is_active', 'is_rare', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'criteria')
        }),
        ('Visual & Rewards', {
            'fields': ('icon', 'color', 'points_reward')
        }),
        ('Status', {
            'fields': ('is_active', 'is_rare')
        }),
    )


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'achievement', 'is_completed', 'completed_at', 'updated_at')
    list_filter = ('is_completed', 'completed_at', 'achievement__is_rare')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'achievement__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_points', 'quizzes_completed', 'courses_completed', 'challenges_completed', 'current_streak')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('updated_at',)
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Points Tracking', {
            'fields': ('total_points', 'quiz_points', 'course_points', 'challenge_points')
        }),
        ('Activity', {
            'fields': ('quizzes_completed', 'quizzes_passed', 'courses_completed', 'challenges_completed')
        }),
        ('Streaks', {
            'fields': ('current_streak', 'longest_streak', 'last_activity_date')
        }),
        ('Metadata', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )


# Admin customizations
admin.site.site_header = "EcoLearn Platform Administration"
admin.site.site_title = "EcoLearn Admin"
admin.site.index_title = "Platform Management"
