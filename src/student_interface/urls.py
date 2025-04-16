# student_interface/urls.py
from django.urls import path
from . import views

app_name = 'student_interface' # Define namespace

urlpatterns = [
    # URL for the student landing/entry page
    path('quiz/start/', views.student_landing_view, name='student_landing'),
    # Add URL for quiz taking page (STU-2) later
    # e.g., path('quiz/take/<uuid:quiz_id>/', views.quiz_taking_view, name='quiz_taking'),

    # --- URL for Quiz Taking Page ---
    path('quiz/take/<uuid:quiz_id>/', views.quiz_taking_view, name='quiz_taking'),
    # --- End Add ---
    # Add URL for feedback page (STU-3) later
    # e.g., path('quiz/results/<uuid:attempt_id>/', views.quiz_results_view, name='quiz_results'),
]