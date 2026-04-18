import json

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.http import Http404
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.assessments.models import Question, Quiz, QuizAttempt
from apps.core.models import Course, Enrollment, Lesson, Module, Topic

from .decorators import teacher_required
from .forms import (
    CourseForm,
    LessonEditForm,
    LessonForm,
    ModuleEditForm,
    ModuleForm,
    QuestionForm,
    QuizForm,
)
from .models import TeacherCourse
from .utils import (
    create_new_lesson_notifications,
    create_student_notifications_for_course,
    create_student_notifications_for_quiz,
)


User = get_user_model()


def _teacher_base_context():
    return {'topics': Topic.objects.filter(is_active=True).order_by('name')}


def _teacher_courses_queryset(user):
    if user.is_superuser:
        return Course.objects.all().select_related('topic')
    return Course.objects.filter(teacher_assignment__teacher=user).select_related('topic')


def _teacher_quizzes_queryset(user):
    if user.is_superuser:
        return Quiz.objects.all().select_related('category')
    return Quiz.objects.filter(created_by=user).select_related('category')


@teacher_required
def dashboard(request):
    courses_qs = _teacher_courses_queryset(request.user)
    quizzes_qs = _teacher_quizzes_queryset(request.user)
    enrollments_qs = Enrollment.objects.filter(course__in=courses_qs).select_related('course', 'user')

    chart_payload = {
        'labels': list(courses_qs.values_list('title', flat=True)),
        'students': [course.enrollments.count() for course in courses_qs],
    }

    context = {
        'courses_count': courses_qs.count(),
        'quizzes_count': quizzes_qs.count(),
        'enrollments_count': enrollments_qs.count(),
        'completed_enrollments': enrollments_qs.filter(is_completed=True).count(),
        'recent_courses': courses_qs[:5],
        'recent_quizzes': quizzes_qs[:5],
        'chart_payload_json': json.dumps(chart_payload),
    }
    context.update(_teacher_base_context())
    return render(request, 'teachers/dashboard.html', context)


@teacher_required
def course_list(request):
    courses = _teacher_courses_queryset(request.user)
    query = request.GET.get('q', '').strip()
    topic = request.GET.get('topic', '').strip()
    status = request.GET.get('status', '').strip()

    if query:
        courses = courses.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if topic:
        courses = courses.filter(topic__slug=topic)
    if status == 'active':
        courses = courses.filter(enrollments__isnull=False).distinct()
    elif status == 'empty':
        courses = courses.filter(enrollments__isnull=True)

    return render(
        request,
        'teachers/course_list.html',
        {
            'courses': courses,
            'search_query': query,
            'selected_topic': topic,
            'selected_status': status,
            **_teacher_base_context(),
        },
    )


@teacher_required
def course_create(request):
    form = CourseForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        course = form.save()
        TeacherCourse.objects.create(teacher=request.user, course=course)
        create_student_notifications_for_course(
            actor=request.user,
            event_type='course_created',
            title='New course available',
            message=f'{request.user.get_full_name() or request.user.email} published a new course: {course.title}.',
        )
        messages.success(request, 'Course created successfully.')
        return redirect('teacher:course_builder', course_id=course.id)
    context = {'form': form, 'mode': 'create'}
    context.update(_teacher_base_context())
    return render(request, 'teachers/course_form.html', context)


def _get_teacher_course_or_404(user, course_id):
    course = get_object_or_404(Course, id=course_id)
    if not TeacherCourse.objects.filter(teacher=user, course=course).exists() and not user.is_superuser:
        raise Http404('Course not found')
    return course


def _get_teacher_module_or_404(user, module_id):
    module = get_object_or_404(Module.objects.select_related('course'), id=module_id)
    _get_teacher_course_or_404(user, module.course_id)
    return module


def _get_teacher_lesson_or_404(user, lesson_id):
    lesson = get_object_or_404(Lesson.objects.select_related('module__course'), id=lesson_id)
    _get_teacher_course_or_404(user, lesson.module.course_id)
    return lesson


@teacher_required
def course_update(request, course_id):
    course = _get_teacher_course_or_404(request.user, course_id)
    form = CourseForm(request.POST or None, request.FILES or None, instance=course)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Course updated successfully.')
        return redirect('teacher:course_builder', course_id=course.id)
    context = {'form': form, 'mode': 'update', 'course': course}
    context.update(_teacher_base_context())
    return render(request, 'teachers/course_form.html', context)


@teacher_required
def course_delete(request, course_id):
    course = _get_teacher_course_or_404(request.user, course_id)
    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Course deleted successfully.')
        return redirect('teacher:course_list')
    context = {'course': course}
    context.update(_teacher_base_context())
    return render(request, 'teachers/course_confirm_delete.html', context)


