from django.urls import path
from .views import (
    QuizListView, QuizDetailView, ChallengeListView,
    start_quiz, take_quiz, submit_quiz, quiz_result, quiz_status
)

app_name = 'assessments'

urlpatterns = [
    path('quizzes/', QuizListView.as_view(), name='quiz_list'),
    path('quizzes/<int:pk>/', QuizDetailView.as_view(), name='quiz_detail'),
    path('quizzes/<int:quiz_id>/status/', quiz_status, name='quiz_status'),
    path('quizzes/<int:quiz_id>/start/', start_quiz, name='start_quiz'),
    path('attempt/<int:attempt_id>/take/', take_quiz, name='take_quiz'),
    path('quizzes/<int:quiz_id>/take/', take_quiz, name='take_quiz_direct'),
    path('attempt/<int:attempt_id>/submit/', submit_quiz, name='submit_quiz'),
    path('attempt/<int:attempt_id>/result/', quiz_result, name='quiz_result'),
    path('challenges/', ChallengeListView.as_view(), name='challenge_list'),
]
