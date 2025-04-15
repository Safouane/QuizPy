from django.shortcuts import render
from django.contrib.auth.decorators import login_required # Standard Django login required
from authentication.decorators import teacher_required # Our custom decorator checking is_staff

# Import functions to potentially fetch summary data later (from quiz app)
# from quiz.views import ... (or better, utility functions later)
# from core.json_storage import load_data # Example: Load data to count quizzes

@teacher_required # Use the decorator that checks login AND is_staff, redirects to login if fails
def dashboard_view(request):
    """
    Renders the main dashboard page for logged-in teachers.
    Placeholder for summary data.
    """
    # --- Placeholder for fetching summary data ---
    # Example: Count active quizzes (implement properly later)
    # try:
    #     data = load_data()
    #     active_quizzes_count = sum(1 for quiz in data.get('quizzes', []) if not quiz.get('archived', False))
    #     total_questions_count = len(data.get('questions', []))
    # except Exception as e:
    #     print(f"Error loading data for dashboard summary: {e}")
    #     active_quizzes_count = 'N/A'
    #     total_questions_count = 'N/A'
    active_quizzes_count = 'N/A' # Placeholder
    total_questions_count = 'N/A' # Placeholder


    context = {
        'username': request.user.username,
        'active_quizzes_count': active_quizzes_count,
        'total_questions_count': total_questions_count,
        # Add more summary data later (e.g., recent results count)
    }
    return render(request, 'teacher_interface/dashboard.html', context)

@teacher_required
def quiz_list_view(request):
    """
    Renders the page that will display the list of quizzes.
    The actual data fetching happens via JavaScript calling API-1.
    """
    # We don't need to pass quiz data in the context here,
    # as the frontend JS will fetch it asynchronously.
    context = {
        'username': request.user.username # Pass username for context if needed
    }
    return render(request, 'teacher_interface/quiz_list.html', context)