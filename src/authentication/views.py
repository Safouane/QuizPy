from django.shortcuts import render

# Create your views here.
import json
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt # For basic API usage without frontend form CSRF token initially
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@csrf_exempt # Use CSRF protection properly with frontend forms later
@require_POST
def login_view(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return JsonResponse({'error': 'Username and password required'}, status=400)

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Check if the user is a staff member (or superuser) for teacher access
            if user.is_staff:
                login(request, user)
                # Session cookie is automatically set by Django's login function
                return JsonResponse({'message': 'Login successful', 'username': user.username})
            else:
                # If regular users existed, this would deny them teacher access
                return JsonResponse({'error': 'Access denied. Not a teacher account.'}, status=403)
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    except Exception as e:
        # Log the exception e
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

@csrf_exempt # Or require POST and use proper CSRF later
def logout_view(request):
     # Check if user is authenticated before logging out
    if not request.user.is_authenticated:
         return JsonResponse({'error': 'Not logged in'}, status=400)

    user_display = request.user.username # Get username before logout
    logout(request)
     # Session cookie is cleared by Django's logout function
    return JsonResponse({'message': f'User {user_display} logged out successfully'})

# Optional: View to check current authentication status
def check_auth_status(request):
    if request.user.is_authenticated and request.user.is_staff:
         return JsonResponse({'isAuthenticated': True, 'username': request.user.username})
    else:
         return JsonResponse({'isAuthenticated': False})

def login_page_view(request):
    """Renders the teacher login page."""
    # If user is already logged in and is staff, redirect them away from login page
    if request.user.is_authenticated and request.user.is_staff:
        # --- MAKE SURE THIS LINE USES A VALID REDIRECT ---
        # --- IT SHOULD BE redirect('core:index') or redirect('/') ---
        # --- NOT redirect('teacher:dashboard') ---
        return redirect('/') # Example using home page URL name
    return render(request, 'authentication/login.html')