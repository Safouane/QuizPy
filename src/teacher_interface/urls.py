from django.urls import path
from . import views

app_name = 'teacher_interface' # Define namespace

urlpatterns = [
    path('teacher/dashboard/', views.dashboard_view, name='dashboard'),
    # Add other teacher UI URLs here later
    # e.g., path('teacher/quizzes/', views.quiz_list_view, name='quiz_list'),
    path('teacher/quizzes/', views.quiz_list_view, name='quiz_list'),
    # URL for creating a new quiz
    path('teacher/quizzes/new/', views.quiz_edit_view, name='quiz_create'),
    # URL for editing an existing quiz (passes quiz_id to the view)
    path('teacher/quizzes/<uuid:quiz_id>/edit/', views.quiz_edit_view, name='quiz_edit'),

    path('teacher/questions/new/', views.question_edit_view, name='question_create'),
    path('teacher/questions/<uuid:question_id>/edit/', views.question_edit_view, name='question_edit'),

    path('teacher/questions/', views.question_bank_view, name='question_bank'),

    # --- Results List URL ---
    path('teacher/results/', views.results_list_view, name='results_list'),

]