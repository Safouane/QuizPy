from django.urls import path
from . import views

app_name = 'teacher_interface' # Define namespace

urlpatterns = [
    path('teacher/dashboard/', views.dashboard_view, name='dashboard'),
    # Add other teacher UI URLs here later
    # e.g., path('teacher/quizzes/', views.quiz_list_view, name='quiz_list'),
]