@teacher_required
def course_builder(request, course_id):
    course = _get_teacher_course_or_404(request.user, course_id)
    module_form = ModuleForm()
    lesson_form = LessonForm()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_module':
            module_form = ModuleForm(request.POST)
            if module_form.is_valid():
                module = module_form.save(commit=False)
                module.course = course
                module.save()
                messages.success(request, 'Module added successfully.')
                return redirect('teacher:course_builder', course_id=course.id)
        elif action == 'add_lesson':
            module_id = request.POST.get('module_id')
            module = get_object_or_404(Module, id=module_id, course=course)
            lesson_form = LessonForm(request.POST, request.FILES)
            if lesson_form.is_valid():
                lesson = lesson_form.save(commit=False)
                lesson.module = module
                lesson.save()
                create_new_lesson_notifications(course=course, lesson=lesson, actor=request.user)
                messages.success(request, 'Lesson added successfully.')
                return redirect('teacher:course_builder', course_id=course.id)

    modules = course.modules.prefetch_related('lessons').all()
    return render(
        request,
        'teachers/course_builder.html',
        {
            'course': course,
            'modules': modules,
            'module_form': module_form,
            'lesson_form': lesson_form,
            **_teacher_base_context(),
        },
    )


@teacher_required
def module_update(request, module_id):
    module = _get_teacher_module_or_404(request.user, module_id)
    form = ModuleEditForm(request.POST or None, instance=module)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Module updated successfully.')
        return redirect('teacher:course_builder', course_id=module.course_id)
    return render(
        request,
        'teachers/module_form.html',
        {
            'form': form,
            'module': module,
            'course': module.course,
            **_teacher_base_context(),
        },
    )


@teacher_required
@require_POST
def module_delete(request, module_id):
    module = _get_teacher_module_or_404(request.user, module_id)
    course_id = module.course_id
    module.delete()
    messages.success(request, 'Module deleted successfully.')
    return redirect('teacher:course_builder', course_id=course_id)


@teacher_required
def lesson_update(request, lesson_id):
    lesson = _get_teacher_lesson_or_404(request.user, lesson_id)
    form = LessonEditForm(request.POST or None, request.FILES or None, instance=lesson)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Lesson updated successfully.')
        return redirect('teacher:course_builder', course_id=lesson.module.course_id)
    return render(
        request,
        'teachers/lesson_form.html',
        {
            'form': form,
            'lesson': lesson,
            'module': lesson.module,
            'course': lesson.module.course,
            **_teacher_base_context(),
        },
    )


@teacher_required
@require_POST
def lesson_delete(request, lesson_id):
    lesson = _get_teacher_lesson_or_404(request.user, lesson_id)
    course_id = lesson.module.course_id
    lesson.delete()
    messages.success(request, 'Lesson deleted successfully.')
    return redirect('teacher:course_builder', course_id=course_id)


@teacher_required
def quiz_list(request):
    quizzes = _teacher_quizzes_queryset(request.user)
    query = request.GET.get('q', '').strip()
    difficulty = request.GET.get('difficulty', '').strip()
    status = request.GET.get('status', '').strip()

    if query:
        quizzes = quizzes.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if difficulty:
        quizzes = quizzes.filter(difficulty=difficulty)
    if status == 'published':
        quizzes = quizzes.filter(is_published=True)
    elif status == 'draft':
        quizzes = quizzes.filter(is_published=False)
    elif status == 'scheduled':
        quizzes = quizzes.filter(is_published=True, is_scheduled=True, scheduled_start_datetime__gt=timezone.now())
    elif status == 'live':
        now = timezone.now()
        quizzes = quizzes.filter(is_published=True).filter(
            Q(is_scheduled=False) |
            (
                Q(is_scheduled=True) &
                (Q(scheduled_start_datetime__isnull=True) | Q(scheduled_start_datetime__lte=now)) &
                (Q(scheduled_end_datetime__isnull=True) | Q(scheduled_end_datetime__gte=now))
            )
        )
    elif status == 'closed':
        quizzes = quizzes.filter(is_published=True, is_scheduled=True, scheduled_end_datetime__lt=timezone.now())

    return render(
        request,
        'teachers/quiz_list.html',
        {
            'quizzes': quizzes,
            'search_query': query,
            'selected_difficulty': difficulty,
            'selected_status': status,
            **_teacher_base_context(),
        },
    )


