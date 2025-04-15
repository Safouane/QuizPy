from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt # Keep using exempt for now, manage CSRF properly with frontend later

import json
import uuid
from core.json_storage import load_data, save_data

# Import the decorator we created in AUTH-3
from authentication.decorators import api_teacher_required

# We will use these functions later to interact with CORE-3 JSON storage
# from core.json_storage import load_quiz_data, save_quiz_data
@csrf_exempt
@api_teacher_required
@require_http_methods(["GET", "POST"])
def quiz_list_create_api(request):
    """
    API endpoint for listing all quizzes (GET) or creating a new quiz (POST).
    Requires teacher authentication. Uses JSON storage.
    """
    data = load_data() # Load current data from JSON
    quizzes = data.get('quizzes', [])

    if request.method == 'GET':
        # Return the list of all quizzes
        # Optionally filter out sensitive info if needed in the future
        return JsonResponse({'quizzes': quizzes})

    elif request.method == 'POST':
        try:
            # Get data from request body
            request_data = json.loads(request.body)
            title = request_data.get('title')
            description = request_data.get('description', '') # Optional field

            if not title:
                return JsonResponse({'error': 'Quiz title is required.'}, status=400)

            # Create new quiz object
            new_quiz_id = str(uuid.uuid4()) # Generate a unique ID
            new_quiz = {
                'id': new_quiz_id,
                'title': title,
                'description': description,
                'questions': [], # List of question IDs belonging to this quiz
                'config': { # Default config, can be updated later via PUT
                    'duration': None, # in minutes
                    'pass_score': 70, # percentage
                    'presentation_mode': 'all', # 'all' or 'one-by-one'
                    'allow_back': True,
                    'randomize_questions': False,
                    'shuffle_answers': False
                },
                'archived': False,
                'versions': [] # For TCHR-8 later
                # Add created_at, updated_at timestamps if desired
            }

            # Add to the list and save
            quizzes.append(new_quiz)
            data['quizzes'] = quizzes # Update the main data dict
            save_data(data) # Write back to JSON file

            return JsonResponse({'message': 'Quiz created successfully.', 'quiz': new_quiz}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format in request body.'}, status=400)
        except Exception as e:
            # Log the exception e
            print(f"Error creating quiz: {e}") # Basic logging
            return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)
        

@csrf_exempt
@api_teacher_required
@require_http_methods(["GET", "PUT", "DELETE"])
def quiz_detail_api(request, quiz_id):
    """
    API endpoint for retrieving (GET), updating (PUT), or deleting (DELETE)
    a specific quiz by its ID. Requires teacher authentication. Uses JSON storage.
    """
    data = load_data()
    quizzes = data.get('quizzes', [])
    quiz = None
    quiz_index = -1

    # Find the quiz by ID
    for index, q in enumerate(quizzes):
        if q.get('id') == str(quiz_id): # Compare as strings if quiz_id is int/uuid
            quiz = q
            quiz_index = index
            break

    if quiz is None:
        return JsonResponse({'error': f'Quiz with ID {quiz_id} not found.'}, status=404)

    # --- GET Request ---
    if request.method == 'GET':
        return JsonResponse({'quiz': quiz})

    # --- PUT Request (Update) ---
    elif request.method == 'PUT':
        try:
            request_data = json.loads(request.body)

            # Update allowed fields (add more fields as needed)
            if 'title' in request_data:
                quiz['title'] = request_data['title']
            if 'description' in request_data:
                quiz['description'] = request_data.get('description', quiz.get('description', '')) # Handle optional field
            if 'config' in request_data: # Allow updating config block
                # Simple merge - careful, might overwrite nested keys unintentionally
                # A more robust update would merge nested dicts carefully
                quiz['config'] = {**quiz.get('config', {}), **request_data['config']}
            if 'archived' in request_data:
                 quiz['archived'] = bool(request_data['archived'])

            # Replace the old quiz dict with the updated one in the list
            quizzes[quiz_index] = quiz
            data['quizzes'] = quizzes
            save_data(data) # Save changes back to JSON

            return JsonResponse({'message': 'Quiz updated successfully.', 'quiz': quiz})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format in request body.'}, status=400)
        except Exception as e:
             print(f"Error updating quiz {quiz_id}: {e}") # Basic logging
             return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)

    # --- DELETE Request ---
    elif request.method == 'DELETE':
        try:
            # Remove the quiz from the list
            deleted_quiz_title = quizzes.pop(quiz_index).get('title', 'N/A')
            data['quizzes'] = quizzes
            save_data(data) # Save changes

            # Note: Deleting a quiz might require deleting associated questions later,
            # or handling orphaned questions. For now, just remove the quiz entry.

            return JsonResponse({'message': f'Quiz "{deleted_quiz_title}" (ID: {quiz_id}) deleted successfully.'})
        except Exception as e:
             print(f"Error deleting quiz {quiz_id}: {e}") # Basic logging
             return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)