# student_interface/views.py
from django.shortcuts import render
from django.http import Http404 # To handle cases where data isn't found


def quiz_results_view(request, attempt_id):
    """
    Renders the immediate feedback page for a specific quiz attempt.
    The actual result data is expected to be loaded via JavaScript
    from sessionStorage (populated by STU-2 after API-4 call).
    """
    # We pass attempt_id so JS knows which attempt's data to look for,
    # although ideally it might just use the 'lastAttemptId' from storage.
    # Passing it makes the URL meaningful.
    print(f"DEBUG: Rendering results page for attempt_id: {attempt_id}") # Log
    context = {
        'attempt_id': attempt_id,
    }
    # Add checks later: Ensure this attempt_id actually belongs to the current session/user?
    # For now, rely on sessionStorage data being present.
    return render(request, 'student_interface/quiz_results.html', context)

def student_landing_view(request):
    """
    Renders the initial landing page for students to enter details and quiz key.
    """
    # No specific context needed from backend initially
    context = {}
    return render(request, 'student_interface/landing.html', context)

def quiz_taking_view(request, quiz_id):
    """
    Renders the main quiz taking interface for the student.
    The actual quiz data is expected to be loaded via JavaScript
    from sessionStorage (populated by STU-1/API-3).
    """
    # We pass the quiz_id to the template so JS knows which quiz data to load
    # Basic validation could happen here later if needed (e.g., check UUID format)
    print(f"DEBUG: Rendering quiz taking page for quiz_id: {quiz_id}") # Log
    context = {
        'quiz_id': quiz_id,
        # Student info could also be passed from session if using Django sessions,
        # but we'll rely on JS sessionStorage for now.
    }
    # Consider adding a check here to see if the corresponding session data exists,
    # returning a different template or error if accessed directly without going through STU-1.
    # For now, assume JS will handle missing data.
    return render(request, 'student_interface/quiz_taking.html', context)