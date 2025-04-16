# student_interface/views.py
from django.shortcuts import render

def student_landing_view(request):
    """
    Renders the initial landing page for students to enter details and quiz key.
    """
    # No specific context needed from backend initially
    context = {}
    return render(request, 'student_interface/landing.html', context)