from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def teacher_required(view_func):
    @login_required
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.user_type != 'teacher' and not request.user.is_superuser:
            messages.error(request, 'You need a teacher account to access this page.')
            return redirect('core:dashboard')
        return view_func(request, *args, **kwargs)

    return _wrapped_view
