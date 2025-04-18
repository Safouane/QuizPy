from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt # Keep using exempt for now, manage CSRF properly with frontend later
import json
import uuid
from core.json_storage import load_data, save_data
from django.http import HttpResponse
import random
import datetime
from decimal import Decimal, ROUND_HALF_UP # For accurate score calculation
import openpyxl # Add import
from openpyxl.utils import get_column_letter # Optional: For setting column widths


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
            import random # Add import
            import string # Add import
            # Get data from request body
            request_data = json.loads(request.body)
            title = request_data.get('title')
            description = request_data.get('description', '') # Optional field

            if not title:
                return JsonResponse({'error': 'Quiz title is required.'}, status=400)

            def generate_quiz_key(length=6):
                # Simple key generator (letters and digits) - make more robust if needed
                characters = string.ascii_uppercase + string.digits
                return ''.join(random.choice(characters) for i in range(length))

            # Generate a unique key (add checks later if collision is a concern)
            new_quiz_key = generate_quiz_key()
            
            # Create new quiz object
            new_quiz_id = str(uuid.uuid4()) # Generate a unique ID
            new_quiz = {
                'id': new_quiz_id,
                'title': title,
                'description': description,
                # Accept questions list, default to empty if not provided
                'questions': request_data.get('questions', []),
                'config': { # Default config, can be updated later via PUT
                    'duration': None, # in minutes
                    'pass_score': 70, # percentage
                    'presentation_mode': 'all', # 'all' or 'one-by-one'
                    'allow_back': True,
                    'randomize_questions': False,
                    'shuffle_answers': False
                },
                'access_key': new_quiz_key,
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


            # Update allowed fields
            if 'title' in request_data: quiz['title'] = request_data['title']
            if 'description' in request_data: quiz['description'] = request_data.get('description', quiz.get('description', ''))
            if 'config' in request_data: quiz['config'] = {**quiz.get('config', {}), **request_data['config']}
            if 'archived' in request_data: quiz['archived'] = bool(request_data['archived'])
            
            # --- ADDED: Update questions list ---
            if 'questions' in request_data:
            # Basic validation: Ensure it's a list of strings (or can be converted)
                try:
                    quiz['questions'] = [str(q_id) for q_id in request_data['questions']]
                except (TypeError, ValueError):
                    return JsonResponse({'error': 'Invalid format for questions list.'}, status=400)
            # --- END ADD ---

            if 'config' in request_data:
                new_config = request_data['config']
                # Get existing config or default to empty dict
                current_config = quiz.get('config', {})

                # Validate and update specific config fields
                # Duration (Allow null or positive integer)
                duration = new_config.get('duration', current_config.get('duration')) # Keep old if not provided
                if duration is not None:
                    try:
                         duration = int(duration)
                         if duration < 0: duration = None # Allow only non-negative or null
                    except (ValueError, TypeError):
                         duration = None # Reset if invalid type/value
                current_config['duration'] = duration

                # Pass Score (Allow number between 0 and 100)
                pass_score = new_config.get('pass_score', current_config.get('pass_score', 70)) # Keep old or default
                try:
                    pass_score = float(pass_score)
                    if not (0 <= pass_score <= 100):
                         pass_score = 70 # Reset to default if out of range
                except (ValueError, TypeError):
                    pass_score = 70 # Reset if invalid
                current_config['pass_score'] = pass_score

                # Presentation Mode
                presentation_mode = new_config.get('presentation_mode', current_config.get('presentation_mode', 'all'))
                if presentation_mode not in ['all', 'one-by-one']:
                    presentation_mode = 'all' # Default if invalid
                current_config['presentation_mode'] = presentation_mode

                # Allow Back Navigation (Boolean)
                allow_back = new_config.get('allow_back', current_config.get('allow_back', True))
                current_config['allow_back'] = bool(allow_back) # Ensure boolean

                # Randomize Question Order (Boolean)
                randomize_questions = new_config.get('randomize_questions', current_config.get('randomize_questions', False)) # Default false
                current_config['randomize_questions'] = bool(randomize_questions) # Ensure boolean

                # Shuffle Answer Options (Boolean)
                shuffle_answers = new_config.get('shuffle_answers', current_config.get('shuffle_answers', False)) # Default false
                current_config['shuffle_answers'] = bool(shuffle_answers) # Ensure boolean
                
                # Assign the updated config back
                quiz['config'] = current_config

            if 'archived' in request_data: quiz['archived'] = bool(request_data['archived'])

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
        type_filter = query_params.get('type') # <<< Make sure you read this parameter
        # Add more filters like difficulty, type if needed

        filtered_questions = all_questions
        if quiz_id_filter:
            # Filter questions linked to the specific quiz_id
            filtered_questions = [q for q in filtered_questions if quiz_id_filter in q.get('quiz_ids', [])]
        if category_filter:
             # Case-insensitive category filter
            filtered_questions = [q for q in filtered_questions if category_filter.lower() == q.get('category', '').lower()]
        if type_filter:
            filtered_questions = [q for q in filtered_questions if type_filter.upper() == q.get('type', '').upper()] # Case-insensitive type check
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
        

@api_teacher_required
@require_http_methods(["GET"]) # Export is typically a GET request
def quiz_export_api(request, quiz_id):
    """
    API endpoint to export a single quiz and its associated questions as JSON.
    """
    try:
        data = load_data()
        quizzes = data.get('quizzes', [])
        all_questions = data.get('questions', [])
        quiz_to_export = None

        # Find the quiz
        for q in quizzes:
            if str(q.get('id')) == str(quiz_id): # Compare as strings
                quiz_to_export = q
                break

        if quiz_to_export is None:
            return JsonResponse({'error': f'Quiz with ID {quiz_id} not found.'}, status=404)

        # Find associated questions
        question_ids_in_quiz = set(quiz_to_export.get('questions', []))
        associated_questions = [
            q for q in all_questions if str(q.get('id')) in question_ids_in_quiz
        ]

        # Structure the export data
        export_data = {
            "quiz": quiz_to_export,
            "questions": associated_questions
        }

        # Prepare the file response
        json_data = json.dumps(export_data, indent=2) # Pretty print JSON
        # Create a safe filename (e.g., replace spaces)
        filename_title = quiz_to_export.get('title', 'quiz').replace(' ', '_')
        filename = f"quiz_{filename_title}_{quiz_id}.json"

        response = HttpResponse(json_data, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{filename}"' # Force download
        response['Access-Control-Expose-Headers'] = 'Content-Disposition' # Important for JS if needed later

        print(f"DEBUG: Exporting quiz ID {quiz_id} as {filename}") # Logging
        return response

    except Exception as e:
        print(f"Error exporting quiz {quiz_id}: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'An unexpected error occurred during export: {str(e)}'}, status=500)
    
@csrf_exempt # Use proper CSRF handling if form submitted directly later
@api_teacher_required
@require_http_methods(["POST"])
def quiz_import_api(request):
    """
    API endpoint to import a quiz and its questions from an uploaded JSON file.
    Generates new IDs for the imported items.
    """
    try:
        # Check if file is present
        if 'quizFile' not in request.FILES:
            return JsonResponse({'error': 'No quiz file provided.'}, status=400)

        uploaded_file = request.FILES['quizFile']

        # Basic validation: Check file extension (allow .json)
        if not uploaded_file.name.lower().endswith('.json'):
            return JsonResponse({'error': 'Invalid file type. Only .json files are accepted.'}, status=400)

        # Read and parse JSON content
        try:
            import_data = json.load(uploaded_file) # Reads directly from file stream
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format in the uploaded file.'}, status=400)
        except Exception as e:
             return JsonResponse({'error': f'Error reading file content: {str(e)}'}, status=400)


        # --- Validate and Process Import Data ---
        imported_quiz_data = import_data.get("quiz")
        imported_questions_data = import_data.get("questions", [])

        if not imported_quiz_data or not isinstance(imported_quiz_data, dict):
            return JsonResponse({'error': 'Invalid JSON structure: Missing or invalid "quiz" object.'}, status=400)
        if not isinstance(imported_questions_data, list):
             return JsonResponse({'error': 'Invalid JSON structure: "questions" must be a list.'}, status=400)

        # Load existing data
        data = load_data()
        all_quizzes = data.get('quizzes', [])
        all_questions = data.get('questions', [])

        # --- Process Questions First ---
        newly_created_question_ids = []
        old_to_new_question_id_map = {}
        for q_data in imported_questions_data:
            if not isinstance(q_data, dict) or not q_data.get('text') or not q_data.get('type'):
                 print(f"Skipping invalid question data: {q_data}") # Log skip
                 continue # Skip invalid question entries

            old_q_id = q_data.get('id') # Get original ID for mapping
            new_q = q_data.copy() # Create a copy to modify

            # Generate NEW IDs
            new_q_id = str(uuid.uuid4())
            new_q['id'] = new_q_id
            if old_q_id: # Store mapping if original ID existed
                old_to_new_question_id_map[old_q_id] = new_q_id

            # Generate NEW Option IDs if MCQ
            if new_q.get('type') == 'MCQ' and isinstance(new_q.get('options'), list):
                 new_options = []
                 old_to_new_option_id_map = {}
                 correct_answer_texts = [] # Need to rebuild correct answers based on new IDs

                 # Find correct texts first using old IDs
                 old_correct_option_ids = set(new_q.get('correct_answer', []))
                 original_options = new_q.get('options', [])
                 for opt in original_options:
                     if isinstance(opt, dict) and opt.get('id') in old_correct_option_ids:
                         correct_answer_texts.append(opt.get('text'))

                 # Generate new options and map correct answers
                 new_correct_answer_ids = []
                 for opt in original_options:
                      if not isinstance(opt, dict) or 'text' not in opt: continue # Skip invalid option
                      new_opt_id = str(uuid.uuid4())
                      new_options.append({'id': new_opt_id, 'text': opt['text']})
                      # If this option's text was marked correct, use the new ID
                      if opt.get('text') in correct_answer_texts:
                          new_correct_answer_ids.append(new_opt_id)

                 new_q['options'] = new_options
                 new_q['correct_answer'] = new_correct_answer_ids
            else:
                 # Clear options/answers if not MCQ
                 new_q['options'] = []
                 new_q['correct_answer'] = []


            # Add processed question to main list
            all_questions.append(new_q)
            newly_created_question_ids.append(new_q_id) # Keep track for the quiz

        # --- Process Quiz ---
        new_quiz = imported_quiz_data.copy()
        new_quiz_id = str(uuid.uuid4())
        new_quiz['id'] = new_quiz_id

        # Update quiz's question list with NEW question IDs
        # Map old IDs from imported quiz's 'questions' list to new IDs
        old_question_ids_in_quiz = imported_quiz_data.get('questions', [])
        new_question_ids_for_quiz = [
            old_to_new_question_id_map[old_id]
            for old_id in old_question_ids_in_quiz
            if old_id in old_to_new_question_id_map # Only include if the question was valid and processed
        ]
        # If no 'questions' key in import, use all newly created ones
        if not old_question_ids_in_quiz and newly_created_question_ids:
             new_question_ids_for_quiz = newly_created_question_ids

        new_quiz['questions'] = new_question_ids_for_quiz

        # Add basic validation for title
        if not new_quiz.get('title'):
            new_quiz['title'] = "Imported Quiz" # Default title

        # Reset potentially sensitive/runtime data? (e.g., versions)
        new_quiz['versions'] = []
        new_quiz['archived'] = False # Import as active

        # Add processed quiz to main list
        all_quizzes.append(new_quiz)

        # --- Save Updated Data ---
        data['quizzes'] = all_quizzes
        data['questions'] = all_questions
        save_data(data)

        print(f"DEBUG: Imported quiz '{new_quiz['title']}' (New ID: {new_quiz_id}) with {len(new_question_ids_for_quiz)} questions.") # Logging
        return JsonResponse({
            'message': 'Quiz imported successfully!',
            'new_quiz_id': new_quiz_id,
            'new_quiz_title': new_quiz['title'],
            'questions_imported_count': len(newly_created_question_ids)
             }, status=201)

    except Exception as e:
        print(f"Error importing quiz: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'An unexpected error occurred during import: {str(e)}'}, status=500)
    

@csrf_exempt # If called via JS POST potentially, otherwise maybe GET
@require_http_methods(["POST"]) # Let's use POST to receive the key potentially alongside student info later
def quiz_access_api(request):
    """
    API endpoint for students to access a quiz using a key.
    Validates the key, fetches quiz and question data, applies randomization,
    and returns the prepared quiz structure for the student to take.
    """
    try:
        request_data = json.loads(request.body)
        quiz_key = request_data.get('quiz_key')

        if not quiz_key:
            return JsonResponse({'error': 'Quiz key is required.'}, status=400)

        print(f"DEBUG: Quiz access requested with key: {quiz_key}") # Log

        data = load_data()
        all_quizzes = data.get('quizzes', [])
        all_questions = data.get('questions', [])
        target_quiz = None
        quiz_metadata = None

        # --- Find Quiz by Access Key ---
        for quiz in all_quizzes:
            # Case-insensitive key matching recommended
            if quiz.get('access_key') and quiz.get('access_key').upper() == quiz_key.upper():
                 # Found the quiz, check if it's active
                 if quiz.get('archived', False):
                      print(f"DEBUG: Quiz found for key {quiz_key} but is archived.")
                      return JsonResponse({'error': 'This quiz is currently inactive.'}, status=403) # Forbidden
                 target_quiz = quiz
                 break # Stop searching once found

        if target_quiz is None:
            print(f"DEBUG: Invalid quiz key provided: {quiz_key}")
            return JsonResponse({'error': 'Invalid quiz key.'}, status=404) # Not Found

        print(f"DEBUG: Found active quiz '{target_quiz.get('title')}' (ID: {target_quiz.get('id')}) for key {quiz_key}")

        # --- Fetch Associated Questions ---
        question_ids_in_quiz = set(target_quiz.get('questions', []))
        quiz_questions = [
            q for q in all_questions if str(q.get('id')) in question_ids_in_quiz
        ]

        if not quiz_questions:
             print(f"DEBUG: Quiz {target_quiz.get('id')} has no associated questions.")
             return JsonResponse({'error': 'This quiz contains no questions.'}, status=400) # Bad Request

        print(f"DEBUG: Found {len(quiz_questions)} questions for quiz {target_quiz.get('id')}")

        # --- Apply Randomization (Based on TCHR-6 config) ---
        quiz_config = target_quiz.get('config', {})

        # 1. Randomize Question Order
        if quiz_config.get('randomize_questions', False):
            print("DEBUG: Randomizing question order.")
            random.shuffle(quiz_questions)

        # 2. Shuffle Answer Options (for MCQs)
        if quiz_config.get('shuffle_answers', False):
            print("DEBUG: Shuffling MCQ answer options.")
            for question in quiz_questions:
                if question.get('type') == 'MCQ' and isinstance(question.get('options'), list):
                     # Important: Shuffle a *copy* if you don't want to affect the stored data
                     # For now, let's shuffle in place just for this student's attempt
                     random.shuffle(question['options'])
                     # NOTE: Shuffling options means the stored `correct_answer` (which holds option IDs)
                     # is now potentially incorrect *relative to the shuffled order*.
                     # The grading logic (API-4) MUST compare student's selected option ID(s)
                     # against the original `correct_answer` list, NOT based on the shuffled index.

        # --- Prepare Data Payload for Student ---
        # Remove sensitive/internal data before sending
        prepared_quiz = {
            'id': target_quiz.get('id'),
            'title': target_quiz.get('title'),
            'description': target_quiz.get('description'),
            'config': { # Send only relevant config for student UI
                'duration': quiz_config.get('duration'),
                'presentation_mode': quiz_config.get('presentation_mode', 'all'),
                'allow_back': quiz_config.get('allow_back', True),
            },
            'questions': [] # Prepare questions below
        }

        for q in quiz_questions:
             prepared_q = {
                 'id': q.get('id'),
                 'text': q.get('text'),
                 'type': q.get('type'),
                 'score': q.get('score', 1), # Send score for potential display? Optional.
                 'media_url': q.get('media_url'), # Send media URL if present
                 'options': [] # Prepare options below (only for MCQ)
             }
             # Send only option ID and Text, DO NOT SEND correct_answer IDs
             if q.get('type') == 'MCQ' and isinstance(q.get('options'), list):
                  prepared_q['options'] = [
                      {'id': opt.get('id'), 'text': opt.get('text')}
                      for opt in q.get('options', []) if isinstance(opt, dict) # Basic safety check
                  ]
             prepared_quiz['questions'].append(prepared_q)

        print(f"DEBUG: Returning prepared quiz data for student. Quiz ID: {prepared_quiz['id']}, Question Count: {len(prepared_quiz['questions'])}")
        return JsonResponse(prepared_quiz)


    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request format.'}, status=400)
    except Exception as e:
        print(f"Error accessing quiz with key: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)
    


@csrf_exempt # Student submissions likely won't have CSRF from standard forms
@require_http_methods(["POST"])
def quiz_submit_api(request, quiz_id):
    """
    API endpoint for students to submit their completed quiz answers.
    Performs grading, calculates score, stores attempt, and returns feedback.
    """
    try:
        submission_data = json.loads(request.body)
        print(f"DEBUG: Received submission for quiz_id: {quiz_id}") # Log

        # --- Extract data from submission ---
        student_info = submission_data.get('student_info')
        student_answers = submission_data.get('answers') # { question_id: answer }
        # Timestamps likely sent as JS Date.now() milliseconds - convert if needed
        # start_time_ms = submission_data.get('start_time')
        # end_time_ms = submission_data.get('end_time')
        # submitted_due_to_timeout = submission_data.get('submitted_due_to_timeout', False)

        # Basic validation
        if not student_info or not isinstance(student_info, dict) or not student_info.get('name'):
             return JsonResponse({'error': 'Missing or invalid student information.'}, status=400)
        if not student_answers or not isinstance(student_answers, dict):
             return JsonResponse({'error': 'Missing or invalid answers data.'}, status=400)

        # --- Load Quiz and Question Data ---
        data = load_data()
        all_quizzes = data.get('quizzes', [])
        all_questions = data.get('questions', [])
        target_quiz = None

        for q in all_quizzes:
             if str(q.get('id')) == str(quiz_id):
                  target_quiz = q
                  break

        if target_quiz is None:
             return JsonResponse({'error': 'Quiz not found.'}, status=404)
        # Should not happen if access key was validated, but good check
        if target_quiz.get('archived'):
             return JsonResponse({'error': 'Cannot submit to an archived quiz.'}, status=403)

        quiz_config = target_quiz.get('config', {})
        pass_score_threshold = Decimal(quiz_config.get('pass_score', 70)) # Use Decimal

        # Get relevant questions for this quiz
        question_ids_in_quiz = set(target_quiz.get('questions', []))
        questions_in_quiz_dict = {
             str(q.get('id')): q for q in all_questions if str(q.get('id')) in question_ids_in_quiz
        }

        # --- Perform Grading ---
        total_score_achieved = Decimal(0)
        max_possible_score = Decimal(0)
        graded_details = [] # Optional detailed results

        for q_id, question_data in questions_in_quiz_dict.items():
            q_id_str = str(q_id) # Ensure consistency
            question_score = Decimal(question_data.get('score', 1)) # Use Decimal
            max_possible_score += question_score # Add to max score for this quiz attempt
            question_type = question_data.get('type')
            student_answer = student_answers.get(q_id_str) # Get student's answer for this question

            is_correct = None # None = not auto-graded/applicable, True/False otherwise
            score_awarded = Decimal(0)
            needs_manual_review = False

            if student_answer is not None: # Only grade if student provided an answer
                if question_type == 'MCQ':
                     correct_option_ids = set(question_data.get('correct_answer', []))
                     # Student answer for MCQ should be a list of selected option IDs
                     if isinstance(student_answer, list):
                          selected_option_ids = set(student_answer)
                          # Exact match required for correctness (all correct selected, no incorrect selected)
                          is_correct = (selected_option_ids == correct_option_ids)
                          if is_correct:
                               score_awarded = question_score
                     else:
                          is_correct = False # Invalid answer format

                elif question_type == 'SHORT_TEXT':
                     review_mode = question_data.get('short_answer_review_mode', 'manual')
                     if review_mode == 'auto':
                          correct_text = question_data.get('short_answer_correct_text')
                          if correct_text is not None and isinstance(student_answer, str):
                               # Case-INSENSITIVE comparison after trimming whitespace
                               is_correct = (student_answer.strip().lower() == correct_text.lower())
                               if is_correct:
                                   score_awarded = question_score
                          else:
                               is_correct = False # Cannot auto-grade if no correct text stored or invalid student answer
                     else: # Manual review mode
                          needs_manual_review = True
                          is_correct = None # Mark as needing review

                # Add logic for other question types here later

            # Accumulate total score
            total_score_achieved += score_awarded

            # Store detailed result (optional)
            graded_details.append({
                "question_id": q_id_str,
                "is_correct": is_correct,
                "score_awarded": float(score_awarded.quantize(Decimal("0.01"), ROUND_HALF_UP)), # Store as float
                "needs_manual_review": needs_manual_review
            })

        # Calculate percentage
        percentage = Decimal(0)
        if max_possible_score > 0:
             percentage = (total_score_achieved / max_possible_score) * 100
             # Round to reasonable precision, e.g., 2 decimal places
             percentage = percentage.quantize(Decimal("0.01"), ROUND_HALF_UP)

        passed = percentage >= pass_score_threshold

        # --- Prepare Attempt Record ---
        attempt_id = str(uuid.uuid4())
        # Convert timestamps if they were milliseconds
        # start_time_iso = datetime.datetime.fromtimestamp(start_time_ms / 1000).isoformat() if start_time_ms else None
        # end_time_iso = datetime.datetime.fromtimestamp(end_time_ms / 1000).isoformat() if end_time_ms else datetime.datetime.now().isoformat()
        # Using simple now() for timestamps for now, as frontend isn't sending them yet fully
        start_time_iso = submission_data.get('start_time') or datetime.datetime.now(datetime.timezone.utc).isoformat()
        end_time_iso = submission_data.get('end_time') or datetime.datetime.now(datetime.timezone.utc).isoformat()
        submitted_due_to_timeout = submission_data.get('submitted_due_to_timeout', False)


        new_attempt = {
            "attempt_id": attempt_id,
            "quiz_id": str(quiz_id),
            "quiz_title_at_submission": target_quiz.get('title', 'N/A'),
            "student_info": student_info,
            "answers": student_answers, # Store what student submitted
            "score_achieved": float(total_score_achieved.quantize(Decimal("0.01"), ROUND_HALF_UP)), # Store as float
            "max_possible_score": float(max_possible_score.quantize(Decimal("0.01"), ROUND_HALF_UP)), # Store as float
            "percentage": float(percentage), # Store as float
            "passed": bool(passed),
            "pass_score_threshold": float(pass_score_threshold), # Store threshold used
            "start_time": start_time_iso,
            "end_time": end_time_iso,
            "submitted_due_to_timeout": submitted_due_to_timeout,
            "graded_details": graded_details # Store detailed results
        }

        # --- Save Attempt ---
        all_attempts = data.get('attempts', [])
        all_attempts.append(new_attempt)
        data['attempts'] = all_attempts
        save_data(data)

        print(f"DEBUG: Stored attempt {attempt_id} for quiz {quiz_id}. Score: {percentage}%") # Log

        # --- Return Feedback ---
        feedback_payload = {
            "attempt_id": attempt_id,
            "score": float(percentage), # Send percentage score
            "passed": bool(passed),
            "max_score": float(max_possible_score), # Maybe useful
            "achieved_score": float(total_score_achieved) # Maybe useful
            # Optionally include correct answers here based on teacher config later
        }
        return JsonResponse(feedback_payload, status=201) # 201 Created

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid submission format.'}, status=400)
    except Exception as e:
        print(f"Error processing submission for quiz {quiz_id}: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'An unexpected error occurred during submission: {str(e)}'}, status=500)
    

# quiz/views.py
# ... existing imports ...

@api_teacher_required
@require_http_methods(["GET"])
def get_quiz_attempts_api(request, quiz_id):
    """
    API endpoint for teachers to retrieve a summary list of attempts
    for a specific quiz.
    """
    try:
        data = load_data()
        all_attempts = data.get('attempts', [])
        quiz_id_str = str(quiz_id) # Ensure comparison type consistency

        # Filter attempts for the specific quiz
        quiz_attempts = [
            attempt for attempt in all_attempts
            if str(attempt.get('quiz_id')) == quiz_id_str
        ]

        # Sort attempts, e.g., by submission time descending
        quiz_attempts.sort(key=lambda x: x.get('end_time', ''), reverse=True)

        # Prepare summarized data to return (avoid sending raw answers here)
        summarized_attempts = [
            {
                "attempt_id": att.get('attempt_id'),
                "student_name": att.get('student_info', {}).get('name', 'N/A'),
                "student_class": att.get('student_info', {}).get('class', ''),
                "student_id_number": att.get('student_info', {}).get('id', ''),
                "score_percentage": att.get('percentage'),
                "passed": att.get('passed'),
                "submission_time": att.get('end_time'), # ISO format timestamp
                "submitted_due_to_timeout": att.get('submitted_due_to_timeout', False)
            }
            for att in quiz_attempts
        ]

        print(f"DEBUG: Returning {len(summarized_attempts)} attempt summaries for quiz {quiz_id}")
        return JsonResponse({'attempts': summarized_attempts})

    except Exception as e:
        print(f"Error fetching attempts for quiz {quiz_id}: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)
    
def _get_attempts_for_quiz(quiz_id_to_find):
    """Helper function to fetch and sort attempts for reuse."""
    data = load_data()
    all_attempts = data.get('attempts', [])
    quiz_id_str = str(quiz_id_to_find)
    quiz_attempts = [
        attempt for attempt in all_attempts
        if str(attempt.get('quiz_id')) == quiz_id_str
    ]
    quiz_attempts.sort(key=lambda x: x.get('end_time', ''), reverse=True)
    # Also fetch quiz title for filename
    quiz_title = 'UnknownQuiz'
    all_quizzes = data.get('quizzes', [])
    for q in all_quizzes:
        if str(q.get('id')) == quiz_id_str:
            quiz_title = q.get('title', 'Quiz').replace(' ', '_') # Safe title for filename
            break
    return quiz_attempts, quiz_title

@api_teacher_required
@require_http_methods(["GET"])
def export_quiz_attempts_json_api(request, quiz_id):
    """Exports attempts for a specific quiz as a JSON file."""
    try:
        quiz_attempts, quiz_title = _get_attempts_for_quiz(quiz_id)
        if not quiz_attempts:
            # Optionally return empty file or error? Let's return empty for now.
             pass

        # Select fields for export (can be more detailed than summary list)
        export_data = [
             {
                "Attempt ID": att.get('attempt_id'),
                "Student Name": att.get('student_info', {}).get('name', 'N/A'),
                "Student Class": att.get('student_info', {}).get('class', ''),
                "Student ID/Number": att.get('student_info', {}).get('id', ''),
                "Score (%)": att.get('percentage'),
                "Score Achieved": att.get('score_achieved'),
                "Max Score": att.get('max_possible_score'),
                "Passed": att.get('passed'),
                "Submission Time (UTC)": att.get('end_time'),
                "Timed Out": att.get('submitted_due_to_timeout', False),
                "Answers": att.get('answers'), # Include raw answers in JSON export
                "Graded Details": att.get('graded_details') # Include grading details
            }
            for att in quiz_attempts
        ]

        json_export_data = json.dumps({"quiz_results": export_data}, indent=2)
        filename = f"results_{quiz_title}_{quiz_id}.json"
        response = HttpResponse(json_export_data, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        # Handle errors appropriately, maybe return JSON error response
        print(f"Error exporting JSON results for quiz {quiz_id}: {e}")
        return JsonResponse({'error': 'Failed to generate JSON export.'}, status=500)

@api_teacher_required
@require_http_methods(["GET"])
def export_quiz_attempts_excel_api(request, quiz_id):
    """Exports attempts for a specific quiz as an Excel (.xlsx) file."""
    try:
        quiz_attempts, quiz_title = _get_attempts_for_quiz(quiz_id)

        # Create Excel workbook and sheet
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"Quiz Results ({quiz_title[:20]})" # Sheet title limit

        # Define headers
        headers = [
            "Attempt ID", "Student Name", "Student Class", "Student ID/Number",
            "Score (%)", "Passed", "Submission Time (UTC)", "Timed Out",
            "Score Achieved", "Max Score"
            # Avoid exporting raw answers/details to basic Excel for simplicity,
            # can be added as separate sheets or complex cells if needed later.
        ]
        ws.append(headers)

        # Add data rows
        for att in quiz_attempts:
            passed_text = "Yes" if att.get('passed') else "No"
            timeout_text = "Yes" if att.get('submitted_due_to_timeout', False) else "No"
            row = [
                att.get('attempt_id', ''),
                att.get('student_info', {}).get('name', 'N/A'),
                att.get('student_info', {}).get('class', ''),
                att.get('student_info', {}).get('id', ''),
                att.get('percentage', ''),
                passed_text,
                att.get('end_time', ''),
                timeout_text,
                att.get('score_achieved', ''),
                att.get('max_possible_score', '')
            ]
            ws.append(row)

        # Optional: Adjust column widths
        for i, column_cells in enumerate(ws.columns):
             max_length = max(len(str(cell.value)) for cell in column_cells)
             adjusted_width = (max_length + 2)
             ws.column_dimensions[get_column_letter(i + 1)].width = adjusted_width

        # Prepare HTTP response
        filename = f"results_{quiz_title}_{quiz_id}.xlsx"
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        wb.save(response) # Save workbook content to the response
        return response

    except Exception as e:
         print(f"Error exporting Excel results for quiz {quiz_id}: {e}")
         return JsonResponse({'error': 'Failed to generate Excel export.'}, status=500)