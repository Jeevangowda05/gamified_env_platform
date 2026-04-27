from django import forms

from .models import CourseResource, Project, ProjectFile


class CourseResourceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

    class Meta:
        model = CourseResource
        fields = ['title', 'description', 'file']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class ProjectForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

    class Meta:
        model = Project
        fields = ['project_type', 'course', 'title', 'description', 'github_url']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        project_type = cleaned_data.get('project_type')
        course = cleaned_data.get('course')
        if project_type == 'SUBJECT' and not course:
            self.add_error('course', 'A course is required for subject-wise projects.')
        if project_type == 'OVERALL' and course:
            cleaned_data['course'] = None
        return cleaned_data


class ProjectFileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

    class Meta:
        model = ProjectFile
        fields = ['file_type', 'file']
