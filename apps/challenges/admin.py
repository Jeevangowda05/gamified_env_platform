from django.contrib import admin
from django.utils.html import format_html
from .models import Challenge, ChallengeSubmission


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ['title', 'difficulty', 'points_reward', 'status', 'created_at']
    list_filter = ['status', 'difficulty', 'category']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ChallengeSubmission)
class ChallengeSubmissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'challenge', 'status_badge', 'submitted_at', 'reviewed_by', 'action_buttons']
    list_filter = ['status', 'submitted_at', 'challenge']
    search_fields = ['user__username', 'challenge__title']
    readonly_fields = ['submitted_at', 'reviewed_at', 'user', 'challenge', 'proof_file', 'description']
    
    # Separate fieldsets for viewing
    fieldsets = (
        ('Submission Details', {
            'fields': ('user', 'challenge', 'proof_file', 'description', 'submitted_at')
        }),
        ('Review Status', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'reviewer_notes')
        }),
    )
    
    def status_badge(self, obj):
        """Display status with color badge"""
        colors = {
            'pending': '#FFA500',   # Orange
            'approved': '#28a745',  # Green
            'rejected': '#dc3545',  # Red
        }
        color = colors.get(obj.status, '#grey')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def action_buttons(self, obj):
        """Display approve/reject buttons based on status"""
        if obj.status == 'pending':
            return format_html(
                '<a class="button" style="background-color: #28a745; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;" href="#" onclick="return approveSubmission({})">✓ Approve</a> '
                '<a class="button" style="background-color: #dc3545; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-left: 5px;" href="#" onclick="return rejectSubmission({})">✗ Reject</a>',
                obj.id, obj.id
            )
        elif obj.status == 'approved':
            return format_html('<span style="color: green; font-weight: bold;">✓ Approved</span>')
        else:
            return format_html('<span style="color: red; font-weight: bold;">✗ Rejected</span>')
    action_buttons.short_description = 'Actions'
    
    def save_model(self, request, obj, form, change):
        """Override save to call approve/reject methods"""
        # Check if status was changed
        if change:  # It's an existing object being edited
            original = ChallengeSubmission.objects.get(pk=obj.pk)
            
            # If status changed from pending to approved
            if original.status == 'pending' and obj.status == 'approved':
                obj.approve(request.user)
                return  # approve() already saves
            
            # If status changed from pending to rejected
            elif original.status == 'pending' and obj.status == 'rejected':
                obj.reject(request.user, obj.reviewer_notes)
                return  # reject() already saves
        
        # Normal save for other changes
        super().save_model(request, obj, form, change)
    
    actions = ['approve_selected', 'reject_selected']
    
    def approve_selected(self, request, queryset):
        """Bulk approve action"""
        count = 0
        for submission in queryset.filter(status='pending'):
            submission.approve(request.user)
            count += 1
        self.message_user(request, f'{count} submissions approved and points awarded!')
    approve_selected.short_description = "✓ Approve Selected Submissions"
    
    def reject_selected(self, request, queryset):
        """Bulk reject action"""
        count = 0
        for submission in queryset.filter(status='pending'):
            submission.reject(request.user, "Rejected via bulk action")
            count += 1
        self.message_user(request, f'{count} submissions rejected!')
    reject_selected.short_description = "✗ Reject Selected Submissions"
