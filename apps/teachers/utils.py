from django.contrib.auth import get_user_model

from apps.teachers.models import TeacherCourse, TeacherNotification


User = get_user_model()


def create_teacher_notification_for_course(course, actor, event_type, title, message):
    assignment = TeacherCourse.objects.filter(course=course).select_related('teacher').first()
    if not assignment or assignment.teacher_id == getattr(actor, 'id', None):
        return None
    return TeacherNotification.objects.create(
        teacher=assignment.teacher,
        actor=actor,
        event_type=event_type,
        title=title,
        message=message,
    )


def create_teacher_notification_for_quiz(quiz, actor, event_type, title, message):
    teacher = getattr(quiz, 'created_by', None)
    if not teacher or teacher.id == getattr(actor, 'id', None):
        return None
    return TeacherNotification.objects.create(
        teacher=teacher,
        actor=actor,
        event_type=event_type,
        title=title,
        message=message,
    )


def create_teacher_notifications_for_challenge_submission(actor, challenge):
    teachers = User.objects.filter(
        user_type='teacher',
        notifications_enabled=True,
    ).only('id')
    payloads = [
        TeacherNotification(
            teacher_id=teacher.id,
            actor=actor,
            event_type='challenge_submitted',
            title='Challenge submitted',
            message=f'{actor.get_full_name() or actor.email} submitted "{challenge.title}".',
        )
        for teacher in teachers
        if teacher.id != getattr(actor, 'id', None)
    ]
    if payloads:
        TeacherNotification.objects.bulk_create(payloads)
    return len(payloads)


def _student_recipients_queryset():
    return User.objects.filter(user_type='student', notifications_enabled=True).only('id')


def create_student_notifications_for_course(actor, event_type, title, message, recipients=None):
    target_recipients = recipients if recipients is not None else _student_recipients_queryset()
    notifications = [
        {
            'recipient_id': recipient.id,
            'actor': actor,
            'event_type': event_type,
            'title': title,
            'message': message,
        }
        for recipient in target_recipients
        if recipient.id != getattr(actor, 'id', None)
    ]
    if not notifications:
        return 0
    from apps.teachers.models import StudentNotification

    StudentNotification.objects.bulk_create([StudentNotification(**payload) for payload in notifications])
    return len(notifications)


def create_student_notifications_for_quiz(actor, event_type, title, message):
    return create_student_notifications_for_course(
        actor=actor,
        event_type=event_type,
        title=title,
        message=message,
    )


def create_new_lesson_notifications(course, lesson, actor):
    recipients = (
        User.objects.filter(
            enrollments__course=course,
            user_type='student',
            notifications_enabled=True,
        )
        .distinct()
        .only('id')
    )
    return create_student_notifications_for_course(
        actor=actor,
        event_type='lesson_added',
        title=f'New lesson in {course.title}',
        message=f'A new lesson "{lesson.title}" has been added to {course.title}.',
        recipients=recipients,
    )
