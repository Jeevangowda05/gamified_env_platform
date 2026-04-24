"""
Core models for the platform
"""

import os

from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta


class Topic(models.Model):
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    COLOR_CHOICES = [
        ('#E53E3E', 'Red'),
        ('#DD6B20', 'Orange'), 
        ('#38A169', 'Green'),
        ('#805AD5', 'Purple'),
        ('#3182CE', 'Blue'),
        ('#319795', 'Teal'),
    ]

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, help_text="FontAwesome icon class (e.g., fas fa-thermometer-half)")
    background_color = models.CharField(max_length=7, choices=COLOR_CHOICES, default='#38A169')
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_course_count(self):
        return self.courses.count()

    def get_difficulty_display_icon(self):
        icons = {
            'beginner': 'fas fa-star',
            'intermediate': 'fas fa-star-half-alt', 
            'advanced': 'fas fa-crown'
        }
        return icons.get(self.difficulty_level, 'fas fa-star')


User = get_user_model()


class SiteConfiguration(models.Model):
    """Site-wide configuration settings"""

    site_name = models.CharField(max_length=100, default='EcoLearn Platform')
    site_logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    site_description = models.TextField(blank=True)
    maintenance_mode = models.BooleanField(default=False)
    registration_enabled = models.BooleanField(default=True)

    # Gamification settings
    points_per_lesson = models.IntegerField(default=50)
    points_per_quiz = models.IntegerField(default=100)
    daily_login_bonus = models.IntegerField(default=10)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site Configuration'
        verbose_name_plural = 'Site Configuration'

    def __str__(self):
        return self.site_name


class ContactMessage(models.Model):
    """Contact form messages"""

    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()

    # User association (if logged in)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    # Status
    is_read = models.BooleanField(default=False)
    is_replied = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject}"


class NewsletterSubscription(models.Model):
    """Newsletter subscription model"""

    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-subscribed_at']

    def __str__(self):
        return self.email


class Course(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    completion_points = models.PositiveIntegerField(default=150, help_text="Points awarded for completing this course")
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='courses', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Auto-generate slug from title if not provided
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def enrollments_count(self):
        # Count enrollments
        return self.enrollments.count() if hasattr(self, 'enrollments') else 0
    
    @property
    def total_lessons(self):
        """Get total number of lessons in all modules"""
        return Lesson.objects.filter(module__course=self).count()
    
    @property
    def has_video_content(self):
        """Check if course has any video content"""
        return Lesson.objects.filter(
            module__course=self
        ).filter(
            models.Q(video_file__isnull=False) | models.Q(video_url__isnull=False)
        ).exists()


class CourseResource(models.Model):
    course = models.ForeignKey(Course, related_name='resources', on_delete=models.CASCADE)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='course_resources/%Y/%m/%d/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_file_name(self):
        """Return just the filename (without the upload path)."""
        return os.path.basename(self.file.name) if self.file else ''


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(models.Model):
    """
    Comprehensive Lesson model supporting:
    - YouTube videos via URL
    - Downloaded video files (MP4, WebM, OGG)
    - Text content
    - Quiz content
    - Practical exercises
    """
    
    LESSON_TYPE_CHOICES = [
        ('text', 'Text'),
        ('video', 'Video'),
        ('pdf', 'PDF'),
        ('image', 'Image'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
        ('practical', 'Practical'),
    ]

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True, null=True)
    
    # ===== VIDEO OPTION 1: YouTube URL =====
    video_url = models.URLField(
        blank=True, 
        null=True,
        help_text="Add YouTube video embed URL (e.g., https://www.youtube.com/embed/abc123)"
    )
    
    # ===== VIDEO OPTION 2: Downloaded Video File =====
    video_file = models.FileField(
        upload_to='lessons/videos/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text="Upload a video file from your system (MP4, WebM, OGG supported)"
    )
    pdf_file = models.FileField(
        upload_to='lessons/pdfs/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text="Upload a PDF file for this lesson"
    )
    image = models.ImageField(
        upload_to='lessons/images/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text="Upload an image for this lesson"
    )
    
    # Lesson metadata
    lesson_type = models.CharField(
        max_length=20,
        choices=LESSON_TYPE_CHOICES,
        default='text'
    )
    
    duration_minutes = models.IntegerField(
        default=0,
        help_text="Video duration in minutes"
    )
    
    points_value = models.PositiveIntegerField(
        default=25, 
        help_text="Points awarded for completing this lesson"
    )
    
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.module.title} - {self.title}"
    
    def has_video_content(self):
        """Check if lesson has any video content"""
        return bool(self.video_file or self.video_url)
    
    def get_video_type(self):
        """Determine which video type is available"""
        if self.video_file and self.video_url:
            return 'both'
        elif self.video_file:
            return 'file'
        elif self.video_url:
            return 'url'
        return None
    
    def get_video_display_name(self):
        """Get display name for video file"""
        if self.video_file:
            return self.video_file.name.split('/')[-1]
        return None


class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('user', 'course')
        ordering = ['-enrolled_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.course.title}"
    
    @property
    def progress_percentage(self):
        """Calculate course progress percentage"""
        total_lessons = Lesson.objects.filter(module__course=self.course).count()
        if total_lessons == 0:
            return 0
        completed_lessons = self.lesson_progress.filter(is_completed=True).count()
        return int((completed_lessons / total_lessons) * 100)


class LessonProgress(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    lesson_watched = models.BooleanField(default=False, help_text="Lesson content fully consumed")
    completed_at = models.DateTimeField(null=True, blank=True)
    watched_duration = models.IntegerField(default=0, help_text="Seconds watched")
    
    class Meta:
        unique_together = ('enrollment', 'lesson')
        ordering = ['lesson__order']
    
    def __str__(self):
        return f"{self.enrollment.user.username} - {self.lesson.title}"


class Certificate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    issued_at = models.DateTimeField(auto_now_add=True)
    certificate_id = models.CharField(max_length=50, unique=True)
    
    class Meta:
        ordering = ['-issued_at']
    
    def save(self, *args, **kwargs):
        if not self.certificate_id:
            import uuid
            self.certificate_id = str(uuid.uuid4())[:12].upper()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - {self.course.title} Certificate"
