from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.utils import timezone


User = get_user_model()


class Challenge(models.Model):
    """Real-world environmental challenges for users to complete"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructions = models.TextField(help_text="Step-by-step instructions for completing the challenge")
    difficulty = models.CharField(
        max_length=20,
        choices=[
            ('easy', 'Easy'),
            ('medium', 'Medium'),
            ('hard', 'Hard'),
        ],
        default='medium'
    )
    
    # Rewards
    points_reward = models.IntegerField(default=50, help_text="Points awarded upon approval")
    badge_name = models.CharField(max_length=100, blank=True, help_text="Badge name (optional)")
    
    # Details
    category = models.CharField(
        max_length=100,
        choices=[
            ('tree_plantation', 'Tree Plantation'),
            ('waste_management', 'Waste Management'),
            ('water_conservation', 'Water Conservation'),
            ('energy_saving', 'Energy Saving'),
            ('clean_environment', 'Clean Environment'),
            ('other', 'Other'),
        ],
        default='other'
    )
    
    thumbnail = models.ImageField(upload_to='challenges/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title



class ChallengeSubmission(models.Model):
    """Track user submissions for challenges"""
    SUBMISSION_STATUS = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='challenge_submissions')
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='submissions')
    
    # Submission
    proof_file = models.FileField(
        upload_to='challenge_proofs/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    description = models.TextField(blank=True, help_text="User's description of what they did")
    
    # Status and Review
    status = models.CharField(max_length=20, choices=SUBMISSION_STATUS, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Admin review
    reviewer_notes = models.TextField(blank=True, help_text="Admin notes during review")
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_submissions'
    )
    
    class Meta:
        unique_together = ('user', 'challenge')  # One submission per user per challenge
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.challenge.title} ({self.status})"
    
    def approve(self, reviewer):
    #"""Approve submission and award points"""
        from apps.gamification.models import PointTransaction, UserProgress
    
        self.status = 'approved'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save()
    
        try:
        # Create PointTransaction
            PointTransaction.objects.create(
                user=self.user,
                transaction_type='earned',
                points=self.challenge.points_reward,
                reason=f"Challenge Approved: {self.challenge.title}",
                related_content_type='challenge',
                related_object_id=str(self.challenge.id)
            )
        
        # Update UserProgress
            user_progress, created = UserProgress.objects.get_or_create(user=self.user)
            user_progress.add_challenge_points(self.challenge.points_reward)
        
        except Exception as e:
            print(f"Error awarding points: {e}")

        
    
    def reject(self, reviewer, notes=""):
        """Reject submission"""
        self.status = 'rejected'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.reviewer_notes = notes
        self.save()
