from django import forms
from django.utils import timezone

from apps.assessments.models import Question, Quiz
from apps.core.models import Course, Lesson, Module


class CourseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

    class Meta:
        model = Course
        fields = [
            'title',
            'description',
            'topic',
            'duration',
            'completion_points',
            'thumbnail',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class ModuleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

    class Meta:
        model = Module
        fields = ['title', 'description', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }


class ModuleEditForm(ModuleForm):
    class Meta(ModuleForm.Meta):
        fields = ['title', 'description', 'order']


class LessonForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault('class', 'form-check-input')
            else:
                field.widget.attrs.setdefault('class', 'form-control')

    class Meta:
        model = Lesson
        fields = [
            'title',
            'lesson_type',
            'content',
            'video_url',
            'video_file',
            'pdf_file',
            'image',
            'duration_minutes',
            'points_value',
            'order',
        ]
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
        }


class LessonEditForm(LessonForm):
    class Meta(LessonForm.Meta):
        fields = [
            'title',
            'lesson_type',
            'content',
            'video_url',
            'video_file',
            'pdf_file',
            'image',
            'duration_minutes',
            'points_value',
            'order',
        ]

class QuizForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault('class', 'form-check-input')
            else:
                field.widget.attrs.setdefault('class', 'form-control')
        for field_name in ('scheduled_start_datetime', 'scheduled_end_datetime'):
            value = self.initial.get(field_name) or getattr(self.instance, field_name, None)
            if value:
                self.initial[field_name] = timezone.localtime(value).strftime('%Y-%m-%dT%H:%M')

    class Meta:
        model = Quiz
        fields = [
            'title',
            'description',
            'category',
            'quiz_type',
            'difficulty',
            'time_limit',
            'max_attempts',
            'passing_score',
            'points_per_question',
            'bonus_points',
            'is_published',
            'is_featured',
            'is_scheduled',
            'scheduled_start_datetime',
            'scheduled_end_datetime',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'quiz_type': forms.Select(),
            'category': forms.Select(),
            'difficulty': forms.Select(),
            'scheduled_start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'scheduled_end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        is_scheduled = cleaned_data.get('is_scheduled')
        start_time = cleaned_data.get('scheduled_start_datetime')
        end_time = cleaned_data.get('scheduled_end_datetime')

        if is_scheduled and not start_time:
            self.add_error('scheduled_start_datetime', 'Start date/time is required for scheduled quizzes.')

        if start_time and end_time and end_time <= start_time:
            self.add_error('scheduled_end_datetime', 'End date/time must be later than start date/time.')

        if not is_scheduled:
            cleaned_data['scheduled_start_datetime'] = None
            cleaned_data['scheduled_end_datetime'] = None

        return cleaned_data


class QuestionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

    class Meta:
        model = Question
        fields = [
            'question_text',
            'option_a',
            'option_b',
            'option_c',
            'option_d',
            'correct_answer',
            'points',
            'explanation',
        ]
        widgets = {
            'question_text': forms.Textarea(attrs={'rows': 3}),
            'explanation': forms.Textarea(attrs={'rows': 2}),
        }
