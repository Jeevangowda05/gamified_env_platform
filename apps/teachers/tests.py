from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.assessments.models import Quiz, QuizAttempt, QuizCategory
from apps.challenges.models import Challenge
from apps.core.models import Course, Enrollment, Lesson, Module, Topic
from apps.gamification.models import PointTransaction, UserProgress
from apps.gamification.utils import award_points
from apps.teachers.models import StudentNotification, TeacherCourse, TeacherNotification


User = get_user_model()


class TeacherAccessTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teacher1',
            email='teacher1@example.com',
            password='testpass123',
            first_name='Teach',
            last_name='Er',
            user_type='teacher',
        )
        self.student = User.objects.create_user(
            username='student1',
            email='student1@example.com',
            password='testpass123',
            first_name='Stu',
            last_name='Dent',
            user_type='student',
        )

    def test_teacher_can_access_dashboard(self):
        self.client.login(email='teacher1@example.com', password='testpass123')
        response = self.client.get(reverse('teacher:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_student_redirected_from_teacher_dashboard(self):
        self.client.login(email='student1@example.com', password='testpass123')
        response = self.client.get(reverse('teacher:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('core:dashboard'))

    def test_teacher_redirected_to_teacher_dashboard_from_core_dashboard(self):
        self.client.login(email='teacher1@example.com', password='testpass123')
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('teacher:dashboard'))


class TeacherCrudFlowTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teacher2',
            email='teacher2@example.com',
            password='testpass123',
            first_name='Teach',
            last_name='Two',
            user_type='teacher',
        )
        self.topic = Topic.objects.create(
            name='Climate',
            description='Climate basics',
            icon='fas fa-leaf',
            background_color='#38A169',
            difficulty_level='beginner',
        )
        self.category = QuizCategory.objects.create(
            name='Category',
            description='Quiz category',
            slug='category',
        )
        self.client.login(email='teacher2@example.com', password='testpass123')

    def test_course_create_creates_teacher_assignment(self):
        response = self.client.post(
            reverse('teacher:course_create'),
            data={
                'title': 'Teacher Course',
                'description': 'Course body',
                'topic': self.topic.id,
                'duration': 30,
                'completion_points': 100,
            },
        )
        self.assertEqual(response.status_code, 302)
        course = Course.objects.get(title='Teacher Course')
        self.assertTrue(TeacherCourse.objects.filter(teacher=self.teacher, course=course).exists())

    def test_quiz_create_assigns_teacher_as_creator(self):
        response = self.client.post(
            reverse('teacher:quiz_create'),
            data={
                'title': 'Teacher Quiz',
                'description': 'Quiz body',
                'category': self.category.id,
                'quiz_type': 'knowledge',
                'difficulty': 'easy',
                'max_attempts': 2,
                'passing_score': 60,
                'points_per_question': 10,
                'bonus_points': 20,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Quiz.objects.filter(title='Teacher Quiz', created_by=self.teacher).exists())

    def test_course_builder_can_add_module_and_lesson(self):
        course = Course.objects.create(
            title='Builder Course',
            description='Course body',
            topic=self.topic,
            duration=40,
            completion_points=100,
        )
        TeacherCourse.objects.create(teacher=self.teacher, course=course)

        module_response = self.client.post(
            reverse('teacher:course_builder', kwargs={'course_id': course.id}),
            data={'action': 'add_module', 'title': 'Module 1', 'description': 'Module body', 'order': 1},
        )
        self.assertEqual(module_response.status_code, 302)
        module = Module.objects.get(course=course, title='Module 1')

        lesson_response = self.client.post(
            reverse('teacher:course_builder', kwargs={'course_id': course.id}),
            data={
                'action': 'add_lesson',
                'module_id': module.id,
                'title': 'Lesson 1',
                'lesson_type': 'text',
                'content': '<p>HTML body</p>',
                'duration_minutes': 10,
                'points_value': 15,
                'order': 1,
            },
        )
        self.assertEqual(lesson_response.status_code, 302)
        self.assertTrue(Lesson.objects.filter(module=module, title='Lesson 1').exists())

    def test_teacher_search_endpoint_returns_results(self):
        course = Course.objects.create(
            title='River Safety',
            description='Water awareness',
            topic=self.topic,
            duration=20,
            completion_points=90,
        )
        TeacherCourse.objects.create(teacher=self.teacher, course=course)
        response = self.client.get(reverse('teacher:search'), {'q': 'River'})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertGreaterEqual(payload['counts']['courses'], 1)

    def test_course_builder_module_and_lesson_edit_delete(self):
        course = Course.objects.create(
            title='Builder CRUD Course',
            description='Course body',
            topic=self.topic,
            duration=40,
            completion_points=100,
        )
        TeacherCourse.objects.create(teacher=self.teacher, course=course)
        module = Module.objects.create(course=course, title='Module A', description='Body', order=1)
        lesson = Lesson.objects.create(
            module=module,
            title='Lesson A',
            lesson_type='text',
            content='Body',
            duration_minutes=10,
            points_value=15,
            order=1,
        )

        update_module_response = self.client.post(
            reverse('teacher:module_update', kwargs={'module_id': module.id}),
            data={'title': 'Module B', 'description': 'Updated body', 'order': 2},
        )
        self.assertEqual(update_module_response.status_code, 302)
        module.refresh_from_db()
        self.assertEqual(module.title, 'Module B')

        update_lesson_response = self.client.post(
            reverse('teacher:lesson_update', kwargs={'lesson_id': lesson.id}),
            data={
                'title': 'Lesson B',
                'lesson_type': 'text',
                'content': 'Updated content',
                'duration_minutes': 11,
                'points_value': 20,
                'order': 2,
            },
        )
        self.assertEqual(update_lesson_response.status_code, 302)
        lesson.refresh_from_db()
        self.assertEqual(lesson.title, 'Lesson B')

        delete_lesson_response = self.client.post(reverse('teacher:lesson_delete', kwargs={'lesson_id': lesson.id}))
        self.assertEqual(delete_lesson_response.status_code, 302)
        self.assertFalse(Lesson.objects.filter(id=lesson.id).exists())

        delete_module_response = self.client.post(reverse('teacher:module_delete', kwargs={'module_id': module.id}))
        self.assertEqual(delete_module_response.status_code, 302)
        self.assertFalse(Module.objects.filter(id=module.id).exists())


class TeacherNotificationsAndGamificationTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teacher3',
            email='teacher3@example.com',
            password='testpass123',
            first_name='Teach',
            last_name='Three',
            user_type='teacher',
        )
        self.student = User.objects.create_user(
            username='student3',
            email='student3@example.com',
            password='testpass123',
            first_name='Stu',
            last_name='Three',
            user_type='student',
        )
        self.topic = Topic.objects.create(
            name='Energy',
            description='Energy basics',
            icon='fas fa-bolt',
            background_color='#38A169',
            difficulty_level='beginner',
        )
        self.course = Course.objects.create(
            title='Teacher Notification Course',
            description='Course body',
            topic=self.topic,
            duration=45,
            completion_points=120,
        )
        TeacherCourse.objects.create(teacher=self.teacher, course=self.course)

    def test_enroll_creates_teacher_notification(self):
        self.client.login(email='student3@example.com', password='testpass123')
        response = self.client.get(reverse('core:enroll_course', kwargs={'slug': self.course.slug}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            TeacherNotification.objects.filter(
                teacher=self.teacher,
                actor=self.student,
                event_type='course_enrollment',
            ).exists()
        )

    def test_teacher_does_not_receive_points(self):
        award_points(self.teacher, 50, 'Should not award points', content_type='quiz', object_id='1')
        self.assertFalse(PointTransaction.objects.filter(user=self.teacher).exists())
        self.assertFalse(UserProgress.objects.filter(user=self.teacher).exists())

    def test_teacher_notifications_api_returns_real_entries(self):
        TeacherNotification.objects.create(
            teacher=self.teacher,
            actor=self.student,
            event_type='course_enrollment',
            title='Enrollment',
            message='Student enrolled.',
        )
        self.client.login(email='teacher3@example.com', password='testpass123')
        response = self.client.get(reverse('core:notifications_api'))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['unread_count'], 1)
        self.assertEqual(payload['notifications'][0]['type'], 'course_enrollment')

    def test_teacher_creating_course_creates_student_notification(self):
        self.client.login(email='teacher3@example.com', password='testpass123')
        response = self.client.post(
            reverse('teacher:course_create'),
            data={
                'title': 'New Teacher Course',
                'description': 'Course body',
                'topic': self.topic.id,
                'duration': 60,
                'completion_points': 150,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            StudentNotification.objects.filter(
                recipient=self.student,
                event_type='course_created',
                title='New course available',
            ).exists()
        )

    def test_notification_api_mark_read_and_archive_for_student(self):
        notification = StudentNotification.objects.create(
            recipient=self.student,
            actor=self.teacher,
            event_type='quiz_created',
            title='New quiz',
            message='A quiz is available.',
        )
        self.client.login(email='student3@example.com', password='testpass123')
        unread_response = self.client.get(reverse('core:notifications_api'))
        self.assertEqual(unread_response.status_code, 200)
        self.assertEqual(unread_response.json()['unread_count'], 1)

        mark_read_response = self.client.post(
            reverse('core:notifications_api'),
            data={'action': 'mark_read', 'notification_id': notification.id},
            content_type='application/json',
        )
        self.assertEqual(mark_read_response.status_code, 200)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

        archive_response = self.client.post(
            reverse('core:notifications_api'),
            data={'action': 'archive', 'notification_id': notification.id},
            content_type='application/json',
        )
        self.assertEqual(archive_response.status_code, 200)
        archived_response = self.client.get(reverse('core:notifications_api'), {'filter': 'archived'})
        self.assertEqual(archived_response.status_code, 200)
        self.assertEqual(archived_response.json()['notifications'][0]['id'], notification.id)

    def test_challenge_submission_creates_teacher_notification(self):
        challenge = Challenge.objects.create(
            title='Cleanup Drive',
            description='Join cleanup',
            instructions='Step 1\nStep 2',
            difficulty='easy',
            points_reward=25,
            category='clean_environment',
            status='active',
        )
        self.client.login(email='student3@example.com', password='testpass123')
        response = self.client.post(
            reverse('challenges:submit_challenge', kwargs={'pk': challenge.id}),
            data={
                'description': 'Submitted proof',
                'proof_file': SimpleUploadedFile('proof.jpg', b'filecontent', content_type='image/jpeg'),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            TeacherNotification.objects.filter(
                teacher=self.teacher,
                actor=self.student,
                event_type='challenge_submitted',
            ).exists()
        )


class TeacherEnrollmentViewTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teacher4',
            email='teacher4@example.com',
            password='testpass123',
            first_name='Teach',
            last_name='Four',
            user_type='teacher',
        )
        self.student = User.objects.create_user(
            username='student4',
            email='student4@example.com',
            password='testpass123',
            first_name='Stu',
            last_name='Four',
            user_type='student',
        )
        self.topic = Topic.objects.create(
            name='Biodiversity',
            description='Biodiversity basics',
            icon='fas fa-leaf',
            background_color='#38A169',
            difficulty_level='beginner',
        )
        self.course = Course.objects.create(
            title='Forest Course',
            description='Course body',
            topic=self.topic,
            duration=30,
            completion_points=100,
        )
        TeacherCourse.objects.create(teacher=self.teacher, course=self.course)
        Enrollment.objects.create(user=self.student, course=self.course, is_completed=False)
        category = QuizCategory.objects.create(name='Ecology', description='Eco category', slug='ecology')
        self.quiz = Quiz.objects.create(
            title='Forest Quiz',
            description='Quiz body',
            category=category,
            quiz_type='knowledge',
            difficulty='easy',
            created_by=self.teacher,
            max_attempts=3,
            passing_score=60,
            points_per_question=10,
            bonus_points=20,
        )
        QuizAttempt.objects.create(
            user=self.student,
            quiz=self.quiz,
            attempt_number=1,
            total_questions=10,
            correct_answers=8,
            score_percentage=80,
            is_completed=True,
            is_passed=True,
            points_earned=100,
        )
        self.client.login(email='teacher4@example.com', password='testpass123')

    def test_enrollments_page_includes_course_and_quiz_rows(self):
        response = self.client.get(reverse('teacher:enrollments'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Forest Course')
        self.assertContains(response, 'Forest Quiz')

    def test_enrollments_type_filter_quiz(self):
        response = self.client.get(reverse('teacher:enrollments'), {'type': 'quiz'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Forest Quiz')
        self.assertNotContains(response, 'Forest Course')
