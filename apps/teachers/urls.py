from django.urls import path

from . import views

app_name = 'teacher'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('courses/', views.course_list, name='course_list'),
    path('courses/create/', views.course_create, name='course_create'),
    path('courses/<int:course_id>/builder/', views.course_builder, name='course_builder'),
    path('courses/<int:course_id>/edit/', views.course_update, name='course_update'),
    path('courses/<int:course_id>/delete/', views.course_delete, name='course_delete'),
    path('modules/<int:module_id>/edit/', views.module_update, name='module_update'),
    path('modules/<int:module_id>/delete/', views.module_delete, name='module_delete'),
    path('lessons/<int:lesson_id>/edit/', views.lesson_update, name='lesson_update'),
    path('lessons/<int:lesson_id>/delete/', views.lesson_delete, name='lesson_delete'),
    path('quizzes/', views.quiz_list, name='quiz_list'),
    path('quizzes/create/', views.quiz_create, name='quiz_create'),
    path('quizzes/<int:quiz_id>/edit/', views.quiz_update, name='quiz_update'),
    path('quizzes/<int:quiz_id>/delete/', views.quiz_delete, name='quiz_delete'),
    path('quizzes/<int:quiz_id>/questions/', views.quiz_questions, name='quiz_questions'),
    path(
        'quizzes/<int:quiz_id>/questions/<int:question_id>/edit/',
        views.question_update,
        name='question_update',
    ),
    path(
        'quizzes/<int:quiz_id>/questions/<int:question_id>/delete/',
        views.question_delete,
        name='question_delete',
    ),
    path('enrollments/', views.enrollments, name='enrollments'),
    path('analytics/', views.analytics, name='analytics'),
    path('search/', views.search, name='search'),
]
