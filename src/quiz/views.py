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
        
@csrf_exempt
@api_teacher_required
@require_http_methods(["GET", "POST"])
def question_list_create_api(request):
    """
    API endpoint for listing all questions (GET) or creating a new question (POST).
    Supports filtering by quiz_id or category via query parameters.
    Requires teacher authentication. Uses JSON storage.
    """
    data = load_data()
    all_questions = data.get('questions', [])

    if request.method == 'GET':
        # --- Filtering Logic ---
        query_params = request.GET
        quiz_id_filter = query_params.get('quiz_id')
        category_filter = query_params.get('category')
        # Add more filters like difficulty, type if needed

        filtered_questions = all_questions
        if quiz_id_filter:
            # Filter questions linked to the specific quiz_id
            filtered_questions = [q for q in filtered_questions if quiz_id_filter in q.get('quiz_ids', [])]
        if category_filter:
             # Case-insensitive category filter
            filtered_questions = [q for q in filtered_questions if category_filter.lower() == q.get('category', '').lower()]

        # If no filters, returns all questions (acting as question bank)
        return JsonResponse({'questions': filtered_questions})

    elif request.method == 'POST':
        try:
            request_data = json.loads(request.body)

            # --- Validate Required Fields ---
            text = request_data.get('text')
            q_type = request_data.get('type')
            if not text or not q_type:
                return JsonResponse({'error': 'Question text and type are required.'}, status=400)

            # Generate unique ID
            new_question_id = str(uuid.uuid4())
            
            # Prepare basic question structure
            new_question = {
                'id': new_question_id,
                'quiz_ids': request_data.get('quiz_ids', []),
                'text': text,
                'type': q_type,
                'options': [],
                'correct_answer': [],
                'score': request_data.get('score', 1),
                'difficulty': request_data.get('difficulty', 'Medium'),
                'category': request_data.get('category', 'Uncategorized'),
                'media_url': request_data.get('media_url'),
                # --- ADDED FOR SHORT TEXT ---
                'short_answer_review_mode': 'manual', # Default mode
                'short_answer_correct_text': None
                # --- END ADD ---
            }

            # --- Handle MCQ Specific Fields ---
            if q_type == 'MCQ':
                options_data = request_data.get('options', [])
                correct_answer_texts = request_data.get('correct_answer_texts', []) # Expect list of correct option TEXTS from frontend for simplicity

                if not options_data or not correct_answer_texts:
                     return JsonResponse({'error': 'MCQ questions require options and correct_answer_texts.'}, status=400)
                
                generated_options = []
                correct_option_ids = []
                for opt_text in options_data:
                     option_id = str(uuid.uuid4())
                     generated_options.append({"id": option_id, "text": opt_text})
                     if opt_text in correct_answer_texts:
                          correct_option_ids.append(option_id)
                
                if not correct_option_ids:
                     return JsonResponse({'error': 'Correct answer text(s) did not match any provided options.'}, status=400)

                new_question['options'] = generated_options
                new_question['correct_answer'] = correct_option_ids

            # --- Handle other types (e.g., SHORT_TEXT) - add validation/fields as needed ---
            elif q_type == 'SHORT_TEXT':
                review_mode = request_data.get('short_answer_review_mode', 'manual')
                correct_text = request_data.get('short_answer_correct_text', None)

                if review_mode not in ['manual', 'auto']:
                    return JsonResponse({'error': 'Invalid short answer review mode.'}, status=400)
                if review_mode == 'auto' and not correct_text:
                    return JsonResponse({'error': 'Correct answer text is required for automatic review mode.'}, status=400)

                new_question['short_answer_review_mode'] = review_mode
                new_question['short_answer_correct_text'] = correct_text if review_mode == 'auto' else None


            # Add to list and save
            all_questions.append(new_question)
            data['questions'] = all_questions
            save_data(data)

            # Optional: If quiz_ids were provided, update those quizzes too
            if new_question['quiz_ids']:
                all_quizzes = data.get('quizzes', [])
                updated = False
                for quiz in all_quizzes:
                    if quiz.get('id') in new_question['quiz_ids']:
                        if new_question_id not in quiz.get('questions', []):
                            quiz.setdefault('questions', []).append(new_question_id)
                            updated = True
                if updated:
                     data['quizzes'] = all_quizzes
                     save_data(data) # Save again if quizzes were updated


            return JsonResponse({'message': 'Question created successfully.', 'question': new_question}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format in request body.'}, status=400)
        except Exception as e:
            print(f"Error creating question: {e}")
            import traceback
            traceback.print_exc() # Print full traceback for debugging
            return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)
        

