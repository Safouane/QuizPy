from django.shortcuts import render

# Create your views here.
import json
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt # For basic API usage without frontend form CSRF token initially
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required # Standard Django login required


# Import the decorator we created in AUTH-3
from authentication.decorators import api_teacher_required # Our custom decorator checking is_staff

@csrf_exempt
@require_POST
def login_view(request):
    print("--- LOGIN VIEW START ---") # ADD LOGGING
    try:
        print("Request body:", request.body) # ADD LOGGING
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        print(f"Attempting login for username: {username}") # ADD LOGGING

        if not username or not password:
            print("!!! Missing username or password") # ADD LOGGING
            return JsonResponse({'error': 'Username and password required'}, status=400)

        user = authenticate(request, username=username, password=password)

        if user is not None:
            print(f"User '{username}' authenticated successfully. Is staff? {user.is_staff}") # ADD LOGGING
            if user.is_staff:
                login(request, user)
                print(f"Django login successful for {username}. Session key: {request.session.session_key}") # ADD LOGGING
                return JsonResponse({'message': 'Login successful', 'username': user.username})
            else:
                print(f"!!! User '{username}' is not staff. Denying access.") # ADD LOGGING
                return JsonResponse({'error': 'Access denied. Not a teacher account.'}, status=403)
        else:
            print(f"!!! Invalid credentials for username: {username}") # ADD LOGGING
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
    except json.JSONDecodeError:
        print("!!! Invalid JSON received") # ADD LOGGING
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    except Exception as e:
        print(f"!!! Unexpected error: {e}") # ADD LOGGING
        # Log the exception e properly here in real code
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)
    finally:
         print("--- LOGIN VIEW END ---") # ADD LOGGING

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
        return redirect('teacher_interface:dashboard') # Redirect to teacher dashboard
    return render(request, 'authentication/login.html')