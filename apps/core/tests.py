from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Course, Enrollment, Lesson, LessonProgress, Module, Topic


User = get_user_model()


class LessonCompletionFlowTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username='core_student',
            email='core_student@example.com',
            password='testpass123',
            user_type='student',
        )
        self.topic = Topic.objects.create(
            name='Core Topic',
            description='Topic description',
            icon='fas fa-leaf',
            background_color='#38A169',
            difficulty_level='beginner',
        )
        self.course = Course.objects.create(
            title='Core Course',
            description='Course description',
            duration=30,
            completion_points=100,
            topic=self.topic,
        )
        self.module = Module.objects.create(course=self.course, title='Module 1', order=1)
        self.video_lesson = Lesson.objects.create(
            module=self.module,
            title='Video Lesson',
            lesson_type='video',
            content='Video lesson',
            order=1,
        )
        self.enrollment = Enrollment.objects.create(user=self.student, course=self.course)
        self.client.login(email='core_student@example.com', password='testpass123')

    def test_video_lesson_cannot_complete_before_video_watched(self):
        response = self.client.post(
            reverse(
                'core:complete_lesson',
                kwargs={'slug': self.course.slug, 'lesson_id': self.video_lesson.id},
            )
        )
        self.assertEqual(response.status_code, 302)
        progress = LessonProgress.objects.get(enrollment=self.enrollment, lesson=self.video_lesson)
        self.assertFalse(progress.is_completed)

    def test_video_lesson_completes_after_video_marked_watched(self):
        progress = LessonProgress.objects.create(
            enrollment=self.enrollment,
            lesson=self.video_lesson,
            lesson_watched=True,
        )
        response = self.client.post(
            reverse(
                'core:complete_lesson',
                kwargs={'slug': self.course.slug, 'lesson_id': self.video_lesson.id},
            )
        )
        self.assertEqual(response.status_code, 302)
        progress.refresh_from_db()
        self.assertTrue(progress.is_completed)

