"""
Views for accounts app
"""

from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from .models import User
from .forms import CustomUserCreationForm, UserProfileForm
from .email_utils import is_smtp_configured, using_console_email, email_setup_hint
from . import password_reset as pwd_reset
import json
import logging

logger = logging.getLogger(__name__)

UserModel = get_user_model()


def password_reset_request(request):
    """Step 1: User enters email; we send a 6-digit OTP."""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Please enter a valid email address.')
            return render(request, 'accounts/password_reset.html')

        user = UserModel.objects.filter(email__iexact=email).first()
        if user:
            if not is_smtp_configured():
                messages.error(
                    request,
                    'Email delivery is not configured yet. Ask the administrator to run: '
                    'python manage.py configure_email',
                )
                return render(request, 'accounts/password_reset.html', {'email_not_configured': True})

            try:
                pwd_reset.send_password_reset_otp(user)
                request.session['password_reset_user_id'] = user.id
                request.session['password_reset_email_masked'] = pwd_reset.mask_email(user.email)
                request.session['password_reset_phone_masked'] = pwd_reset.mask_phone(user.phone)
                messages.success(request, 'Verification code sent! Check your Gmail inbox and spam folder.')
            except Exception as exc:
                logger.exception('Password reset email failed')
                messages.error(
                    request,
                    'Could not send email. Run: python manage.py configure_email '
                    'and use a Gmail App Password (not your normal password).',
                )
                return render(request, 'accounts/password_reset.html')
        else:
            request.session['password_reset_user_id'] = None
            request.session['password_reset_email_masked'] = pwd_reset.mask_email(email)
            request.session['password_reset_phone_masked'] = None

        return redirect('accounts:password_reset_verify')

    return render(request, 'accounts/password_reset.html', {
        'email_not_configured': not is_smtp_configured(),
    })


def password_reset_verify(request):
    """Step 2: User enters OTP from email."""
    user_id = request.session.get('password_reset_user_id')
    email_masked = request.session.get('password_reset_email_masked')

    if not email_masked:
        return redirect('accounts:password_reset')

    if request.method == 'POST':
        action = request.POST.get('action', 'verify')

        if action == 'resend':
            if user_id:
                user = UserModel.objects.filter(id=user_id).first()
                if user:
                    try:
                        pwd_reset.send_password_reset_otp(user)
                    except Exception:
                        messages.error(request, 'Could not resend code. Check email settings.')
                        return redirect('accounts:password_reset_verify')
            messages.success(request, 'A new verification code has been sent.')
            return redirect('accounts:password_reset_verify')

        if not user_id:
            messages.error(request, 'Invalid or expired verification code.')
            return redirect('accounts:password_reset_verify')

        otp = request.POST.get('otp', '').strip()
        ok, error = pwd_reset.verify_otp(user_id, otp)
        if ok:
            return redirect('accounts:password_reset_confirm')
        messages.error(request, error)

    return render(request, 'accounts/password_reset_verify.html', {
        'email_masked': email_masked,
        'phone_masked': request.session.get('password_reset_phone_masked'),
    })


def password_reset_confirm(request):
    """Step 3: User sets a new password after OTP verification."""
    user_id = request.session.get('password_reset_user_id')
    if not user_id or not pwd_reset.is_verified(user_id):
        messages.error(request, 'Please complete verification first.')
        return redirect('accounts:password_reset')

    if request.method == 'POST':
        password1 = request.POST.get('new_password1', '')
        password2 = request.POST.get('new_password2', '')
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
        elif len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        else:
            user = UserModel.objects.get(id=user_id)
            user.set_password(password1)
            user.save()
            pwd_reset.clear_verification(user_id)
            for key in ('password_reset_user_id', 'password_reset_email_masked', 'password_reset_phone_masked'):
                request.session.pop(key, None)
            messages.success(request, 'Your password has been reset successfully!')
            return redirect('accounts:password_reset_complete')

    return render(request, 'accounts/password_reset_confirm.html', {'validlink': True})


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
