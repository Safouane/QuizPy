from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt # Keep using exempt for now, manage CSRF properly with frontend later

# Import the decorator we created in AUTH-3
from authentication.decorators import api_teacher_required

# We will use these functions later to interact with CORE-3 JSON storage
# from core.json_storage import load_quiz_data, save_quiz_data
@csrf_exempt # Apply csrf_exempt if needed for POST/PUT/DELETE without frontend CSRF token yet
@api_teacher_required # Apply our custom decorator FIRST
@require_http_methods(["GET", "POST"]) # Specify allowed methods
def quiz_list_create_api(request):
    """
    API endpoint for listing all quizzes (GET) or creating a new quiz (POST).
    Requires teacher authentication.
    Placeholder implementation.
    """
    if request.method == 'GET':
        # TODO: Implement logic to load and return quiz list from JSON/DB (API-1)
        return JsonResponse({'message': 'Accessed protected quiz list (GET).', 'quizzes': []}) # Placeholder data
    
    elif request.method == 'POST':
        # TODO: Implement logic to create a new quiz from request.body and save (API-1)
        try:
             # import json # Import json if you use it here
             # data = json.loads(request.body)
             # quiz_title = data.get('title', 'Untitled Quiz')
             # Create and save quiz...
            return JsonResponse({'message': f'Protected quiz creation (POST) successful.'}, status=201)
        except Exception as e:
            return JsonResponse({'error': f'Failed to process request: {str(e)}'}, status=400)

@csrf_exempt # Apply csrf_exempt if needed for PUT/DELETE without frontend CSRF token yet
@api_teacher_required # Apply our custom decorator FIRST
@require_http_methods(["GET", "PUT", "DELETE"]) # Specify allowed methods
def quiz_detail_api(request, quiz_id):
    """
    API endpoint for retrieving (GET), updating (PUT), or deleting (DELETE)
    a specific quiz by its ID. Requires teacher authentication.
    Placeholder implementation.
    """
    # TODO: Implement logic to load/find the specific quiz by quiz_id (API-1)
    
    if request.method == 'GET':
        return JsonResponse({'message': f'Accessed protected quiz detail for ID {quiz_id} (GET).'})
    
    elif request.method == 'PUT':
        # TODO: Implement logic to update quiz_id from request.body (API-1)
         try:
             # import json # Import json if you use it here
             # data = json.loads(request.body)
             # Update quiz...
            return JsonResponse({'message': f'Protected quiz update for ID {quiz_id} (PUT) successful.'})
         except Exception as e:
             return JsonResponse({'error': f'Failed to process request: {str(e)}'}, status=400)

    elif request.method == 'DELETE':
        # TODO: Implement logic to delete quiz_id (API-1)
        return JsonResponse({'message': f'Protected quiz deletion for ID {quiz_id} (DELETE) successful.'})