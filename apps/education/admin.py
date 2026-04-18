"""
Admin configuration for education app
"""

#from django.contrib import admin
#from .models import EnvironmentalTopic

#@admin.register(EnvironmentalTopic)
##list_display = ('name', 'difficulty_level', 'is_active', 'is_featured', 'order')
    #list_filter = ('difficulty_level', 'is_active', 'is_featured')
    #search_fields = ('name', 'description')
    #prepopulated_fields = {'slug': ('name',)}
    #ordering = ('order', 'name')

# REMOVED: Course, CourseEnrollment, Certificate admin
# These are now managed in apps/core/admin.py only
