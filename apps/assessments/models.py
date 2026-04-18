"""
Assessment and quiz models for Environmental Education Platform
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class QuizCategory(models.Model):
    """Categories for organizing quizzes"""

    name = models.CharField(max_length=100)
    description = models.TextField()
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default='#007bff')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'quiz_categories'
        verbose_name_plural = 'Quiz Categories'

    def __str__(self):
        return self.name


class Quiz(models.Model):
    """Environmental knowledge quizzes"""

    QUIZ_TYPES = [
        ('knowledge', 'Knowledge Check'),
        ('assessment', 'Course Assessment'),
        ('challenge', 'Daily Challenge'),
        ('competitive', 'Competitive Quiz'),
    ]

    DIFFICULTY_LEVELS = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
        ('expert', 'Expert'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(QuizCategory, on_delete=models.CASCADE, related_name='quizzes')
    quiz_type = models.CharField(max_length=20, choices=QUIZ_TYPES)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS)

    bulk_questions_json = models.TextField(
        blank=True,
        null=True,
        help_text='Paste JSON to bulk add questions. Leave empty if adding questions individually.'
    )

    # Quiz settings
    time_limit = models.PositiveIntegerField(blank=True, null=True)  # in minutes
    max_attempts = models.PositiveIntegerField(default=3)
    passing_score = models.PositiveIntegerField(default=70)  # percentage

    # Gamification
    points_per_question = models.IntegerField(default=10)
    bonus_points = models.IntegerField(default=50)

    # Availability
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_scheduled = models.BooleanField(default=False)
    scheduled_start_datetime = models.DateTimeField(blank=True, null=True)
    scheduled_end_datetime = models.DateTimeField(blank=True, null=True)

    @property
    def unique_users_taken(self):
        return self.attempts.values('user').distinct().count()

    # Tracking
    attempt_count = models.PositiveIntegerField(default=0)

    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_quizzes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'quizzes'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    QUIZ_STATUS_DRAFT = 'draft'
    QUIZ_STATUS_SCHEDULED = 'scheduled'
    QUIZ_STATUS_LIVE = 'live'
    QUIZ_STATUS_CLOSED = 'closed'

    QUIZ_STATUS_CHOICES = [
        (QUIZ_STATUS_DRAFT, 'Draft'),
        (QUIZ_STATUS_SCHEDULED, 'Scheduled'),
        (QUIZ_STATUS_LIVE, 'Live'),
        (QUIZ_STATUS_CLOSED, 'Closed'),
    ]

    def get_quiz_status(self, now=None):
        if not self.is_published:
            return self.QUIZ_STATUS_DRAFT

        now = now or timezone.now()
        if not self.is_scheduled:
            return self.QUIZ_STATUS_LIVE

        if self.scheduled_start_datetime and now < self.scheduled_start_datetime:
            return self.QUIZ_STATUS_SCHEDULED
        if self.scheduled_end_datetime and now > self.scheduled_end_datetime:
            return self.QUIZ_STATUS_CLOSED
        return self.QUIZ_STATUS_LIVE

    def get_quiz_status_display_label(self):
        status = self.get_quiz_status()
        return dict(self.QUIZ_STATUS_CHOICES).get(status, 'Live')



class QuizAttempt(models.Model):
    """Individual quiz attempts by users"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')

    # Attempt tracking
    attempt_number = models.PositiveIntegerField()
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    time_taken = models.PositiveIntegerField(blank=True, null=True)  # in seconds

    # Scoring
    total_questions = models.PositiveIntegerField()
    correct_answers = models.PositiveIntegerField(default=0)
    score_percentage = models.FloatField(default=0.0)
    points_earned = models.IntegerField(default=0)

    # Status
    is_completed = models.BooleanField(default=False)
    is_passed = models.BooleanField(default=False)

    class Meta:
        db_table = 'quiz_attempts'
        unique_together = ['user', 'quiz', 'attempt_number']
        ordering = ['-started_at']

    def __str__(self):
        status = "✓" if self.is_passed else "✗"
        return f"{status} {self.user.full_name} - {self.quiz.title}"


class CompetitiveChallenge(models.Model):
    """Daily/weekly competitive challenges"""

    CHALLENGE_TYPES = [
        ('daily', 'Daily Challenge'),
        ('weekly', 'Weekly Challenge'),
        ('special', 'Special Event'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    challenge_type = models.CharField(max_length=20, choices=CHALLENGE_TYPES)

    # Challenge content
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='challenges')

    # Timing
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    # Rewards
    winner_points = models.IntegerField(default=1000)
    participation_points = models.IntegerField(default=100)

    # Status
    is_active = models.BooleanField(default=True)
    participant_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'competitive_challenges'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.challenge_type.title()}: {self.title}"

    @property
    def is_ongoing(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date

class Question(models.Model):
    """Individual questions for quizzes"""
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    # Points for this question
    points = models.IntegerField(default=10)  # <<--- ADD THIS LINE
    # Multiple choice options
    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500)
    option_d = models.CharField(max_length=500)
    
    # Correct answer (A, B, C, or D)
    correct_answer = models.CharField(max_length=1, choices=[
        ('A', 'Option A'),
        ('B', 'Option B'),
        ('C', 'Option C'),
        ('D', 'Option D'),
    ])
    
    explanation = models.TextField(blank=True, help_text="Explanation for the correct answer")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'quiz_questions'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.quiz.title} - Q{self.pk}"

class QuizResponse(models.Model):
    """User's answers to individual questions"""
    
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.CharField(max_length=1, choices=[
        ('A', 'Option A'),
        ('B', 'Option B'),
        ('C', 'Option C'),
        ('D', 'Option D'),
    ], blank=True, null=True)
    
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'quiz_responses'
        unique_together = ['attempt', 'question']
    
    def __str__(self):
        return f"{self.attempt.user.username} - {self.question.question_text[:50]}"