@teacher_required
def quiz_create(request):
    form = QuizForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        quiz = form.save(commit=False)
        quiz.created_by = request.user
        quiz.save()
        create_student_notifications_for_quiz(
            actor=request.user,
            event_type='quiz_created',
            title='New quiz available',
            message=f'{request.user.get_full_name() or request.user.email} published a new quiz: {quiz.title}.',
        )
        messages.success(request, 'Quiz created successfully.')
        return redirect('teacher:quiz_update', quiz_id=quiz.id)
    context = {'form': form, 'mode': 'create'}
    context.update(_teacher_base_context())
    return render(request, 'teachers/quiz_form.html', context)


def _get_teacher_quiz_or_404(user, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if quiz.created_by_id != user.id and not user.is_superuser:
        raise Http404('Quiz not found')
    return quiz


@teacher_required
def quiz_update(request, quiz_id):
    quiz = _get_teacher_quiz_or_404(request.user, quiz_id)
    form = QuizForm(request.POST or None, instance=quiz)
    question_form = QuestionForm(request.POST or None, prefix='question')
    if request.method == 'POST':
        if request.POST.get('action') == 'add_question':
            if question_form.is_valid():
                question = question_form.save(commit=False)
                question.quiz = quiz
                question.save()
                messages.success(request, 'Question added successfully.')
                return redirect('teacher:quiz_update', quiz_id=quiz.id)
        elif form.is_valid():
            form.save()
            messages.success(request, 'Quiz updated successfully.')
            return redirect('teacher:quiz_update', quiz_id=quiz.id)
    return render(
        request,
        'teachers/quiz_form.html',
        {
            'form': form,
            'mode': 'update',
            'quiz': quiz,
            'question_form': question_form,
            'questions': quiz.questions.all(),
            **_teacher_base_context(),
        },
    )


@teacher_required
def quiz_delete(request, quiz_id):
    quiz = _get_teacher_quiz_or_404(request.user, quiz_id)
    if request.method == 'POST':
        quiz.delete()
        messages.success(request, 'Quiz deleted successfully.')
        return redirect('teacher:quiz_list')
    context = {'quiz': quiz}
    context.update(_teacher_base_context())
    return render(request, 'teachers/quiz_confirm_delete.html', context)


@teacher_required
def quiz_questions(request, quiz_id):
    quiz = _get_teacher_quiz_or_404(request.user, quiz_id)
    questions = quiz.questions.all()
    form = QuestionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        question = form.save(commit=False)
        question.quiz = quiz
        question.save()
        messages.success(request, 'Question added successfully.')
        return redirect('teacher:quiz_questions', quiz_id=quiz.id)
    return render(
        request,
        'teachers/quiz_questions.html',
        {'quiz': quiz, 'questions': questions, 'form': form, **_teacher_base_context()},
    )


@teacher_required
def question_update(request, quiz_id, question_id):
    quiz = _get_teacher_quiz_or_404(request.user, quiz_id)
    question = get_object_or_404(Question, id=question_id, quiz=quiz)
    form = QuestionForm(request.POST or None, instance=question)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Question updated successfully.')
        return redirect('teacher:quiz_questions', quiz_id=quiz.id)
    return render(
        request,
        'teachers/question_form.html',
        {'form': form, 'quiz': quiz, 'question': question, **_teacher_base_context()},
    )


@teacher_required
def question_delete(request, quiz_id, question_id):
    quiz = _get_teacher_quiz_or_404(request.user, quiz_id)
    question = get_object_or_404(Question, id=question_id, quiz=quiz)
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted successfully.')
        return redirect('teacher:quiz_questions', quiz_id=quiz.id)
    return render(
        request,
        'teachers/question_confirm_delete.html',
        {'quiz': quiz, 'question': question, **_teacher_base_context()},
    )


@teacher_required
def enrollments(request):
    courses = _teacher_courses_queryset(request.user)
    enrollments_qs = Enrollment.objects.filter(course__in=courses).select_related('user', 'course')
    quizzes = _teacher_quizzes_queryset(request.user)
    quiz_attempts = (
        QuizAttempt.objects.filter(quiz__in=quizzes)
        .select_related('user', 'quiz')
        .order_by('user_id', 'quiz_id', '-started_at')
    )
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    content_type = request.GET.get('type', '').strip()

    rows = []
    for enrollment in enrollments_qs:
        if enrollment.is_completed:
            enrollment_status = 'Completed'
        elif enrollment.progress_percentage > 0:
            enrollment_status = 'In Progress'
        else:
            enrollment_status = 'Enrolled'
        rows.append(
            {
                'student_name': enrollment.user.get_full_name() or enrollment.user.email,
                'content_name': enrollment.course.title,
                'progress': round(enrollment.progress_percentage, 2),
                'status': enrollment_status,
                'enrolled_at': enrollment.enrolled_at,
                'type': 'course',
            }
        )

    latest_attempts = {}
    for attempt in quiz_attempts:
        key = (attempt.user_id, attempt.quiz_id)
        if key not in latest_attempts:
            latest_attempts[key] = attempt
    for attempt in latest_attempts.values():
        rows.append(
            {
                'student_name': attempt.user.get_full_name() or attempt.user.email,
                'content_name': attempt.quiz.title,
                'progress': round(attempt.score_percentage or 0, 2),
                'status': 'Completed' if attempt.is_completed else 'In Progress',
                'enrolled_at': attempt.started_at,
                'type': 'quiz',
            }
        )

    if query:
        lowered_query = query.lower()
        rows = [
            row
            for row in rows
            if lowered_query in row['student_name'].lower() or lowered_query in row['content_name'].lower()
        ]
    if content_type in {'course', 'quiz'}:
        rows = [row for row in rows if row['type'] == content_type]
    if status == 'completed':
        rows = [row for row in rows if row['status'] == 'Completed']
    elif status == 'in_progress':
        rows = [row for row in rows if row['status'] == 'In Progress']
    elif status == 'enrolled':
        rows = [row for row in rows if row['status'] == 'Enrolled']

    rows.sort(key=lambda item: item['enrolled_at'], reverse=True)

    return render(
        request,
        'teachers/enrollments.html',
        {
            'enrollment_rows': rows,
            'search_query': query,
            'selected_status': status,
            'selected_type': content_type,
            **_teacher_base_context(),
        },
    )


@teacher_required
def analytics(request):
    courses = _teacher_courses_queryset(request.user)
    enrollments_qs = Enrollment.objects.filter(course__in=courses)
    quizzes = _teacher_quizzes_queryset(request.user)
    attempts = QuizAttempt.objects.filter(quiz__in=quizzes, is_completed=True)

    enrollment_rows = list(enrollments_qs)
    avg_progress = (
        sum(enrollment.progress_percentage for enrollment in enrollment_rows) / len(enrollment_rows)
        if enrollment_rows
        else 0
    )
    pass_rate = 0
    if attempts.exists():
        pass_rate = round((attempts.filter(is_passed=True).count() / attempts.count()) * 100, 2)

    courses_by_students = courses.annotate(student_count=Count('enrollments')).order_by('-student_count')
    analytics_payload = {
        'labels': [item.title for item in courses_by_students],
        'students': [item.student_count for item in courses_by_students],
    }

    context = {
        'total_students': enrollments_qs.values('user').distinct().count(),
        'total_enrollments': enrollments_qs.count(),
        'completed_courses': enrollments_qs.filter(is_completed=True).count(),
        'average_progress_value': round(avg_progress, 2),
        'quiz_pass_rate': pass_rate,
        'analytics_payload_json': json.dumps(analytics_payload),
    }
    context.update(_teacher_base_context())
    return render(request, 'teachers/analytics.html', context)


@teacher_required
def search(request):
    query = request.GET.get('q', '').strip()
    topic = request.GET.get('topic', '').strip()
    difficulty = request.GET.get('difficulty', '').strip()
    status = request.GET.get('status', '').strip()

    courses = _teacher_courses_queryset(request.user)
    quizzes = _teacher_quizzes_queryset(request.user)
    enrollments = Enrollment.objects.filter(course__in=courses).select_related('user', 'course')

    if query:
        courses = courses.filter(Q(title__icontains=query) | Q(description__icontains=query))
        quizzes = quizzes.filter(Q(title__icontains=query) | Q(description__icontains=query))
        enrollments = enrollments.filter(
            Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(user__email__icontains=query)
            | Q(course__title__icontains=query)
        )
    if topic:
        courses = courses.filter(topic__slug=topic)
        enrollments = enrollments.filter(course__topic__slug=topic)
    if difficulty:
        quizzes = quizzes.filter(difficulty=difficulty)
    if status == 'completed':
        enrollments = enrollments.filter(is_completed=True)
    elif status == 'in_progress':
        enrollments = enrollments.filter(is_completed=False)

    payload = {
        'courses': [{'id': item.id, 'title': item.title} for item in courses[:5]],
        'quizzes': [{'id': item.id, 'title': item.title} for item in quizzes[:5]],
        'students': [
            {
                'id': item.user.id,
                'name': item.user.get_full_name() or item.user.email,
                'course': item.course.title,
                'status': 'Completed' if item.is_completed else 'In Progress',
            }
            for item in enrollments[:5]
        ],
        'counts': {
            'courses': courses.count(),
            'quizzes': quizzes.count(),
            'students': enrollments.values('user').distinct().count(),
        },
        'generated_at': timezone.now().isoformat(),
    }
    return JsonResponse(payload)
