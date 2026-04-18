"""
Admin configuration for accounts app
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User Admin"""

    inlines = (UserProfileInline,)
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'level', 'total_points', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_active', 'is_staff', 'level', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name', 'institution')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'avatar', 'bio', 'date_of_birth')}),
        (_('Educational info'), {'fields': ('user_type', 'institution', 'grade_level')}),
        (_('Gamification'), {'fields': ('total_points', 'level', 'experience_points', 'last_login_streak')}),
        (_('Activity'), {'fields': ('total_lessons_completed', 'total_quizzes_taken')}),
        (_('Preferences'), {'fields': ('preferred_language', 'notifications_enabled')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'user_type'),
        }),
    )

    readonly_fields = ('date_joined', 'last_login', 'total_lessons_completed', 'total_quizzes_taken')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'learning_style', 'badges_earned', 'certificates_earned', 'is_public_profile')
    list_filter = ('learning_style', 'is_public_profile', 'allow_friend_requests')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('badges_earned', 'certificates_earned', 'created_at', 'updated_at')
