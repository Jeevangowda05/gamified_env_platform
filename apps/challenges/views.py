from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from .models import Challenge, ChallengeSubmission
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from apps.teachers.utils import create_teacher_notifications_for_challenge_submission


# ============================================================================
# CHALLENGE LIST VIEW
# ============================================================================


class ChallengeListView(LoginRequiredMixin, ListView):
    """Display all available challenges"""
    model = Challenge
    template_name = 'challenges/challenge_list.html'
    context_object_name = 'challenges'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Challenge.objects.filter(status='active')
        
        # Filter by category
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by difficulty
        difficulty = self.request.GET.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user's submissions
        context['my_submissions'] = ChallengeSubmission.objects.filter(user=user)
        context['completed_challenges'] = set(
            s.challenge_id for s in context['my_submissions'] 
            if s.status == 'approved'
        )
        
        return context



class ChallengeDetailView(LoginRequiredMixin, DetailView):
    """Display challenge details"""
    model = Challenge
    template_name = 'challenges/challenge_detail.html'
    context_object_name = 'challenge'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        challenge = self.get_object()
        
        # Check if user already submitted
        context['user_submission'] = ChallengeSubmission.objects.filter(
            user=user,
            challenge=challenge
        ).first()
        
        # Split instructions by newline to display as list
        instructions_list = [
            line.strip() for line in challenge.instructions.split('\n') 
            if line.strip()
        ]
        context['instructions_list'] = instructions_list
        
        return context
    



# ============================================================================
# SUBMISSION VIEWS
# ============================================================================


@login_required
def submit_challenge(request, pk):
    """Submit challenge proof"""
    challenge = get_object_or_404(Challenge, pk=pk, status='active')
    user = request.user
    
    # Check if already submitted
    existing = ChallengeSubmission.objects.filter(user=user, challenge=challenge).first()
    
    if request.method == 'POST':
        # If already submitted, show message
        if existing and existing.status == 'approved':
            messages.error(request, "You have already completed this challenge!")
            return redirect('challenges:challenge_detail', pk=pk)
        
        # Get form data
        proof_file = request.FILES.get('proof_file')
        description = request.POST.get('description', '')
        
        if not proof_file:
            messages.error(request, "Please upload proof file (image or PDF)")
            return redirect('challenges:challenge_detail', pk=pk)
        
        # Create or update submission
        if existing:
            existing.proof_file = proof_file
            existing.description = description
            existing.status = 'pending'
            existing.save()
            create_teacher_notifications_for_challenge_submission(actor=user, challenge=challenge)
            messages.info(request, "Submission updated! Waiting for verification...")
        else:
            submission = ChallengeSubmission.objects.create(
                user=user,
                challenge=challenge,
                proof_file=proof_file,
                description=description
            )
            create_teacher_notifications_for_challenge_submission(actor=user, challenge=challenge)
            messages.success(request, "Challenge submitted! Waiting for verification from admins...")
        
        return redirect('challenges:challenge_detail', pk=pk)
    
    context = {
        'challenge': challenge,
        'existing_submission': existing,
    }
    return render(request, 'challenges/submit_challenge.html', context)



@login_required
def my_submissions(request):
    """View user's challenge submissions"""
    submissions = ChallengeSubmission.objects.filter(user=request.user).select_related('challenge')
    
    context = {
        'submissions': submissions,
        'pending_count': submissions.filter(status='pending').count(),
        'approved_count': submissions.filter(status='approved').count(),
        'rejected_count': submissions.filter(status='rejected').count(),
    }
    return render(request, 'challenges/my_submissions.html', context)



# ============================================================================
# ADMIN VERIFICATION VIEWS
# ============================================================================


@login_required
def admin_verify_submissions(request):
    """Admin panel to verify submissions"""
    if not request.user.is_staff:
        messages.error(request, "Access denied!")
        return redirect('core:home')
    
    # Get pending submissions
    pending = ChallengeSubmission.objects.filter(status='pending').select_related('user', 'challenge')
    approved = ChallengeSubmission.objects.filter(status='approved').select_related('user', 'challenge')
    rejected = ChallengeSubmission.objects.filter(status='rejected').select_related('user', 'challenge')
    
    context = {
        'pending': pending,
        'approved': approved,
        'rejected': rejected,
        'pending_count': pending.count(),
    }
    return render(request, 'challenges/admin_verify.html', context)



@require_POST
@login_required
def approve_submission(request, submission_id):
    """Approve a submission"""
    if not request.user.is_staff:
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)
    
    submission = get_object_or_404(ChallengeSubmission, pk=submission_id)
    submission.approve(request.user)
    
    return JsonResponse({
        'status': 'success',
        'message': f"✓ Approved! {submission.user.first_name} earned {submission.challenge.points_reward} points"
    })



@require_POST
@login_required
def reject_submission(request, submission_id):
    """Reject a submission"""
    if not request.user.is_staff:
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)
    
    submission = get_object_or_404(ChallengeSubmission, pk=submission_id)
    notes = request.POST.get('notes', 'Proof does not meet requirements')
    submission.reject(request.user, notes)
    
    return JsonResponse({
        'status': 'success',
        'message': '✗ Rejected! User notified.'
    })
