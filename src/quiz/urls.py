# quiz/urls.py
from django.urls import path
from . import views

app_name = 'quiz'

urlpatterns = [
    # Quiz URLs
    path('api/quizzes/', views.quiz_list_create_api, name='quiz_list_create'),
    path('api/quizzes/<uuid:quiz_id>/', views.quiz_detail_api, name='quiz_detail'),

    # --- Add Question URLs ---
    path('api/questions/', views.question_list_create_api, name='question_list_create'),
    path('api/questions/<uuid:question_id>/', views.question_detail_api, name='question_detail'),
    # --- End Add ---
]