from django.shortcuts import render, redirect, get_object_or_404 # Add redirect, get_object_or_404
from django.contrib.auth.decorators import login_required # Standard Django login required
from authentication.decorators import teacher_required # Our custom decorator checking is_staff
from django.urls import reverse

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

@teacher_required
def quiz_edit_view(request, quiz_id=None):
    """
    Renders the quiz creation/editing form.
    If quiz_id is provided, it's for editing (not implemented yet).
    If quiz_id is None, it's for creating a new quiz.
    """
    # For now, we only handle the 'Create' case (quiz_id is None)
    # Edit functionality (fetching quiz data via API-1 GET and passing to template)
    # will be added later.
    if quiz_id:
         # Placeholder for edit logic - maybe fetch data here or let JS fetch?
         # Let's assume JS will fetch for edit for now to keep view simple.
         context = {
             'quiz_id': quiz_id, # Pass ID so JS knows it's in edit mode
             'form_title': 'Edit Quiz' # Dynamic title
         }
    else:
        context = {
            'quiz_id': None,
            'form_title': 'Create New Quiz'
        }

    return render(request, 'teacher_interface/quiz_edit_form.html', context)

@teacher_required
def question_edit_view(request, question_id=None):
    """
    Renders the question creation/editing form.
    If question_id is provided, it's for editing.
    If question_id is None, it's for creating a new question.
    Actual data fetching/population for edit mode is handled by JavaScript.
    """
    context = {
        'question_id': question_id,
        'form_title': 'Edit Question' if question_id else 'Create New Question'
    }
    # Optionally pass categories fetched from existing questions for dropdown later
    # data = load_data()
    # categories = sorted(list(set(q.get('category', 'Uncategorized') for q in data.get('questions', []))))
    # context['existing_categories'] = categories
    return render(request, 'teacher_interface/question_edit_form.html', context)

@teacher_required
def question_bank_view(request):
    """
    Renders the Question Bank page.
    Questions are loaded asynchronously via JavaScript calling API-2.
    """
    context = {
        'username': request.user.username
    }
    # Potentially pass filter options like categories here later
    return render(request, 'teacher_interface/question_bank.html', context)