"""
URL configuration for accounts app
"""

from django.urls import path, include
from django.contrib.auth import views as auth_views
from allauth.socialaccount.providers.google.views import oauth2_callback as google_callback
from allauth.socialaccount.providers.facebook.views import oauth2_callback as facebook_callback
from . import views, social_views

app_name = 'accounts'

urlpatterns = [
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        redirect_authenticated_user=True
    ), name='login'),

    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('register/', views.RegisterView.as_view(), name='register'),

    # Profile URLs  
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),

    # Password Change URLs (for logged-in users)
    path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html',
        success_url='/accounts/password-change/done/'
    ), name='password_change'),
    
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'
    ), name='password_change_done'),

    # Password Reset — 2-step verification with email OTP
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/verify/', views.password_reset_verify, name='password_reset_verify'),
    path('password-reset/new-password/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),

    # Legacy redirect for old reset links
    path('password-reset/done/', views.password_reset_verify, name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.password_reset_request, name='password_reset_legacy'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete_legacy'),

    # Export data
    path('export-data/', views.export_user_data, name='export_data'),

    # Settings
    path('settings/', views.ProfileUpdateView.as_view(), name='settings'),

    # Dashboard redirect
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),

    # Social authentication (Google & Facebook)
    path('auth/google/login/', social_views.google_login, name='social_google'),
    path('auth/google/login/callback/', google_callback, name='google_callback'),
    path('auth/facebook/login/', social_views.facebook_login, name='social_facebook'),
    path('auth/facebook/login/callback/', facebook_callback, name='facebook_callback'),
    path('auth/', include('allauth.urls')),
]
