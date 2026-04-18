from django.urls import path
from . import views

app_name = 'challenges'

urlpatterns = [
    # Public challenges
    path('', views.ChallengeListView.as_view(), name='challenge_list'),
    path('<int:pk>/', views.ChallengeDetailView.as_view(), name='challenge_detail'),
    path('<int:pk>/submit/', views.submit_challenge, name='submit_challenge'),
    
    # User submissions
    path('my-submissions/', views.my_submissions, name='my_submissions'),
    
    # Admin verification
    path('admin/verify/', views.admin_verify_submissions, name='admin_verify'),
    path('admin/approve/<int:submission_id>/', views.approve_submission, name='approve_submission'),
    path('admin/reject/<int:submission_id>/', views.reject_submission, name='reject_submission'),
]
