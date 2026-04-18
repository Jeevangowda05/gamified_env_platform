"""
Views for accounts app
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, DetailView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponse
from .models import User
from .forms import CustomUserCreationForm, UserProfileForm
import json

class RegisterView(CreateView):
    """User registration view"""
    model = User
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('core:dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Log the user in after successful registration
        username = form.cleaned_data.get('email')
        password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        login(self.request, user)
        messages.success(self.request, f'Welcome to EcoLearn, {user.first_name}!')
        return response

class ProfileView(LoginRequiredMixin, DetailView):
    """User profile view"""
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'profile_user'

    def get_object(self):
        return self.request.user

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Update user profile"""
    model = User
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('core:profile')
    
    # Specify all fields that can be updated
    fields = [
        'first_name', 'last_name', 'avatar', 'bio', 'phone', 'date_of_birth',
        'institution', 'grade_level', 'student_id', 'learning_style',
        'notifications_enabled', 'email_notifications', 'show_on_leaderboard'
    ]

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Your profile has been updated successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

@login_required
def dashboard_redirect(request):
    """Redirect to dashboard after login"""
    return redirect('core:dashboard')

@login_required
def export_user_data(request):
    """Export user's learning progress and data as JSON"""
    user = request.user
    
    # Import models
    from apps.gamification.models import UserProgress, UserBadge
    from apps.core.models import Enrollment, Certificate
    
    # Gather user data
    try:
        progress = UserProgress.objects.get(user=user)
    except:
        progress = None
    
    enrollments = Enrollment.objects.filter(user=user)
    certificates = Certificate.objects.filter(user=user)
    badges = UserBadge.objects.filter(user=user)
    
    data = {
        'user_info': {
            'name': user.get_full_name() if hasattr(user, 'get_full_name') else user.full_name,
            'email': user.email,
            'username': user.username,
            'institution': user.institution,
            'grade_level': user.grade_level,
            'joined_date': str(user.date_joined),
        },
        'progress': {
            'total_points': progress.total_points if progress else user.total_points,
            'level': user.level,
            'courses_completed': progress.courses_completed if progress else 0,
            'quizzes_completed': progress.quizzes_completed if progress else 0,
        },
        'enrollments': [
            {
                'course': e.course.title,
                'enrolled_at': str(e.enrolled_at),
                'completed': e.is_completed,
                'progress': getattr(e, 'progress_percentage', 0)
            } for e in enrollments
        ],
        'certificates': [
            {
                'course': c.course.title,
                'issued_date': str(c.issued_at) if hasattr(c, 'issued_at') else str(c.created_at)
            } for c in certificates
        ],
        'badges': [
            {
                'badge': b.badge.name,
                'earned_date': str(b.earned_at)
            } for b in badges
        ]
    }
    
    # Return as JSON download
    response = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="ecolearn_data_{user.username}.json"'
    return response
