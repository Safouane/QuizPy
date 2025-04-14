from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.shortcuts import redirect
from django.urls import reverse_lazy

def teacher_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user is logged in and is a staff member.
    Redirects to the login page if necessary.
    """
    if login_url is None:
        login_url = reverse_lazy('authentication:login_page') # Use the name of your login page URL

    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_staff,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

# Optional: Decorator for API views that returns 403 instead of redirecting
def api_teacher_required(view_func):
    """
    Decorator for API views that checks if the user is authenticated and is staff.
    Returns 401/403 JSON response if not.
    """
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.http import JsonResponse
            return JsonResponse({'error': 'Authentication required.'}, status=401)
        if not request.user.is_staff:
            from django.http import JsonResponse
            return JsonResponse({'error': 'Permission denied. Teacher access required.'}, status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view