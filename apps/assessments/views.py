from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.contrib import messages
import json

from apps.gamification.utils import award_points
from apps.gamification.models import UserProgress
from apps.teachers.utils import create_teacher_notification_for_quiz
from .models import (
    Quiz,
    QuizCategory,
    CompetitiveChallenge,
    Question,
    QuizAttempt,
    QuizResponse,
)

class QuizListView(ListView):
    model = Quiz
    template_name = 'assessments/quiz_list.html'
    context_object_name = 'quizzes'
    paginate_by = 12
    def get_queryset(self):
        return Quiz.objects.filter(is_published=True).select_related('category')

class QuizDetailView(LoginRequiredMixin, DetailView):
    model = Quiz
    template_name = 'assessments/quiz_detail.html'
    context_object_name = 'quiz'

    def get_queryset(self):
        return Quiz.objects.filter(is_published=True).select_related('category')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiz = self.get_object()
        user_attempts = QuizAttempt.objects.filter(user=self.request.user, quiz=quiz).count()
        quiz_status = quiz.get_quiz_status()
        context['user_attempts'] = user_attempts
        context['attempts_left'] = max(0, (quiz.max_attempts or 0) - user_attempts)
        context['questions_count'] = quiz.questions.count()
        context['quiz_status'] = quiz_status
        context['quiz_is_live'] = quiz_status == Quiz.QUIZ_STATUS_LIVE
        context['scheduled_start_iso'] = quiz.scheduled_start_datetime.isoformat() if quiz.scheduled_start_datetime else ''
        context['scheduled_end_iso'] = quiz.scheduled_end_datetime.isoformat() if quiz.scheduled_end_datetime else ''
        return context

@login_required
def start_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id, is_published=True)
    quiz_status = quiz.get_quiz_status()
    if quiz_status != Quiz.QUIZ_STATUS_LIVE:
        if quiz_status == Quiz.QUIZ_STATUS_SCHEDULED:
            return HttpResponseForbidden('Quiz not yet available.')
        if quiz_status == Quiz.QUIZ_STATUS_CLOSED:
            return HttpResponseForbidden('Quiz is closed.')
        return HttpResponseForbidden('Quiz is not available.')

    attempt_count = QuizAttempt.objects.filter(
        user=request.user,
        quiz=quiz
    ).count()
    if attempt_count >= quiz.max_attempts:
        messages.error(request, 'You have used all attempts for this quiz.')
        return redirect('assessments:quiz_detail', pk=quiz_id)
    total_questions = Question.objects.filter(quiz=quiz).count()
    if total_questions == 0:
        messages.error(request, 'This quiz has no questions yet.')
        return redirect('assessments:quiz_detail', pk=quiz_id)
    attempt = QuizAttempt.objects.create(
        user=request.user,
        quiz=quiz,
        attempt_number=attempt_count + 1,
        total_questions=total_questions,
        is_completed=False
    )
    return redirect('assessments:take_quiz', attempt_id=attempt.id)

@login_required
def take_quiz(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, pk=attempt_id, user=request.user)
    quiz = attempt.quiz
    questions = Question.objects.filter(quiz=quiz).order_by('created_at')
    print(f'Quiz pk: {quiz.pk}, Questions found: {questions.count()}')
    if attempt.is_completed:
        return redirect('assessments:quiz_result', attempt_id=attempt.id)
    context = {
        'attempt': attempt,
        'quiz': quiz,
        'questions': questions,
    }
    return render(request, 'assessments/take_quiz.html', context)

@login_required
def submit_quiz(request, attempt_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user, is_completed=False)
    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
        answers = payload.get('answers', {})
        correct_count = 0
        total_questions = attempt.quiz.questions.count()
        for qid, selected_answer in answers.items():
            try:
                qid_val = int(qid)
            except (TypeError, ValueError):
                qid_val = qid
            question = get_object_or_404(Question, id=qid_val, quiz=attempt.quiz)
            selected = str(selected_answer).strip().upper() if selected_answer is not None else None
            is_correct = bool(selected) and (selected == question.correct_answer)
            if is_correct:
                correct_count += 1
            QuizResponse.objects.create(
                attempt=attempt,
                question=question,
                selected_answer=selected,
                is_correct=is_correct,
            )
        score_percentage = (correct_count / total_questions) * 100 if total_questions > 0 else 0
        is_passed = score_percentage >= (attempt.quiz.passing_score or 0)
        points_per_q = getattr(attempt.quiz, 'points_per_question', 0) or 0
        bonus = getattr(attempt.quiz, 'bonus_points', 0) or 0
        points_earned = correct_count * points_per_q
        # Award bonus only for passed attempts
        if is_passed:
            points_earned += bonus
        attempt.completed_at = timezone.now()
        attempt.correct_answers = correct_count
        attempt.score_percentage = score_percentage
        attempt.is_completed = True
        attempt.is_passed = is_passed
        attempt.points_earned = points_earned
        attempt.save()
        create_teacher_notification_for_quiz(
            quiz=attempt.quiz,
            actor=request.user,
            event_type='quiz_completed',
            title='Quiz completed',
            message=f'{request.user.get_full_name() or request.user.email} completed {attempt.quiz.title} with {score_percentage:.1f}%.',
        )
        # Only award if not already awarded (avoid duplicates)
        if points_earned > 0:
            reason = f'Completed quiz: {attempt.quiz.title}'
            if is_passed:
                reason += f' (PASSED with {score_percentage:.1f}%)'
            else:
                reason += f' ({score_percentage:.1f}%)'
            # Award all points (quiz + bonus) in a single transaction
            award_points(
                user=request.user,
                points=points_earned,
                reason=reason,
                content_type='quiz',
                object_id=attempt.quiz.id,
                transaction_type='earned'
            )
        if request.user.user_type == 'student':
            progress, created = UserProgress.objects.get_or_create(user=request.user)
            progress.quizzes_completed += 1
            if is_passed:
                progress.quizzes_passed += 1
            progress.save()
        return JsonResponse({
            'success': True,
            'score_percentage': score_percentage,
            'correct_answers': correct_count,
            'total_questions': total_questions,
            'is_passed': is_passed,
            'points_earned': points_earned,
        })
    except Exception as exc:
        return JsonResponse({'error': str(exc)}, status=500)

@login_required
def quiz_result(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user, is_completed=True)
    responses = attempt.responses.select_related('question').all()
    context = {
        'attempt': attempt,
        'responses': responses,
        'quiz': attempt.quiz,
    }
    return render(request, 'assessments/quiz_result.html', context)

# Remove the duplicate or legacy complete_quiz view.


@login_required
def quiz_status(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id, is_published=True)
    status_value = quiz.get_quiz_status()
    return JsonResponse(
        {
            'status': status_value,
            'status_label': quiz.get_quiz_status_display_label(),
            'is_live': status_value == Quiz.QUIZ_STATUS_LIVE,
            'scheduled_start_datetime': (
                quiz.scheduled_start_datetime.isoformat() if quiz.scheduled_start_datetime else None
            ),
            'scheduled_end_datetime': (
                quiz.scheduled_end_datetime.isoformat() if quiz.scheduled_end_datetime else None
            ),
        }
    )

class ChallengeListView(LoginRequiredMixin, ListView):
    model = CompetitiveChallenge
    template_name = 'assessments/challenge_list.html'
    context_object_name = 'challenges'
    def get_queryset(self):
        return CompetitiveChallenge.objects.filter(is_active=True)
