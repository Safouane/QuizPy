from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt # Keep using exempt for now, manage CSRF properly with frontend later
import json
import uuid
from core.json_storage import load_data, save_data
from django.http import HttpResponse


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