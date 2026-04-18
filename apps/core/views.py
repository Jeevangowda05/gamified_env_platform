"""
Core views for the Gamified Environmental Education Platform
Handles main dashboard, home page, and core functionality
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView
from django.db.models import Count, Q, Avg
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import get_user_model
from .models import Course, Module, Lesson, Enrollment, LessonProgress, Certificate
from apps.core.models import Topic
from django.shortcuts import get_object_or_404
from apps.gamification.models import UserProgress, UserBadge
from apps.teachers.models import StudentNotification, TeacherNotification
from apps.teachers.utils import create_teacher_notification_for_course
from django.views.decorators.http import require_POST
from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status


def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug)
    enrollment = None
    progress_percentage = 0
    
    if request.user.is_authenticated:
        try:
            enrollment = Enrollment.objects.get(user=request.user, course=course)
            progress_percentage = enrollment.progress_percentage
        except Enrollment.DoesNotExist:
            enrollment = None
    
    context = {
        'course': course,
        'enrollment': enrollment,
        'progress_percentage': progress_percentage,
    }
    return render(request, 'core/course_detail.html', context)


def course_list(request):
    courses = Course.objects.select_related('topic').filter(topic__slug__isnull=False)
    
    if not courses.exists():
        courses = Course.objects.all()

    return render(request, 'core/course_list.html', {'courses': courses})


def complete_course(request, course_id):
    progress, created = UserProgress.objects.get_or_create(user=request.user)
    progress.total_points += course_points
    progress.course_points += course_points
    progress.courses_completed += 1
    progress.update_streak()
    progress.save()
    progress.check_badge_eligibility()


# ===== NEW COURSE LEARNING VIEWS WITH VIDEO FILE SUPPORT =====
@login_required
def enroll_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    enrollment, created = Enrollment.objects.get_or_create(
        user=request.user,
        course=course
    )
    
    if created:
        messages.success(request, f'Successfully enrolled in {course.title}!')
        create_teacher_notification_for_course(
            course=course,
            actor=request.user,
            event_type='course_enrollment',
            title='New course enrollment',
            message=f'{request.user.get_full_name() or request.user.email} enrolled in {course.title}.',
        )
    
    return redirect('core:course_learn', slug=course.slug)


@login_required
def course_learn(request, slug):
    course = get_object_or_404(Course, slug=slug)
    enrollment = get_object_or_404(Enrollment, user=request.user, course=course)
    
    modules = course.modules.prefetch_related('lessons').all()
    
    requested_lesson_id = request.GET.get('lesson')
    current_lesson = None
    
    if requested_lesson_id:
        try:
            current_lesson = Lesson.objects.get(id=requested_lesson_id, module__course=course)
        except Lesson.DoesNotExist:
            pass
    
    if not current_lesson:
        for module in modules:
            for lesson in module.lessons.all():
                lesson_progress, _ = LessonProgress.objects.get_or_create(
                    enrollment=enrollment,
                    lesson=lesson
                )
                if not lesson_progress.is_completed:
                    current_lesson = lesson
                    break
            if current_lesson:
                break
    
    if not current_lesson and modules.exists():
        current_lesson = modules.first().lessons.first()

    current_lesson_progress = None
    if current_lesson:
        current_lesson_progress, _ = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=current_lesson,
        )
    
    all_lessons = []
    for module in modules:
        for lesson in module.lessons.all().order_by('order'):
            all_lessons.append(lesson)
    
    previous_lesson = None
    next_lesson = None
    if current_lesson:
        for i, lesson in enumerate(all_lessons):
            if lesson.id == current_lesson.id:
                previous_lesson = all_lessons[i - 1] if i > 0 else None
                next_lesson = all_lessons[i + 1] if i < len(all_lessons) - 1 else None
                break

    # ===== FIX: Sidebar lesson completion & progress bar context =====
    completed_lessons_set = set(
        enrollment.lesson_progress.filter(is_completed=True).values_list('lesson_id', flat=True)
    )
    total_lessons = len(all_lessons)
    completed_count = len(completed_lessons_set)
    course_points = sum([
        getattr(lesson, 'points_value', 25)
        for module in modules
        for lesson in module.lessons.all()
    ])
    current_lesson_num = all_lessons.index(current_lesson) + 1 if current_lesson in all_lessons else 1
    
    # ===== Video file data =====
    video_data = {
        'has_video': current_lesson.has_video_content() if current_lesson else False,
        'video_type': current_lesson.get_video_type() if current_lesson else None,
        'video_file': current_lesson.video_file if current_lesson else None,
        'video_url': current_lesson.video_url if current_lesson else None,
    }
    
    context = {
        'course': course,
        'enrollment': enrollment,
        'modules': modules,
        'current_lesson': current_lesson,
        'previous_lesson': previous_lesson,
        'next_lesson': next_lesson,
        'progress_percentage': enrollment.progress_percentage,
        'video_data': video_data,
        'completed_lessons_set': completed_lessons_set,
        'total_lessons': total_lessons,
        'completed_count': completed_count,
        'course_points': course_points,
        'current_lesson_num': current_lesson_num,
        'current_lesson_progress': current_lesson_progress,
    }
    return render(request, 'core/course_learn.html', context)


@login_required
def lesson_detail(request, slug, lesson_id):
    course = get_object_or_404(Course, slug=slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course)
    enrollment = get_object_or_404(Enrollment, user=request.user, course=course)
    
    lesson_progress, created = LessonProgress.objects.get_or_create(
        enrollment=enrollment,
        lesson=lesson
    )
    
    modules = course.modules.prefetch_related('lessons').all()
    all_lessons = []
    for module in modules:
        for lesson_item in module.lessons.all().order_by('order'):
            all_lessons.append(lesson_item)
    
    current_index = None
    for i, lesson_item in enumerate(all_lessons):
        if lesson_item.id == lesson.id:
            current_index = i
            break
    
    previous_lesson = all_lessons[current_index - 1] if current_index and current_index > 0 else None
    next_lesson = all_lessons[current_index + 1] if current_index is not None and current_index < len(all_lessons) - 1 else None
    
    total_lessons = len(all_lessons)
    completed_lessons = enrollment.lesson_progress.filter(is_completed=True).count()
    progress_percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
    
    video_data = {
        'has_video': lesson.has_video_content(),
        'video_type': lesson.get_video_type(),
        'video_file': lesson.video_file,
        'video_url': lesson.video_url,
    }
    
    context = {
        'course': course,
        'lesson': lesson,
        'enrollment': enrollment,
        'lesson_progress': lesson_progress,
        'modules': modules,
        'previous_lesson': previous_lesson,
        'next_lesson': next_lesson,
        'progress_percentage': progress_percentage,
        'video_data': video_data,
    }
    return render(request, 'lesson_detail.html', context)


def _finalize_lesson_completion(request, enrollment, course, lesson, lesson_progress):
    if lesson_progress.is_completed:
        return False, enrollment.is_completed

    lesson_progress.is_completed = True
    lesson_progress.completed_at = timezone.now()
    lesson_progress.save(update_fields=['is_completed', 'completed_at', 'lesson_watched', 'watched_duration'])

    from apps.gamification.utils import award_points

    lesson_points = getattr(lesson, 'points_value', 25)
    award_points(
        user=request.user,
        points=lesson_points,
        reason=f'Completed lesson: {lesson.title}',
        content_type='lesson',
        object_id=lesson.id
    )

    total_lessons = Lesson.objects.filter(module__course=course).count()
    completed_lessons = enrollment.lesson_progress.filter(is_completed=True).count()

    if completed_lessons == total_lessons:
        enrollment.is_completed = True
        enrollment.completed_at = timezone.now()
        enrollment.save()
        create_teacher_notification_for_course(
            course=course,
            actor=request.user,
            event_type='course_completed',
            title='Course completed',
            message=f'{request.user.get_full_name() or request.user.email} completed {course.title}.',
        )

        course_points = getattr(course, 'completion_points', 150)
        award_points(
            user=request.user,
            points=course_points,
            reason=f'Completed course: {course.title}',
            content_type='course',
            object_id=course.id
        )

        if request.user.user_type == 'student':
            progress, created = UserProgress.objects.get_or_create(user=request.user)
            progress.courses_completed += 1
            progress.save()

        Certificate.objects.get_or_create(
            user=request.user,
            course=course
        )

        return True, True

    return True, False


@login_required
@require_POST
def complete_lesson(request, slug, lesson_id):
    course = get_object_or_404(Course, slug=slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course)
    enrollment = get_object_or_404(Enrollment, user=request.user, course=course)
    
    lesson_progress, created = LessonProgress.objects.get_or_create(
        enrollment=enrollment,
        lesson=lesson
    )
    
    if lesson.lesson_type == 'video' and not lesson_progress.lesson_watched:
        messages.error(request, 'Please finish the video to unlock the next lesson.')
        return redirect('core:course_learn', slug=course.slug)

    if lesson.lesson_type != 'video':
        lesson_progress.lesson_watched = True

    newly_completed, course_completed = _finalize_lesson_completion(
        request=request,
        enrollment=enrollment,
        course=course,
        lesson=lesson,
        lesson_progress=lesson_progress,
    )

    if newly_completed and course_completed:
        course_points = getattr(course, 'completion_points', 150)
        messages.success(request, f'Congratulations! You completed {course.title} and earned {course_points} points!')
        return redirect('core:course_certificate', slug=course.slug)
    
    return redirect('core:course_learn', slug=course.slug)


@login_required
@require_POST
def complete_lesson_api(request, slug, lesson_id):
    course = get_object_or_404(Course, slug=slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course)
    enrollment = get_object_or_404(Enrollment, user=request.user, course=course)
    lesson_progress, _ = LessonProgress.objects.get_or_create(
        enrollment=enrollment,
        lesson=lesson
    )

    video_completed = request.POST.get('video_completed') == 'true'
    if lesson.lesson_type == 'video' and not video_completed:
        return JsonResponse(
            {'success': False, 'message': 'Video must be completed before advancing.'},
            status=400,
        )
    lesson_progress.lesson_watched = True

    try:
        watched_duration = int(request.POST.get('watched_duration', 0) or 0)
    except (TypeError, ValueError):
        watched_duration = 0
    if watched_duration > 0:
        lesson_progress.watched_duration = max(lesson_progress.watched_duration, watched_duration)

    newly_completed, course_completed = _finalize_lesson_completion(
        request=request,
        enrollment=enrollment,
        course=course,
        lesson=lesson,
        lesson_progress=lesson_progress,
    )

    all_lessons = list(
        Lesson.objects.filter(module__course=course)
        .select_related('module')
        .order_by('module__order', 'order')
    )
    next_lesson = None
    for index, lesson_item in enumerate(all_lessons):
        if lesson_item.id == lesson.id and index < len(all_lessons) - 1:
            next_lesson = all_lessons[index + 1]
            break

    return JsonResponse(
        {
            'success': True,
            'completed': lesson_progress.is_completed,
            'newly_completed': newly_completed,
            'course_completed': course_completed,
            'progress_percentage': enrollment.progress_percentage,
            'next_lesson_url': (
                f"{reverse('core:course_learn', kwargs={'slug': course.slug})}?lesson={next_lesson.id}"
                if next_lesson
                else ''
            ),
        }
    )


@login_required
def course_certificate(request, slug):
    course = get_object_or_404(Course, slug=slug)
    certificate = get_object_or_404(Certificate, user=request.user, course=course)
    
    context = {
        'course': course,
        'certificate': certificate,
    }
    return render(request, 'core/certificate.html', context)


@login_required
def submit_quiz(request, slug, lesson_id):
    course = get_object_or_404(Course, slug=slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course)
    enrollment = get_object_or_404(Enrollment, user=request.user, course=course)
    
    if request.method == 'POST':
        score = 100
        
        lesson_progress, created = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson
        )
        lesson_progress.is_completed = True
        lesson_progress.completed_at = timezone.now()
        lesson_progress.quiz_score = score
        lesson_progress.save()
        
        messages.success(request, f'Quiz completed! Score: {score}%')
        
    return redirect('core:course_learn', slug=course.slug)


# ===== END NEW COURSE LEARNING VIEWS =====

def topic_list(request):
    topics = Topic.objects.filter(is_active=True).order_by('order', 'name')
    
    return render(request, 'core/topic_list.html', {
        'topics': topics
    })


def topic_detail(request, slug):
    topic = get_object_or_404(Topic, slug=slug, is_active=True)
    all_courses = topic.courses.all()
    
    context = {
        'topic': topic,
        'courses': all_courses,
        'total_courses': all_courses.count(),
        'total_learners': 0,
    }
    return render(request, 'core/topic_detail.html', context)


User = get_user_model()


class HomeView(TemplateView):
    """Landing page for the platform"""
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['stats'] = {
            'total_learners': User.objects.filter(user_type='student').count(),
            'total_courses': Course.objects.count(),
            'total_topics': Topic.objects.count(),
            'certificates_issued': Certificate.objects.count(),
        }

        return context


class DashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard for authenticated users"""
    template_name = 'core/dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.user_type == 'teacher':
            return redirect('teacher:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        user_enrollments = Enrollment.objects.filter(user=user)
        context['total_enrollments'] = user_enrollments.count()
        context['completed_courses'] = user_enrollments.filter(is_completed=True).count()
        context['badges_earned'] = Certificate.objects.filter(user=user).count()
        
        in_progress = user_enrollments.filter(is_completed=False)
        context['in_progress_courses'] = []
        
        UserModel = get_user_model()
        leaderboard = UserModel.objects.filter(
            is_active=True,
            user_type='student',
            show_on_leaderboard=True,
        ).order_by('-progress__total_points')

        user_rank = None
        for idx, ranked_user in enumerate(leaderboard, start=1):
            if ranked_user.id == user.id:
                user_rank = idx
                break

        context['user_rank'] = user_rank
        context['rank_change'] = 5 if user_rank else 0
        
        for enrollment in in_progress:
            total_lessons = Lesson.objects.filter(module__course=enrollment.course).count()
            completed_lessons = enrollment.lesson_progress.filter(is_completed=True).count()
            
            if total_lessons > 0:
                progress_percentage = (completed_lessons / total_lessons) * 100
                
                first_incomplete = None
                for module in enrollment.course.modules.all():
                    for lesson in module.lessons.all():
                        lesson_progress, _ = LessonProgress.objects.get_or_create(
                            enrollment=enrollment, lesson=lesson
                        )
                        if not lesson_progress.is_completed:
                            first_incomplete = lesson
                            break
                    if first_incomplete:
                        break
                
                context['in_progress_courses'].append({
                    'enrollment': enrollment,
                    'progress_percentage': progress_percentage,
                    'first_incomplete_lesson': first_incomplete,
                })

        recent_activities = []
        
        recent_lessons = LessonProgress.objects.filter(
            enrollment__user=user, is_completed=True
        ).order_by('-completed_at')[:5]
        
        for lesson_progress in recent_lessons:
            if lesson_progress.completed_at:
                recent_activities.append({
                    'type': 'lesson_completed',
                    'title': f'Completed lesson: {lesson_progress.lesson.title}',
                    'course': lesson_progress.enrollment.course.title,
                    'date': lesson_progress.completed_at,
                })
        
        recent_enrollments = user_enrollments.order_by('-enrolled_at')[:3]
        for enrollment in recent_enrollments:
            recent_activities.append({
                'type': 'enrolled',
                'title': f'Enrolled in: {enrollment.course.title}',
                'course': enrollment.course.title,
                'date': enrollment.enrolled_at,
            })
        
        recent_activities.sort(key=lambda x: x['date'], reverse=True)
        context['recent_activities'] = recent_activities[:5]

        if user.user_type == 'student':
            progress, _ = UserProgress.objects.get_or_create(user=user)
            context['level'] = progress.get_level
            context['total_points'] = progress.total_points
            context['total_badges'] = UserBadge.objects.filter(user=user).count()
        else:
            context['level'] = 0
            context['total_points'] = 0
            context['total_badges'] = 0

        return context


class LeaderboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/leaderboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.gamification.models import UserProgress, UserBadge

        User = get_user_model()
        users = User.objects.filter(is_active=True, user_type='student', show_on_leaderboard=True)

        user_rows = []
        for user in users:
            try:
                progress = user.progress
            except Exception:
                progress, _ = UserProgress.objects.get_or_create(user=user)
            badges_count = UserBadge.objects.filter(user=user).count()
            courses_completed = getattr(progress, 'courses_completed', 0)
            user_rows.append({
                'user': user,
                'full_name': getattr(user, 'get_full_name', lambda: user.username)(),
                'institution': getattr(user, 'institution', ''),
                'points': progress.total_points,
                'level': getattr(progress, 'get_level', lambda: 1)() if hasattr(progress, 'get_level') else 1,
                'badges': badges_count,
                'courses_completed': courses_completed
            })

        user_rows.sort(key=lambda v: v['points'], reverse=True)
        for idx, ur in enumerate(user_rows):
            ur['rank'] = idx + 1

        context['leaderboard'] = user_rows
        return context


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'core/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.user_type == 'student':
            progress, _ = UserProgress.objects.get_or_create(user=user)
            points_value = progress.total_points
            level = progress.get_level() if hasattr(progress, 'get_level') else 1
        else:
            points_value = 0
            level = 0
        
        enrollments = Enrollment.objects.filter(user=user)
        courses_completed = enrollments.filter(is_completed=True).count()
        
        try:
            from apps.assessments.models import QuizAttempt
            quiz_attempts = QuizAttempt.objects.filter(user=user)
            quizzes_taken = quiz_attempts.values('quiz').distinct().count()
            avg_score = quiz_attempts.aggregate(Avg('score'))['score__avg'] or 0
        except:
            quizzes_taken = 0
            avg_score = 0
        
        points_for_next = (level + 1) * 250
        level_progress = int((points_value % 250) / 250 * 100) if points_value else 0
        
        co2_saved = courses_completed * 61
        water_saved = courses_completed * 312
        waste_recycled = courses_completed * 21
        
        recent_activities = []
        recent_lessons = LessonProgress.objects.filter(
            enrollment__user=user, is_completed=True
        ).order_by('-completed_at')[:5]
        for lp in recent_lessons:
            recent_activities.append({
                'title': f'Completed lesson: {lp.lesson.title}',
                'description': lp.enrollment.course.title,
                'time': f'{(timezone.now() - lp.completed_at).days} days ago' if lp.completed_at else 'Recently',
                'points': 25,
                'icon': 'fa-graduation-cap',
                'icon_color': 'text-info'
            })
        
        recent_badges_qs = UserBadge.objects.filter(user=user).order_by('-earned_at')[:3]
        recent_badges = []
        for ub in recent_badges_qs:
            recent_badges.append({
                'name': ub.badge.name,
                'icon': 'fa-medal',
                'color': 'text-warning',
                'earned_at': f'{(timezone.now() - ub.earned_at).days} days ago' if ub.earned_at else 'Recently'
            })
        
        context.update({
            'user_level': level,
            'user_points': points_value,
            'user_badges': UserBadge.objects.filter(user=user).count() if user.user_type == 'student' else 0,
            'courses_completed': courses_completed,
            'quizzes_taken': quizzes_taken,
            'avg_quiz_score': round(avg_score, 1),
            'level_progress': level_progress,
            'points_to_next_level': points_for_next,
            'co2_saved': co2_saved,
            'water_saved': water_saved,
            'waste_recycled': waste_recycled,
            'recent_activities': recent_activities,
            'recent_badges': recent_badges,
        })
        
        return context


class PublicProfileView(TemplateView):
    """Public profile view for any user (minimal info only)"""
    template_name = 'core/public_profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        username = self.kwargs.get('username')
        profile_user = get_object_or_404(User, username=username)
        
        if profile_user.user_type == 'student':
            progress, _ = UserProgress.objects.get_or_create(user=profile_user)
            points_value = progress.total_points
            level = progress.get_level() if hasattr(progress, 'get_level') else 1
            badges_count = UserBadge.objects.filter(user=profile_user).count()
        else:
            points_value = 0
            level = 0
            badges_count = 0
        
        enrollments = Enrollment.objects.filter(user=profile_user)
        courses_completed = enrollments.filter(is_completed=True).count()
        
        context.update({
            'profile_user': profile_user,
            'user_level': level,
            'user_points': points_value,
            'user_badges': badges_count,
            'courses_completed': courses_completed,
        })
        
        return context


class DashboardStatsAPIView(APIView):
    """API endpoint for dashboard statistics"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        stats = {
            'user_level': user.level,
            'total_points': user.total_points,
            'level_progress': user.get_level_progress(),
            'total_enrollments': 0,
            'completed_courses': 0,
            'in_progress_courses': 0,
            'badges_earned': 0,
            'certificates_earned': 0,
        }

        stats['recent_points'] = []

        return Response(stats)


class UserActivityAPIView(APIView):
    """API endpoint for user activity feed"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        page = int(request.GET.get('page', 1))

        activities = []

        return Response({
            'activities': activities,
            'page': page,
            'has_next': False,
            'total': 0
        })


class NotificationAPIView(APIView):
    """API endpoint for user notifications"""
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _apply_filter(queryset, filter_value):
        if filter_value == 'archived':
            return queryset.filter(is_archived=True)
        if filter_value == 'all':
            return queryset.filter(is_archived=False)
        return queryset.filter(is_archived=False, is_read=False)

    def get(self, request):
        filter_value = request.GET.get('filter', 'unread')
        if request.user.user_type == 'teacher':
            notifications_qs = TeacherNotification.objects.filter(
                teacher=request.user
            ).select_related('actor')
            unread_count = notifications_qs.filter(is_read=False, is_archived=False).count()
            notifications = self._apply_filter(notifications_qs, filter_value)[:20]
            notifications = [
                {
                    'id': item.id,
                    'type': item.event_type,
                    'title': item.title,
                    'message': item.message,
                    'timestamp': item.created_at.isoformat(),
                    'actor': item.actor.get_full_name() if item.actor else '',
                    'is_read': item.is_read,
                    'is_archived': item.is_archived,
                }
                for item in notifications
            ]
        else:
            notifications_qs = StudentNotification.objects.filter(
                recipient=request.user
            ).select_related('actor')
            unread_count = notifications_qs.filter(is_read=False, is_archived=False).count()
            notifications = self._apply_filter(notifications_qs, filter_value)[:20]
            notifications = [
                {
                    'id': item.id,
                    'type': item.event_type,
                    'title': item.title,
                    'message': item.message,
                    'timestamp': item.created_at.isoformat(),
                    'actor': item.actor.get_full_name() if item.actor else '',
                    'is_read': item.is_read,
                    'is_archived': item.is_archived,
                }
                for item in notifications
            ]

        return Response({
            'notifications': notifications,
            'unread_count': unread_count
        })

    def post(self, request):
        action = request.data.get('action')
        notification_id = request.data.get('notification_id')
        if request.user.user_type == 'teacher':
            notifications_qs = TeacherNotification.objects.filter(teacher=request.user)
        else:
            notifications_qs = StudentNotification.objects.filter(recipient=request.user)

        if action == 'mark_read' and notification_id:
            notifications_qs.filter(id=notification_id).update(is_read=True)
        elif action == 'mark_all_read':
            notifications_qs.filter(is_archived=False, is_read=False).update(is_read=True)
        elif action == 'archive' and notification_id:
            notifications_qs.filter(id=notification_id).update(is_archived=True, is_read=True)
        else:
            return Response({'detail': 'Invalid action.'}, status=status.HTTP_400_BAD_REQUEST)

        unread_count = notifications_qs.filter(is_read=False, is_archived=False).count()
        return Response({'success': True, 'unread_count': unread_count})


def health_check(request):
    """Health check endpoint"""
    return JsonResponse({'status': 'healthy', 'timestamp': timezone.now().isoformat()})


def robots_txt(request):
    """Robots.txt file"""
    lines = [
        "User-Agent: *",
        "Disallow: /admin/",
        "Disallow: /api/",
        "",
        "Sitemap: https://ecolearn.edu/sitemap.xml"
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
