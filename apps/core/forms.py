from django import forms

from .models import CourseResource


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
