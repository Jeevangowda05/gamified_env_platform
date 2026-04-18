from django.contrib import admin
from django.contrib import messages
import json
from .models import Quiz, Question,  QuizCategory, QuizAttempt, CompetitiveChallenge


@admin.register(QuizCategory)
class QuizCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'quiz_type', 'difficulty', 'quiz_status', 'is_published', 'created_at']
    list_filter = ['quiz_type', 'difficulty', 'is_published', 'is_scheduled', 'category']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category', 'quiz_type', 'difficulty')
        }),
        ('Quiz Settings', {
            'fields': ('time_limit', 'max_attempts', 'passing_score')
        }),
        ('Gamification', {
            'fields': ('points_per_question', 'bonus_points')
        }),
        ('Availability', {
            'fields': ('is_published', 'is_featured', 'is_scheduled', 'scheduled_start_datetime', 'scheduled_end_datetime')
        }),
        ('Bulk Add Questions (JSON)', {
            'fields': ('bulk_questions_json',),
            'description': 'Paste JSON to bulk add questions. Format: {"questions": [{"question": "...", "points": 10, "option_a": "...", "option_b": "...", "option_c": "...", "option_d": "...", "correct_answer": "A"}]}'
        }),
    )
    
    def save_model(self, request, obj, form, change):
        # Set created_by to current user if it's a new object
        if not change:
            obj.created_by = request.user
        
        # Save the quiz first
        super().save_model(request, obj, form, change)
        
        # Check if JSON data was provided
        if obj.bulk_questions_json and obj.bulk_questions_json.strip():
            try:
                data = json.loads(obj.bulk_questions_json)
                questions_created = 0
                
                for item in data.get('questions', []):
                    # Create question with A/B/C/D options
                    question = Question.objects.create(
                        quiz=obj,
                        question_text=item['question'],
                        points=item.get('points', 10),
                        option_a=item.get('option_a', ''),
                        option_b=item.get('option_b', ''),
                        option_c=item.get('option_c', ''),
                        option_d=item.get('option_d', ''),
                        correct_answer=item.get('correct_answer', 'A'),
                        explanation=item.get('explanation', '')
                    )
                    questions_created += 1
                
                # Clear the JSON field after processing
                obj.bulk_questions_json = ''
                obj.save(update_fields=['bulk_questions_json'])
                
                messages.success(
                    request,
                    f'✅ Successfully created {questions_created} questions from JSON!'
                )
                
            except json.JSONDecodeError as e:
                messages.error(
                    request,
                    f'❌ Invalid JSON format: {str(e)}'
                )
            except Exception as e:
                messages.error(
                    request,
                    f'❌ Error creating questions: {str(e)}'
                )

    def quiz_status(self, obj):
        return obj.get_quiz_status_display_label()
    quiz_status.short_description = 'Status'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text_short', 'quiz', 'points', 'correct_answer', 'created_at']
    list_filter = ['quiz', 'correct_answer']
    search_fields = ['question_text']
    
    def question_text_short(self, obj):
        return obj.question_text[:50] + '...' if len(obj.question_text) > 50 else obj.question_text
    question_text_short.short_description = 'Question'


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'quiz', 'score_percentage', 'is_passed', 'completed_at']
    list_filter = ['is_passed', 'is_completed', 'quiz']
    search_fields = ['user__username', 'quiz__title']


@admin.register(CompetitiveChallenge)
class CompetitiveChallengeAdmin(admin.ModelAdmin):
    list_display = ['title', 'challenge_type', 'start_date', 'end_date', 'is_active']
    list_filter = ['challenge_type', 'is_active']
