"""
Custom user model for Gamified Environmental Education Platform
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    """Custom user model with additional fields for gamification"""

    # Basic user information
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)

    # User type
    USER_TYPES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Administrator'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='student')

    # School/Institution information
    institution = models.CharField(max_length=100, blank=True)
    grade_level = models.CharField(max_length=20, blank=True)
    student_id = models.CharField(max_length=100, blank=True)  # NEW

    # Profile information
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)  # NEW

    # Gamification fields
    total_points = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    experience_points = models.IntegerField(default=0)

    # Activity tracking
    last_login_streak = models.IntegerField(default=0)
    total_lessons_completed = models.IntegerField(default=0)
    total_quizzes_taken = models.IntegerField(default=0)

    # Preferences
    preferred_language = models.CharField(max_length=10, default='en')
    notifications_enabled = models.BooleanField(default=True)
    
    # NEW: Additional privacy & notification settings
    email_notifications = models.BooleanField(default=False)
    show_on_leaderboard = models.BooleanField(default=True)
    learning_style = models.CharField(max_length=50, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_level_progress(self):
        """Calculate progress to next level"""
        points_for_next_level = (self.level * 1000)
        current_level_points = ((self.level - 1) * 1000)
        if points_for_next_level == current_level_points:
            return 100
        progress = (self.total_points - current_level_points) / (points_for_next_level - current_level_points)
        return min(progress * 100, 100)

    def add_points(self, points):
        """Add points and update level if necessary"""
        self.total_points += points
        self.experience_points += points

        # Level up logic
        new_level = (self.total_points // 1000) + 1
        if new_level > self.level:
            self.level = new_level

        self.save()

class UserProfile(models.Model):
    """Extended user profile for additional information"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # Environmental preferences
    favorite_environmental_topics = models.JSONField(default=list, blank=True)
    sustainability_goals = models.TextField(blank=True)

    # Learning preferences
    learning_style = models.CharField(
        max_length=20,
        choices=[
            ('visual', 'Visual Learner'),
            ('auditory', 'Auditory Learner'),
            ('kinesthetic', 'Kinesthetic Learner'),
            ('reading', 'Reading/Writing Learner'),
        ],
        blank=True
    )

    # Social features
    is_public_profile = models.BooleanField(default=True)
    allow_friend_requests = models.BooleanField(default=True)

    # Achievement tracking
    badges_earned = models.IntegerField(default=0)
    certificates_earned = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'

    def __str__(self):
        return f"Profile for {self.user.full_name}"
