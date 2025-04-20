from django.urls import path
from . import views

app_name = "teacher_interface"  # Define namespace

urlpatterns = [
    path("dashboard/", views.dashboard_view, name="dashboard"),
    # Add other teacher UI URLs here later
    # e.g., path('teacher/quizzes/', views.quiz_list_view, name='quiz_list'),
    path("quizzes/", views.quiz_list_view, name="quiz_list"),
    # URL for creating a new quiz
    path("quizzes/new/", views.quiz_edit_view, name="quiz_create"),
    # URL for editing an existing quiz (passes quiz_id to the view)
    path("quizzes/<uuid:quiz_id>/edit/", views.quiz_edit_view, name="quiz_edit"),
    path("questions/new/", views.question_edit_view, name="question_create"),
    path(
        "questions/<uuid:question_id>/edit/",
        views.question_edit_view,
        name="question_edit",
    ),
    path("questions/", views.question_bank_view, name="question_bank"),
    # --- Results List URL ---
    path("results/", views.results_list_view, name="results_list"),
]
