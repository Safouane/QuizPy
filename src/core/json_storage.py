# src/core/json_storage.py

import json
import os
import logging # For logging errors
import uuid # For generating unique IDs later if needed

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the default path relative to the project root (QuizPy)
# Assumes the functions might be called from various places, so absolute path is safer.
# Get the project root directory (assuming this file is src/core/json_storage.py)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'quiz_data.json')

def load_quiz_data(file_path: str = DEFAULT_DATA_PATH) -> dict:
    """
    Loads quiz and question data from a JSON file.

    Args:
        file_path (str): The path to the JSON data file.
                         Defaults to 'data/quiz_data.json' in the project root.

    Returns:
        dict: A dictionary containing 'quizzes' and 'questions' lists.
              Returns an empty structure ({'quizzes': [], 'questions': []})
              if the file is not found or contains invalid JSON.
    """
    empty_data = {'quizzes': [], 'questions': []}
    try:
        # Ensure the directory exists before trying to read (less critical for read, but good practice)
        # data_dir = os.path.dirname(file_path)
        # if not os.path.exists(data_dir):
        #     logging.warning(f"Data directory not found: {data_dir}")
        #     return empty_data # Or maybe create it? For read, returning empty is safer.

        if not os.path.exists(file_path):
             logging.warning(f"Data file not found at {file_path}. Returning empty structure.")
             # Optionally create an empty file here if desired for first run:
             # save_quiz_data(empty_data, file_path)
             return empty_data

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Basic validation: Ensure top-level keys exist
            if 'quizzes' not in data or 'questions' not in data:
                 logging.warning(f"Invalid structure in {file_path}. Missing 'quizzes' or 'questions' key. Returning empty structure.")
                 return empty_data
            # Ensure they are lists
            if not isinstance(data.get('quizzes'), list) or not isinstance(data.get('questions'), list):
                 logging.warning(f"Invalid structure in {file_path}. 'quizzes' or 'questions' is not a list. Returning empty structure.")
                 return empty_data

            logging.info(f"Successfully loaded data from {file_path}")
            return data

    except FileNotFoundError:
        logging.warning(f"Data file not found at {file_path}. Returning empty structure.")
        # Optionally create an empty file here if desired for first run:
        # save_quiz_data(empty_data, file_path)
        return empty_data
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from {file_path}. File might be corrupted. Returning empty structure.")
        return empty_data
    except Exception as e:
        logging.error(f"An unexpected error occurred while loading data from {file_path}: {e}", exc_info=True)
        return empty_data


def save_quiz_data(data: dict, file_path: str = DEFAULT_DATA_PATH) -> bool:
    """
    Saves quiz and question data to a JSON file.

    Args:
        data (dict): The dictionary containing 'quizzes' and 'questions' lists to save.
        file_path (str): The path to the JSON data file.
                         Defaults to 'data/quiz_data.json' in the project root.

    Returns:
        bool: True if saving was successful, False otherwise.
    """
    try:
        # Ensure the target directory exists
        data_dir = os.path.dirname(file_path)
        os.makedirs(data_dir, exist_ok=True) # exist_ok=True prevents error if dir already exists

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False) # indent for readability
        logging.info(f"Successfully saved data to {file_path}")
        return True
    except TypeError as e:
         logging.error(f"Error preparing data for JSON serialization: {e}. Check data structure.", exc_info=True)
         return False
    except IOError as e:
        logging.error(f"Error writing data to {file_path}: {e}", exc_info=True)
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred while saving data to {file_path}: {e}", exc_info=True)
        return False

# --- Example Usage (Optional - for testing this script directly) ---
if __name__ == '__main__':
    print(f"Project Root detected as: {PROJECT_ROOT}")
    print(f"Default data path: {DEFAULT_DATA_PATH}")

    # 1. Load existing data (will be empty initially)
    current_data = load_quiz_data()
    print(f"\nLoaded initial data:\n{json.dumps(current_data, indent=2)}")

    # 2. Add some sample data (if it doesn't exist)
    if not current_data['quizzes']:
        print("\nAdding sample quiz and questions...")
        q1_id = str(uuid.uuid4())
        q2_id = str(uuid.uuid4())
        quiz_id = str(uuid.uuid4())

        current_data['questions'].extend([
            {
                "id": q1_id,
                "text": "What keyword is used to define a function in Python?",
                "type": "MCQ",
                "options": ["def", "fun", "define", "function"],
                "correct_answer": "def",
                "score": 5,
                "category": "Python Basics"
            },
            {
                "id": q2_id,
                "text": "What does 'pip' stand for?",
                "type": "TEXT",
                "correct_answer": "Pip Installs Packages", # Or 'Preferred Installer Program'
                "score": 5,
                "category": "Python Tools"
            }
        ])

        current_data['quizzes'].append(
            {
                "id": quiz_id,
                "title": "Intro Python Quiz",
                "description": "A very basic Python quiz.",
                "question_ids": [q1_id, q2_id],
                "config": {
                    "duration": 5,
                    "passing_score": 50,
                    "randomize_questions": False,
                    "shuffle_answers": False,
                    "presentation_mode": "all-at-once",
                     "allow_back_navigation": True
                }
            }
        )

        # 3. Save the updated data
        success = save_quiz_data(current_data)
        if success:
            print("\nSample data saved successfully.")
        else:
            print("\nFailed to save sample data.")

        # 4. Load again to verify
        reloaded_data = load_quiz_data()
        print(f"\nReloaded data after saving:\n{json.dumps(reloaded_data, indent=2)}")
    else:
        print("\nData file already contains quizzes. Skipping sample data addition.")cd..