from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.teachers.models import TeacherCourse
from .models import Course, CourseResource, Enrollment, Lesson, LessonProgress, Module, Topic


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


class CourseResourceTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='resource_teacher',
            email='resource_teacher@example.com',
            password='testpass123',
            user_type='teacher',
        )
        self.other_teacher = User.objects.create_user(
            username='other_teacher',
            email='other_teacher@example.com',
            password='testpass123',
            user_type='teacher',
        )
        self.student = User.objects.create_user(
            username='resource_student',
            email='resource_student@example.com',
            password='testpass123',
            user_type='student',
        )
        self.topic = Topic.objects.create(
            name='Resource Topic',
            description='Topic description',
            icon='fas fa-leaf',
            background_color='#38A169',
            difficulty_level='beginner',
        )
        self.course = Course.objects.create(
            title='Resource Course',
            description='Course description',
            duration=30,
            completion_points=100,
            topic=self.topic,
        )
        TeacherCourse.objects.create(teacher=self.teacher, course=self.course)
        self.resource = CourseResource.objects.create(
            course=self.course,
            uploaded_by=self.teacher,
            title='Syllabus',
            description='Course syllabus file',
            file=SimpleUploadedFile('syllabus.pdf', b'pdf-content', content_type='application/pdf'),
        )

    def test_course_detail_includes_resources(self):
        response = self.client.get(reverse('core:course_detail', kwargs={'slug': self.course.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('resources', response.context)
        self.assertContains(response, 'Syllabus')

    def test_course_learn_includes_resources(self):
        Enrollment.objects.create(user=self.student, course=self.course)
        self.client.login(email='resource_student@example.com', password='testpass123')
        response = self.client.get(reverse('core:course_learn', kwargs={'slug': self.course.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('resources', response.context)
        self.assertContains(response, 'Syllabus')

    def test_teacher_can_create_resource(self):
        self.client.login(email='resource_teacher@example.com', password='testpass123')
        response = self.client.post(
            reverse('core:teacher_course_resource_add', kwargs={'slug': self.course.slug}),
            {
                'title': 'Worksheet',
                'description': 'Class worksheet',
                'file': SimpleUploadedFile(
                    'worksheet.docx',
                    b'doc-content',
                    content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                ),
            },
        )
        self.assertRedirects(response, reverse('teacher:course_builder', kwargs={'course_id': self.course.id}))
        created = CourseResource.objects.get(title='Worksheet')
        self.assertEqual(created.course, self.course)
        self.assertEqual(created.uploaded_by, self.teacher)

    def test_non_owner_teacher_cannot_list_course_resources(self):
        self.client.login(email='other_teacher@example.com', password='testpass123')
        response = self.client.get(
            reverse('core:teacher_course_resources', kwargs={'slug': self.course.slug})
        )
        self.assertEqual(response.status_code, 404)
