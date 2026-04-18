from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Question, Quiz, QuizCategory


User = get_user_model()


class QuizSchedulingTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teacher_sched',
            email='teacher_sched@example.com',
            password='testpass123',
            user_type='teacher',
        )
        self.student = User.objects.create_user(
            username='student_sched',
            email='student_sched@example.com',
            password='testpass123',
            user_type='student',
        )
        self.category = QuizCategory.objects.create(
            name='Scheduling',
            description='Scheduling category',
            slug='scheduling',
        )
        self.quiz = Quiz.objects.create(
            title='Scheduled Quiz',
            description='Quiz description',
            category=self.category,
            quiz_type='knowledge',
            difficulty='easy',
            is_published=True,
            is_scheduled=True,
            scheduled_start_datetime=timezone.now() + timedelta(hours=1),
            scheduled_end_datetime=timezone.now() + timedelta(hours=2),
            created_by=self.teacher,
        )
        Question.objects.create(
            quiz=self.quiz,
            question_text='What is 2+2?',
            option_a='3',
            option_b='4',
            option_c='5',
            option_d='6',
            correct_answer='B',
        )
        self.client.login(email='student_sched@example.com', password='testpass123')

    def test_quiz_status_changes_by_schedule_window(self):
        self.assertEqual(self.quiz.get_quiz_status(), Quiz.QUIZ_STATUS_SCHEDULED)

        self.quiz.scheduled_start_datetime = timezone.now() - timedelta(minutes=5)
        self.quiz.scheduled_end_datetime = timezone.now() + timedelta(minutes=30)
        self.quiz.save(update_fields=['scheduled_start_datetime', 'scheduled_end_datetime'])
        self.assertEqual(self.quiz.get_quiz_status(), Quiz.QUIZ_STATUS_LIVE)

        self.quiz.scheduled_end_datetime = timezone.now() - timedelta(minutes=1)
        self.quiz.save(update_fields=['scheduled_end_datetime'])
        self.assertEqual(self.quiz.get_quiz_status(), Quiz.QUIZ_STATUS_CLOSED)

    def test_start_quiz_forbidden_before_scheduled_start(self):
        response = self.client.get(reverse('assessments:start_quiz', kwargs={'quiz_id': self.quiz.id}))
        self.assertEqual(response.status_code, 403)

    def test_start_quiz_allowed_during_live_window(self):
        self.quiz.scheduled_start_datetime = timezone.now() - timedelta(minutes=5)
        self.quiz.scheduled_end_datetime = timezone.now() + timedelta(minutes=45)
        self.quiz.save(update_fields=['scheduled_start_datetime', 'scheduled_end_datetime'])

        response = self.client.get(reverse('assessments:start_quiz', kwargs={'quiz_id': self.quiz.id}))
        self.assertEqual(response.status_code, 302)

