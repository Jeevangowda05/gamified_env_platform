"""
Gamification models for the Environmental Education Platform
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
from datetime import timedelta
from django.conf import settings


User = get_user_model()


class BadgeCategory(models.Model):
    """Categories for organizing badges"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, blank=True)  # Font Awesome icon class
    color = models.CharField(max_length=7, default='#28a745')  # Hex color code
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'badge_categories'
        verbose_name_plural = 'Badge Categories'

    def __str__(self):
        return self.name


class Badge(models.Model):
    """Badge definitions for gamification"""

    BADGE_TYPES = [
        ('achievement', 'Achievement'),
        ('participation', 'Participation'),
        ('streak', 'Streak'),
        ('completion', 'Completion'),
        ('special', 'Special Event'),
    ]

    RARITY_LEVELS = [
        ('common', 'Common'),
        ('uncommon', 'Uncommon'),
        ('rare', 'Rare'),
        ('epic', 'Epic'),
        ('legendary', 'Legendary'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPES)
    category = models.ForeignKey(BadgeCategory, on_delete=models.CASCADE, related_name='badges')

    # Visual elements
    icon = models.ImageField(upload_to='badges/', blank=True, null=True)
    icon_class = models.CharField(max_length=50, blank=True)  # CSS class for icon
    rarity = models.CharField(max_length=20, choices=RARITY_LEVELS, default='common')

    # Requirements (original)
    required_points = models.IntegerField(default=0)
    required_actions = models.IntegerField(default=1)
    required_streak = models.IntegerField(default=0)

    # Dynamic progress requirements
    quizzes_required = models.IntegerField(default=0)
    quizzes_passed_required = models.IntegerField(default=0)
    courses_required = models.IntegerField(default=0)
    streak_required = models.IntegerField(default=0)

    # Rewards
    points_reward = models.IntegerField(default=100)

    # Status
    is_active = models.BooleanField(default=True)
    is_hidden = models.BooleanField(default=False)  # Hidden until earned
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'badges'
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    @property
    def earned_count(self):
        return self.user_badges.count()


class UserBadge(models.Model):
    """Many-to-many relationship between users and badges with additional data"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earned_badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='user_badges')

    earned_at = models.DateTimeField(auto_now_add=True)
    progress = models.IntegerField(default=0)  # Progress towards earning the badge
    is_showcased = models.BooleanField(default=False)  # Display on profile

    class Meta:
        db_table = 'user_badges'
        unique_together = ['user', 'badge']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.badge.name}"


class PointTransaction(models.Model):
    """Track all point transactions for transparency"""

    TRANSACTION_TYPES = [
        ('earned', 'Points Earned'),
        ('deducted', 'Points Deducted'),
        ('bonus', 'Bonus Points'),
        ('penalty', 'Penalty'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='point_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    points = models.IntegerField()

    # Context information
    reason = models.CharField(max_length=200)
    related_content_type = models.CharField(max_length=100, blank=True)  # e.g., 'lesson', 'quiz', 'challenge'
    related_object_id = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'point_transactions'
        ordering = ['-created_at']

    def __str__(self):
        sign = '+' if self.points > 0 else ''
        return f"{self.user.get_full_name()}: {sign}{self.points} - {self.reason}"


class LeaderboardEntry(models.Model):
    """Cached leaderboard entries for performance"""

    LEADERBOARD_TYPES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('all_time', 'All Time'),
        ('institutional', 'Institution'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leaderboard_entries')
    leaderboard_type = models.CharField(max_length=20, choices=LEADERBOARD_TYPES)
    points = models.IntegerField(default=0)
    rank = models.IntegerField()

    # Context filters
    institution = models.CharField(max_length=100, blank=True)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'leaderboard_entries'
        unique_together = ['user', 'leaderboard_type', 'period_start']
        ordering = ['rank']

    def __str__(self):
        return f"#{self.rank} {self.user.get_full_name()} - {self.points} pts"


class Achievement(models.Model):
    """Special achievements beyond badges"""

    name = models.CharField(max_length=100)
    description = models.TextField()
    criteria = models.JSONField()  # Store complex achievement criteria

    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default='#ffc107')

    points_reward = models.IntegerField(default=500)
    is_active = models.BooleanField(default=True)
    is_rare = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'achievements'

    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    """Track user achievements"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)

    progress = models.JSONField(default=dict)  # Store progress data
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_achievements'
        unique_together = ['user', 'achievement']

    def __str__(self):
        status = "✓" if self.is_completed else "○"
        return f"{status} {self.user.get_full_name()} - {self.achievement.name}"


class UserProgress(models.Model):
    """Track user's overall progress for badge calculations"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progress')

    # Points Tracking
    total_points = models.PositiveIntegerField(default=0)
    quiz_points = models.PositiveIntegerField(default=0)
    course_points = models.PositiveIntegerField(default=0)
    challenge_points = models.PositiveIntegerField(default=0)
    last_login_bonus_date = models.DateField(null=True, blank=True)

    # Activity Tracking
    quizzes_completed = models.PositiveIntegerField(default=0)
    quizzes_passed = models.PositiveIntegerField(default=0)
    courses_completed = models.PositiveIntegerField(default=0)
    challenges_completed = models.PositiveIntegerField(default=0)

    # Streaks
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    # Timestamps
    updated_at = models.DateTimeField(auto_now=True)

    # Example thresholds for levels (monotonic increasing ints)
    LEVEL_THRESHOLDS = [0, 100, 200, 300, 500, 800, 1200, 1700]

    def get_level(self):
        pts = self.total_points
        for i, threshold in enumerate(self.LEVEL_THRESHOLDS):
            if pts < threshold:
                return i
        return len(self.LEVEL_THRESHOLDS)

    def update_streak(self):
        today = timezone.now().date()
        if self.last_activity_date != today:
            if self.last_activity_date == today - timedelta(days=1):
                self.current_streak += 1
            else:
                self.current_streak = 1
            self.last_activity_date = today
            if self.current_streak > self.longest_streak:
                self.longest_streak = self.current_streak
            self.save()

    def add_challenge_points(self, points):
        """Add points from challenge completion"""
        self.total_points += points
        self.challenge_points += points
        self.challenges_completed += 1
        self.update_streak()
        self.check_badge_eligibility()
        self.save()

    def check_badge_eligibility(self):
        """
        Iterate active badges and award any that the user qualifies for.
        """
        badges = Badge.objects.filter(is_active=True)
        for badge in badges:
            # Skip if already earned
            if UserBadge.objects.filter(user=self.user, badge=badge).exists():
                continue

            # Check requirements
            eligible = True
            if badge.required_points and self.total_points < badge.required_points:
                eligible = False
            if badge.courses_required and self.courses_completed < badge.courses_required:
                eligible = False
            if badge.quizzes_required and self.quizzes_completed < badge.quizzes_required:
                eligible = False
            if badge.quizzes_passed_required and self.quizzes_passed < badge.quizzes_passed_required:
                eligible = False
            if badge.streak_required and self.current_streak < badge.streak_required:
                eligible = False

            # Award badge if eligible
            if eligible:
                UserBadge.objects.create(user=self.user, badge=badge)
                # Add points for earning the badge
                self.total_points += badge.points_reward or 0
                self.save()

    def __str__(self):
        return f"{self.user.get_full_name()} - Level {self.get_level()} ({self.total_points} pts)"

    class Meta:
        db_table = 'user_progress'
        verbose_name_plural = 'User Progress'
