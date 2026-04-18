"""
Forms for accounts app
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Div, Field
from crispy_forms.bootstrap import FormActions
from .models import User, UserProfile


class CustomUserCreationForm(UserCreationForm):
    """Custom user registration form"""

    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    user_type = forms.ChoiceField(choices=User.USER_TYPES, required=True)
    institution = forms.CharField(max_length=100, required=False)
    grade_level = forms.CharField(max_length=20, required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'user_type', 'institution', 'grade_level', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div('first_name', css_class='col-md-6'),
                Div('last_name', css_class='col-md-6'),
                css_class='row'
            ),
            'username',
            'email',
            Div(
                Div('user_type', css_class='col-md-6'),
                Div('grade_level', css_class='col-md-6'),
                css_class='row'
            ),
            'institution',
            Div(
                Div('password1', css_class='col-md-6'),
                Div('password2', css_class='col-md-6'),
                css_class='row'
            ),
            FormActions(
                Submit('register', 'Create Account', css_class='btn btn-primary btn-lg w-100')
            )
        )

        # Add Bootstrap classes to form fields
        for field_name in self.fields:
            self.fields[field_name].widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.user_type = self.cleaned_data['user_type']
        user.institution = self.cleaned_data['institution']
        user.grade_level = self.cleaned_data['grade_level']
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    """User profile update form"""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'avatar', 'bio', 'date_of_birth', 
                 'institution', 'grade_level', 'preferred_language', 'notifications_enabled']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

    learning_style = forms.ChoiceField(
        choices=[('', 'Select Learning Style')] + UserProfile._meta.get_field('learning_style').choices,
        required=False
    )
    sustainability_goals = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    )
    is_public_profile = forms.BooleanField(required=False)
    allow_friend_requests = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div('first_name', css_class='col-md-6'),
                Div('last_name', css_class='col-md-6'),
                css_class='row'
            ),
            'avatar',
            'bio',
            Div(
                Div('date_of_birth', css_class='col-md-6'),
                Div('preferred_language', css_class='col-md-6'),
                css_class='row'
            ),
            Div(
                Div('institution', css_class='col-md-6'),
                Div('grade_level', css_class='col-md-6'),
                css_class='row'
            ),
            'learning_style',
            'sustainability_goals',
            Div(
                Field('notifications_enabled', css_class='form-check-input'),
                Field('is_public_profile', css_class='form-check-input'),
                Field('allow_friend_requests', css_class='form-check-input'),
                css_class='row'
            ),
            FormActions(
                Submit('save', 'Update Profile', css_class='btn btn-primary')
            )
        )

        # Load profile data
        if hasattr(self.instance, 'profile'):
            profile = self.instance.profile
            self.fields['learning_style'].initial = profile.learning_style
            self.fields['sustainability_goals'].initial = profile.sustainability_goals
            self.fields['is_public_profile'].initial = profile.is_public_profile
            self.fields['allow_friend_requests'].initial = profile.allow_friend_requests

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit and hasattr(user, 'profile'):
            profile = user.profile
            profile.learning_style = self.cleaned_data.get('learning_style', '')
            profile.sustainability_goals = self.cleaned_data.get('sustainability_goals', '')
            profile.is_public_profile = self.cleaned_data.get('is_public_profile', True)
            profile.allow_friend_requests = self.cleaned_data.get('allow_friend_requests', True)
            profile.save()
        return user
