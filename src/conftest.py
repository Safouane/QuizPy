# src/conftest.py
import pytest
import json
import os
import shutil
from pathlib import Path
import copy # For deep copies
import uuid # For generating UUIDs
# NOTE: unittest.mock is NOT imported here anymore, patching happens in test files

from unittest.mock import patch # Need this for the target object below
import core.json_storage # Import the target module

# --- Generate Consistent UUIDs for Baseline Data ---
# Generate once so IDs are consistent if baseline_test_data fixture is used multiple times
# They will still be different each time pytest starts.
quiz_1_id = str(uuid.uuid4())
q_mcq_1_id = str(uuid.uuid4())
q_st_1_id = str(uuid.uuid4())
q_bank_1_id = str(uuid.uuid4())
opt_a_id = str(uuid.uuid4())
opt_b_id = str(uuid.uuid4())
opt_x_id = str(uuid.uuid4())
opt_y_id = str(uuid.uuid4())

# --- Define the Baseline Test Data Structure ---
# Using LISTS [] for all collections intended to be JSON arrays.
# Using UUID strings for all IDs.
# Ensuring 'config' is a dictionary {}.
BASELINE_TEST_DATA = {
    "quizzes": [
        {
            "id": quiz_1_id, # UUID String
            "title": "Baseline Quiz 1",
            "description": "For testing.",
            "questions": [q_mcq_1_id, q_st_1_id], # LIST of question UUID Strings
            "config": { # CONFIG MUST BE A DICTIONARY {}
                "duration": 10,
                "pass_score": 50,
                "presentation_mode": "all",
                "allow_back": True,
                "randomize_questions": False,
                "shuffle_answers": False
            },
            "access_key": "KEY123",
            "archived": False,
            "versions": [] # List for versions
        }
        # Add more baseline quizzes if needed for other tests
    ],
    "questions": [
        {
            "id": q_mcq_1_id, # UUID String
            "quiz_ids": [quiz_1_id], # LIST of quiz UUID Strings
            "text": "MCQ Question 1?",
            "type": "MCQ",
            "options": [ # LIST of option dictionaries
                {"id": opt_a_id, "text": "A"}, # Option ID is UUID String
                {"id": opt_b_id, "text": "B"}  # Option ID is UUID String
            ],
            "correct_answer": [opt_b_id], # LIST containing correct option UUID String(s)
            "score": 10, # Use integer for score
            "difficulty": "Easy",
            "category": "Test",
            "media_url": None,
            "short_answer_review_mode": "manual",
            "short_answer_correct_text": None,
            "mcq_is_single_choice": False # Explicitly add flag
        },
        {
            "id": q_st_1_id, # UUID String
            "quiz_ids": [quiz_1_id], # LIST of quiz UUID Strings
            "text": "Short Text Question 1?",
            "type": "SHORT_TEXT",
            "options": [], # Empty LIST for non-MCQ
            "correct_answer": [], # Empty LIST for non-MCQ
            "score": 5, # Use integer for score
            "difficulty": "Medium",
            "category": "Test",
            "media_url": None,
            "short_answer_review_mode": "manual",
            "short_answer_correct_text": None,
            "mcq_is_single_choice": False # Flag relevant? Add default anyway
        },
        { # Standalone question for bank tests
            "id": q_bank_1_id, # UUID String
            "quiz_ids": [], # Empty LIST
            "text": "Bank Question?",
            "type": "MCQ",
            "options": [ # LIST of option dictionaries
                 {"id": opt_x_id, "text": "X"}, # Option ID is UUID String
                 {"id": opt_y_id, "text": "Y"}  # Option ID is UUID String
            ],
            "correct_answer": [opt_x_id], # LIST containing correct option UUID String(s)
            "score": 2, # Use integer for score
            "difficulty": "Hard",
            "category": "Bank",
            "media_url": None,
            "short_answer_review_mode": "manual",
            "short_answer_correct_text": None,
            "mcq_is_single_choice": False
        }
    ],
    "attempts": [] # Empty LIST for attempts
}
# --- End BASELINE_TEST_DATA ---


# --- Fixtures ---

@pytest.fixture(scope='session') # Session scope means BASELINE_TEST_DATA is copied once per session
def baseline_test_data():
    """Provides a deep copy of the baseline dictionary for tests to use."""
    print("\n[Fixture baseline_test_data] Creating deep copy for session.")
    return copy.deepcopy(BASELINE_TEST_DATA)

@pytest.fixture(scope='function', autouse=True) # Add autouse back
def isolated_json_storage(tmp_path, monkeypatch, baseline_test_data): # Renamed back
    """
    Pytest fixture using monkeypatch to redirect core.json_storage functions
    to use a temporary file for test isolation.
    Applies autouse=True to run for all tests in modules that can see it.
    """
    temp_file = tmp_path / f"test_data_{uuid.uuid4()}.json"
    current_test_name = os.environ.get('PYTEST_CURRENT_TEST', 'unknown test').split(':')[-1].split(' ')[0]
    print(f"\n[Fixture Start] Test: {current_test_name}, Temp File: {temp_file}")

    # Write baseline data initially
    initial_data = copy.deepcopy(baseline_test_data)
    try:
        with open(temp_file, 'w') as f:
            json.dump(initial_data, f, indent=2)
        print(f"[Fixture Write Baseline] Wrote {len(initial_data.get('quizzes',[]))} quizzes.")
    except Exception as e:
        pytest.fail(f"Fixture failed to write baseline data: {e}")

    # --- Mocks that interact with the specific temp_file ---
    def mock_load_data_from_file():
        print(f"[Mock Load] Reading from {temp_file} (Test: {current_test_name})")
        if not temp_file.exists(): return copy.deepcopy(baseline_test_data)
        try:
            with open(temp_file, 'r') as f: data = json.load(f)
            print(f"[Mock Load] Success. Loaded {len(data.get('quizzes', []))} quizzes.")
            return data
        except Exception as e:
             print(f"[Mock Load] ERROR reading file {e}. Returning baseline copy.")
             return copy.deepcopy(baseline_test_data)

    def mock_save_data_to_file(data_to_save):
        print(f"[Mock Save] Writing to {temp_file} (Test: {current_test_name})")
        print(f"[Mock Save] Data has {len(data_to_save.get('quizzes',[]))} quizzes.")
        try:
             with open(temp_file, 'w') as f: json.dump(data_to_save, f, indent=2)
             print(f"[Mock Save] Successfully wrote data to file.")
        except Exception as e: print(f"[Mock Save] ERROR writing file: {e}")


    # --- Use monkeypatch to replace functions *where they are imported/used* ---
    # Assuming your views in src/quiz/views.py do "from core.json_storage import load_data, save_data"
    # Patch the functions within the 'quiz.views' module scope.
    # If other modules also use these, patch them there too if needed for other tests.
    monkeypatch.setattr('quiz.views.load_data', mock_load_data_from_file)
    monkeypatch.setattr('quiz.views.save_data', mock_save_data_to_file)
    # --- Also patch where the test file might call it directly ---
    monkeypatch.setattr(core.json_storage, 'load_data', mock_load_data_from_file)
    monkeypatch.setattr(core.json_storage, 'save_data', mock_save_data_to_file)

    print("[Fixture] Patched json_storage functions in quiz.views and core.json_storage.")

    yield temp_file # Test runs here

    print(f"[Fixture Teardown] Test {current_test_name} finished.")
    # No need to manually restore, monkeypatch handles it.