@csrf_exempt
@api_teacher_required
@require_http_methods(["GET", "PUT", "DELETE"])
def question_detail_api(request, question_id):
    """
    API endpoint for retrieving (GET), updating (PUT), or deleting (DELETE)
    a specific question by its ID. Requires teacher authentication. Uses JSON storage.
    """
    data = load_data()
    questions = data.get('questions', [])
    question = None
    question_index = -1

    # Find the question by ID
    for index, q in enumerate(questions):
        if q.get('id') == str(question_id): # Compare as strings
            question = q
            question_index = index
            break

    if question is None:
        return JsonResponse({'error': f'Question with ID {question_id} not found.'}, status=404)

    # --- GET Request ---
    if request.method == 'GET':
        return JsonResponse({'question': question})

    # --- PUT Request (Update) ---
    elif request.method == 'PUT':
        try:
            request_data = json.loads(request.body)
            original_quiz_ids = set(question.get('quiz_ids', []))

            # Update fields (only update fields present in request_data)
            # Use .get() for safety if a field might be missing from the original JSON
            if 'text' in request_data: question['text'] = request_data['text']
            if 'type' in request_data: question['type'] = request_data['type'] # Note: Changing type might invalidate options/answers
            if 'score' in request_data: question['score'] = request_data['score']
            if 'difficulty' in request_data: question['difficulty'] = request_data['difficulty']
            if 'category' in request_data: question['category'] = request_data['category']
            if 'media_url' in request_data: question['media_url'] = request_data.get('media_url') # Allow setting to null
            if 'quiz_ids' in request_data: question['quiz_ids'] = request_data['quiz_ids'] # Overwrite associated quizzes

            # --- Update Short Text Specific Fields ---
            if question.get('type') == 'SHORT_TEXT':
                if 'short_answer_review_mode' in request_data:
                    review_mode = request_data['short_answer_review_mode']
                    if review_mode not in ['manual', 'auto']:
                        return JsonResponse({'error': 'Invalid short answer review mode.'}, status=400)
                    question['short_answer_review_mode'] = review_mode
                    # Reset correct text if switching to manual
                    if review_mode == 'manual':
                        question['short_answer_correct_text'] = None

                if 'short_answer_correct_text' in request_data:
                    # Only allow setting correct text if mode is auto
                    if question.get('short_answer_review_mode') == 'auto':
                        correct_text = request_data['short_answer_correct_text']
                        if not correct_text:
                            return JsonResponse({'error': 'Correct answer text cannot be empty for automatic review mode.'}, status=400)
                        question['short_answer_correct_text'] = correct_text
                    # else: ignore correct_text if mode is manual

            # Update MCQ specific fields carefully
            elif question['type'] == 'MCQ':
                if 'options' in request_data: # Expect list of texts
                     options_data = request_data.get('options', [])
                     correct_answer_texts = request_data.get('correct_answer_texts', []) # Expect correct texts again
                     if not options_data or not correct_answer_texts:
                          return JsonResponse({'error': 'Updating MCQ requires options and correct_answer_texts.'}, status=400)

                     generated_options = []
                     correct_option_ids = []
                     for opt_text in options_data:
                          option_id = str(uuid.uuid4()) # Generate new IDs on update for simplicity
                          generated_options.append({"id": option_id, "text": opt_text})
                          if opt_text in correct_answer_texts:
                               correct_option_ids.append(option_id)

                     if not correct_option_ids:
                          return JsonResponse({'error': 'Correct answer text(s) did not match any provided options during update.'}, status=400)
                     question['options'] = generated_options
                     question['correct_answer'] = correct_option_ids
                # Allow updating only correct answers if options are not provided? Maybe too complex for now.

            # Replace the old question dict with the updated one
            questions[question_index] = question
            data['questions'] = questions
            save_data(data)

            # --- Update Quiz Associations ---
            # Find quizzes removed and quizzes added
            new_quiz_ids = set(question.get('quiz_ids', []))
            removed_quiz_ids = original_quiz_ids - new_quiz_ids
            added_quiz_ids = new_quiz_ids - original_quiz_ids
            quizzes_updated = False
            all_quizzes = data.get('quizzes', [])

            for quiz in all_quizzes:
                quiz_questions = quiz.setdefault('questions', [])
                q_id_str = str(question_id) # Ensure comparison is consistent
                # Remove question from quizzes it's no longer linked to
                if quiz.get('id') in removed_quiz_ids:
                     if q_id_str in quiz_questions:
                          quiz_questions.remove(q_id_str)
                          quizzes_updated = True
                # Add question to quizzes it's newly linked to
                if quiz.get('id') in added_quiz_ids:
                     if q_id_str not in quiz_questions:
                          quiz_questions.append(q_id_str)
                          quizzes_updated = True

            if quizzes_updated:
                data['quizzes'] = all_quizzes
                save_data(data) # Save again with updated quiz links

            return JsonResponse({'message': 'Question updated successfully.', 'question': question})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format in request body.'}, status=400)
        except Exception as e:
            print(f"Error updating question {question_id}: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)

    # --- DELETE Request ---
    elif request.method == 'DELETE':
        try:
            # Remove the question from the main list
            deleted_question = questions.pop(question_index)
            data['questions'] = questions
            save_data(data) # Save questions list

            # Remove the question ID from any quizzes it was associated with
            deleted_q_id = str(question_id)
            quizzes_updated = False
            all_quizzes = data.get('quizzes', [])
            for quiz in all_quizzes:
                 quiz_questions = quiz.get('questions', [])
                 if deleted_q_id in quiz_questions:
                      quiz_questions.remove(deleted_q_id)
                      quizzes_updated = True

            if quizzes_updated:
                data['quizzes'] = all_quizzes
                save_data(data) # Save updated quizzes list

            return JsonResponse({'message': f'Question (ID: {question_id}) deleted successfully.'})
        except Exception as e:
            print(f"Error deleting question {question_id}: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)
        
