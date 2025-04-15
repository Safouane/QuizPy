from django.urls import path
from . import views # Import views from the quiz app

app_name = 'quiz' # Define the namespace for this app

urlpatterns = [
    # Matches POST /api/quizzes/ and GET /api/quizzes/
    path('api/quizzes/', views.quiz_list_create_api, name='quiz_list_create'),

    # Matches GET /api/quizzes/{quiz_id}/, PUT /api/quizzes/{quiz_id}/, DELETE /api/quizzes/{quiz_id}/
    # Assuming quiz_id can be integer or maybe UUID later. Using int for now.
    path('api/quizzes/<uuid:quiz_id>/', views.quiz_detail_api, name='quiz_detail'),

    # Add other quiz/question related API URLs here later (e.g., for API-2)
    # path('api/questions/', views.question_list_create_api, name='question_list_create'),
    # path('api/questions/<int:question_id>/', views.question_detail_api, name='question_detail'),
]