"""
Educational content models for Environmental Education Platform
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

# You can keep this if you want more detailed topic information
# Otherwise, use the Topic model from core
#class EnvironmentalTopic(models.Model):
  #  """Main environmental topics/categories - Extended version"""
    
  #  name = models.CharField(max_length=100)
  #  description = models.TextField()
   # slug = models.SlugField(unique=True)
    
    # Visual elements
  #  icon = models.CharField(max_length=50, blank=True)  # Font Awesome icon
   ## cover_image = models.ImageField(upload_to='topics/', blank=True, null=True)
    
    # Learning objectives
  #  learning_objectives = models.JSONField(default=list)
  #  target_age_group = models.CharField(max_length=50, blank=True)
   ## max_length=20,
       # choices=[
        #    ('beginner', 'Beginner'),
         #   ('intermediate', 'Intermediate'),
          #  ('advanced', 'Advanced'),
        #]#,
        #default='beginner'
    #)
    
    # Ordering and status
    #order = models.PositiveIntegerField(default=0)
    #is_active = models.BooleanField(default=True)
    #is_featured = models.BooleanField(default=False)
    
    #created_at = models.DateTimeField(auto_now_add=True)
    #updated_at = models.DateTimeField(auto_now=True)
    
    #class Meta:
     #   db_table = 'environmental_topics'
      #  ordering = ['order', 'name']
    
   # def __str__(self):
    #    return self.name

# REMOVED: Course, CourseEnrollment, Certificate (duplicates from core)
# Keep these models only in apps/core/models.py

