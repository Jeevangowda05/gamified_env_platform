"""
Admin configuration for core app
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db import models
from .models import (
    SiteConfiguration, ContactMessage, NewsletterSubscription,
    Course, Topic, Module, Lesson, Enrollment, LessonProgress, Certificate
)


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'maintenance_mode', 'registration_enabled', 'updated_at')
    list_filter = ('maintenance_mode', 'registration_enabled')
    fieldsets = (
        ('Site Settings', {
            'fields': ('site_name', 'site_description', 'maintenance_mode', 'registration_enabled')
        }),
        ('Gamification Settings', {
            'fields': ('points_per_lesson', 'points_per_quiz', 'daily_login_bonus')
        }),
    )

    def has_add_permission(self, request):
        # Only allow one configuration instance
        return not SiteConfiguration.objects.exists()


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'is_read', 'is_replied', 'created_at')
    list_filter = ('is_read', 'is_replied', 'created_at')
    search_fields = ('name', 'email', 'subject')
    readonly_fields = ('created_at',)
    actions = ['mark_as_read', 'mark_as_replied']

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = "Mark selected messages as read"

    def mark_as_replied(self, request, queryset):
        queryset.update(is_replied=True)
    mark_as_replied.short_description = "Mark selected messages as replied"


@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_active', 'subscribed_at')
    list_filter = ('is_active', 'subscribed_at')
    search_fields = ('email',)
    readonly_fields = ('subscribed_at',)
    actions = ['activate_subscriptions', 'deactivate_subscriptions']

    def activate_subscriptions(self, request, queryset):
        queryset.update(is_active=True)
    activate_subscriptions.short_description = "Activate selected subscriptions"

    def deactivate_subscriptions(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_subscriptions.short_description = "Deactivate selected subscriptions"


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['name', 'difficulty_level', 'background_color_display', 'get_course_count', 'is_active', 'order']
    list_filter = ['difficulty_level', 'is_active']
    search_fields = ['name', 'description']
    list_editable = ['order']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Display Settings', {
            'fields': ('icon', 'background_color', 'difficulty_level')
        }),
        ('Status & Ordering', {
            'fields': ('is_active', 'order')
        }),
    )
    
    def background_color_display(self, obj):
        """Display color preview"""
        return format_html(
            '<span style="background-color: {}; padding: 3px 10px; border-radius: 3px; color: white;">{}</span>',
            obj.background_color,
            obj.get_background_color_display()
        )
    background_color_display.short_description = 'Color'


class LessonInline(admin.TabularInline):
    """Inline admin for Lessons inside Module"""
    model = Lesson
    extra = 1
    fields = (
        'title', 
        'lesson_type', 
        'video_status_display',
        'duration_minutes',
        'points_value',
        'order'
    )
    readonly_fields = ('video_status_display',)
    
    def video_status_display(self, obj):
        """Show video availability"""
        if obj.video_file and obj.video_url:
            return format_html(
                '<span style="color: #00A651; background: #f0f9f7; padding: 5px 10px; '
                'border-radius: 3px; font-weight: bold;">'
                '<i class="fas fa-check-circle"></i> Both</span>'
            )
        elif obj.video_file:
            return format_html(
                '<span style="color: #FF6B00; background: #fff5f0; padding: 5px 10px; '
                'border-radius: 3px;"><i class="fas fa-file-video"></i> File</span>'
            )
        elif obj.video_url:
            return format_html(
                '<span style="color: #0066cc; background: #f0f5ff; padding: 5px 10px; '
                'border-radius: 3px;"><i class="fas fa-video"></i> YouTube</span>'
            )
        return '—'
    video_status_display.short_description = 'Video Status'


class ModuleInline(admin.TabularInline):
    """Inline admin for Modules inside Course"""
    model = Module
    extra = 1
    fields = ('title', 'order')


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """
    Comprehensive Lesson admin with support for:
    - YouTube URLs
    - Downloaded video files
    - Text, Quiz, Assignment, Practical content
    """
    
    fieldsets = (
        ('📚 Basic Information', {
            'fields': (
                'module',
                'title',
                'lesson_type',
                'order'
            )
        }),
        ('📝 Content', {
            'fields': ('content',),
            'description': 'Add lesson content (text, instructions, etc.)',
            'classes': ('collapse',)
        }),
        ('🎥 VIDEO - Option 1: YouTube URL', {
            'fields': (
                'video_url',
                'video_url_display'
            ),
            'description': 'Paste a YouTube embed URL here as an alternative to uploading a file',
            'classes': ('collapse',)
        }),
        ('📤 VIDEO - Option 2: Upload File', {
            'fields': (
                'video_file',
                'video_file_display'
            ),
            'description': 'Upload a downloaded video file from your system (MP4, WebM, OGG supported)',
            'classes': ('collapse',)
        }),
        ('⏱️ Video Metadata', {
            'fields': (
                'duration_minutes',
                'points_value'
            ),
            'description': 'Set video duration in minutes and points for completion'
        }),
        ('📊 Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = (
        'created_at',
        'updated_at',
        'video_url_display',
        'video_file_display'
    )
    
    list_display = (
        'title',
        'module',
        'lesson_type',
        'video_status',
        'duration_minutes',
        'points_value',
        'order'
    )
    
    list_filter = ('lesson_type', 'module__course', 'created_at')
    search_fields = ('title', 'content', 'module__title')
    ordering = ('module', 'order')
    
    def video_url_display(self, obj):
        """Display current YouTube URL with link"""
        if obj.video_url:
            return format_html(
                '<div style="word-break: break-all; background: #f0f5ff; padding: 10px; border-radius: 4px;">'
                '<strong style="color: #0066cc;">Current YouTube URL:</strong><br>'
                '<code style="background: white; padding: 5px; border-radius: 3px; display: inline-block; '
                'margin-top: 5px;">{}</code><br>'
                '<a href="{}" target="_blank" style="color: #0066cc; text-decoration: underline; margin-top: 5px; '
                'display: inline-block;"><i class="fas fa-external-link-alt"></i> Open video</a>'
                '</div>',
                obj.video_url,
                obj.video_url
            )
        return format_html(
            '<span style="color: #999; padding: 10px; background: #f9f9f9; border-radius: 4px; display: inline-block;">'
            '<i class="fas fa-info-circle"></i> No YouTube URL added yet</span>'
        )
    video_url_display.short_description = 'Current YouTube URL'
    
    def video_file_display(self, obj):
        """Display current video file with download and play options"""
        if obj.video_file:
            file_name = obj.get_video_display_name()
            return format_html(
                '<div style="background: #f9fff5; padding: 10px; border-radius: 4px; border-left: 3px solid #00A651;">'
                '<strong style="color: #00A651;"><i class="fas fa-check-circle"></i> Video File Uploaded</strong><br>'
                '<span style="font-size: 0.9em; color: #666;">File: <code>{}</code></span><br>'
                '<a href="{}" target="_blank" style="color: #00A651; text-decoration: underline; margin-right: 10px; '
                'display: inline-block; margin-top: 5px;"><i class="fas fa-download"></i> Download</a> | '
                '<a href="{}" style="color: #0066cc; text-decoration: underline; display: inline-block;">'
                '<i class="fas fa-play-circle"></i> Play</a>'
                '</div>',
                file_name,
                obj.video_file.url,
                obj.video_file.url
            )
        return format_html(
            '<span style="color: #999; padding: 10px; background: #f9f9f9; border-radius: 4px; display: inline-block;">'
            '<i class="fas fa-info-circle"></i> No video file uploaded yet</span>'
        )
    video_file_display.short_description = 'Current Video File'
    
    def video_status(self, obj):
        """Show comprehensive video availability status"""
        if obj.video_file and obj.video_url:
            return format_html(
                '<span style="color: #00A651; background: #f0f9f7; padding: 6px 12px; '
                'border-radius: 3px; font-weight: bold;">'
                '<i class="fas fa-check-double"></i> Both Available'
                '</span>'
            )
        elif obj.video_file:
            return format_html(
                '<span style="color: #FF6B00; background: #fff5f0; padding: 6px 12px; '
                'border-radius: 3px; font-weight: bold;">'
                '<i class="fas fa-file-video"></i> File Only'
                '</span>'
            )
        elif obj.video_url:
            return format_html(
                '<span style="color: #0066cc; background: #f0f5ff; padding: 6px 12px; '
                'border-radius: 3px; font-weight: bold;">'
                '<i class="fas fa-video"></i> YouTube Only'
                '</span>'
            )
        return format_html(
            '<span style="color: #999;">⚠ No Video</span>'
        )
    video_status.short_description = 'Video Status'


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'total_lessons', 'order')
    list_filter = ('course', 'course__topic')
    search_fields = ('title', 'course__title')
    list_editable = ('order',)
    inlines = [LessonInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('course', 'title', 'description')
        }),
        ('Organization', {
            'fields': ('order',)
        }),
    )
    
    def total_lessons(self, obj):
        count = obj.lessons.count()
        return format_html(
            '<span style="background: #0066cc; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count
        )
    total_lessons.short_description = 'Lessons'


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'topic',
        'total_modules',
        'total_lessons_display',
        'video_content_status',
        'duration',
        'completion_points',
        'created_at'
    )
    list_filter = ('topic', 'created_at')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ModuleInline]
    
    fieldsets = (
        ('📚 Course Information', {
            'fields': ('title', 'slug', 'description', 'topic')
        }),
        ('📊 Course Details', {
            'fields': (
                'duration',
                'completion_points',
                'thumbnail'
            )
        }),
    )
    
    readonly_fields = ()
    
    def total_modules(self, obj):
        count = obj.modules.count()
        return format_html(
            '<span style="background: #0066cc; color: white; padding: 3px 8px; border-radius: 3px;">{} Module{}</span>',
            count,
            's' if count != 1 else ''
        )
    total_modules.short_description = 'Modules'
    
    def total_lessons_display(self, obj):
        count = obj.total_lessons
        return format_html(
            '<span style="background: #00A651; color: white; padding: 3px 8px; border-radius: 3px;">{} Lesson{}</span>',
            count,
            's' if count != 1 else ''
        )
    total_lessons_display.short_description = 'Total Lessons'
    
    def video_content_status(self, obj):
        """Show if course has video content"""
        if obj.has_video_content:
            return format_html(
                '<span style="color: #FF6B00; background: #fff5f0; padding: 6px 12px; border-radius: 3px;">'
                '<i class="fas fa-video"></i> Video Content</span>'
            )
        return format_html(
            '<span style="color: #999;">Text Only</span>'
        )
    video_content_status.short_description = 'Content Type'


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'course',
        'enrolled_at',
        'progress_bar',
        'is_completed'
    )
    list_filter = ('is_completed', 'enrolled_at', 'course')
    search_fields = ('user__username', 'user__email', 'course__title')
    readonly_fields = ('enrolled_at', 'completed_at', 'progress_percentage')
    
    fieldsets = (
        ('Enrollment Information', {
            'fields': ('user', 'course', 'enrolled_at', 'completed_at')
        }),
        ('Status', {
            'fields': ('is_completed', 'progress_percentage')
        }),
    )
    
    def progress_bar(self, obj):
        """Display progress bar"""
        progress = obj.progress_percentage
        color = '#00A651' if progress >= 50 else '#FF6B00'
        return format_html(
            '<div style="width: 100px; height: 20px; background: #f0f0f0; border-radius: 10px; overflow: hidden;">'
            '<div style="width: {}%; height: 100%; background: {}; transition: width 0.3s;"></div>'
            '</div> {}%',
            progress,
            color,
            progress
        )
    progress_bar.short_description = 'Progress'


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'enrollment', 'is_completed', 'completed_at', 'watched_duration_display')
    list_filter = ('is_completed', 'completed_at', 'lesson__module__course')
    search_fields = ('lesson__title', 'enrollment__user__username')
    readonly_fields = ('completed_at',)
    
    def watched_duration_display(self, obj):
        """Display watched duration in readable format"""
        minutes = obj.watched_duration // 60
        seconds = obj.watched_duration % 60
        return f"{minutes}m {seconds}s"
    watched_duration_display.short_description = 'Time Watched'


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_id', 'user', 'course', 'issued_at')
    list_filter = ('issued_at', 'course')
    search_fields = ('user__username', 'course__title', 'certificate_id')
    readonly_fields = ('certificate_id', 'issued_at')
    
    fieldsets = (
        ('Certificate Information', {
            'fields': ('certificate_id', 'user', 'course', 'issued_at')
        }),
    )
