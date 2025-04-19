# quiz/urls.py
from django.urls import path
from . import views

app_name = 'quiz'

urlpatterns = [
    # --- Quiz URLs ---
    path('api/quizzes/', views.quiz_list_create_api, name='quiz_list_create'),
    path('api/quizzes/<uuid:quiz_id>/', views.quiz_detail_api, name='quiz_detail'),

    # --- Question URLs ---
    path('api/questions/', views.question_list_create_api, name='question_list_create'),
    path('api/questions/<uuid:question_id>/', views.question_detail_api, name='question_detail'),

    # --- Export URL ---
    path('api/quizzes/<uuid:quiz_id>/export/', views.quiz_export_api, name='quiz_export'),
    # --- Import URL ---
    path('api/quizzes/import/', views.quiz_import_api, name='quiz_import'),
    
    # --- Quiz Access API URL ---
    path('api/quiz/access/', views.quiz_access_api, name='quiz_access'),

    # --- Submission URL ---
    # POST /api/quizzes/{quiz_id}/submit/
    path('api/quizzes/<uuid:quiz_id>/submit/', views.quiz_submit_api, name='quiz_submit'),
    # --- Regenerate Key URL ---
    path('api/quizzes/<uuid:quiz_id>/regenerate_key/', views.quiz_regenerate_key_api, name='quiz_regenerate_key'),

    # --- Attempt List & Export URLs ---
    path('api/quizzes/<uuid:quiz_id>/attempts/', views.get_quiz_attempts_api, name='quiz_attempts_list'),
    path('api/quizzes/<uuid:quiz_id>/attempts/export/json/', views.export_quiz_attempts_json_api, name='quiz_attempts_export_json'),
    path('api/quizzes/<uuid:quiz_id>/attempts/export/excel/', views.export_quiz_attempts_excel_api, name='quiz_attempts_export_excel'),
    
]