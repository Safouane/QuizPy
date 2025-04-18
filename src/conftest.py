# src/conftest.py
import pytest
import json
import os
import shutil
from pathlib import Path
from unittest.mock import patch
import copy # Import copy for deep copies
import uuid # Import uuid

# --- Generate Consistent UUIDs for Baseline Data ---
# Generate once so IDs are consistent across test runs if needed,
# but they will be different each time conftest.py is loaded.
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
            "score": 10,
            "difficulty": "Easy",
            "category": "Test",
            "media_url": None,
            "short_answer_review_mode": "manual", # Default even if not Short Text
            "short_answer_correct_text": None
        },
        {
            "id": q_st_1_id, # UUID String
            "quiz_ids": [quiz_1_id], # LIST of quiz UUID Strings
            "text": "Short Text Question 1?",
            "type": "SHORT_TEXT",
            "options": [], # Empty LIST for non-MCQ
            "correct_answer": [], # Empty LIST for non-MCQ
            "score": 5,
            "difficulty": "Medium",
            "category": "Test",
            "media_url": None,
            "short_answer_review_mode": "manual",
            "short_answer_correct_text": None
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
            "score": 2,
            "difficulty": "Hard",
            "category": "Bank",
            "media_url": None,
            "short_answer_review_mode": "manual",
            "short_answer_correct_text": None
        }
    ],
    "attempts": [] # Empty LIST for attempts
}

# --- Fixtures ---

@pytest.fixture(scope='session')
def baseline_test_data():
    """Provides the baseline dictionary for tests to use."""
    # Return a deep copy to ensure baseline isn't modified by tests using the fixture directly
    # (though isolated_json_storage provides the main isolation)
    return copy.deepcopy(BASELINE_TEST_DATA)

@pytest.fixture(scope='function', autouse=True)
def isolated_json_storage(tmp_path, monkeypatch, baseline_test_data): # Takes baseline data
    """
    Pytest fixture to redirect json_storage operations to temporary memory/file
    for test isolation. Resets the state for each test function using a deep
    copy of the baseline data.
    """
    temp_data_path = tmp_path / "test_quiz_data.json"
    print(f"\n[Fixture] Using temporary data file: {temp_data_path}")

    # --- Use an in-memory dict container for the state ---
    fixture_state = {
        'current_data': copy.deepcopy(baseline_test_data) # USE FIXTURE ARGUMENT
    }
    print(f"[Fixture] Initialized fixture_state with {len(fixture_state['current_data'].get('quizzes',[]))} quizzes.")

    # Write initial state to temp file (mostly for debugging/reference)
    try:
        with open(temp_data_path, 'w') as f:
            # Use fixture_state['current_data'] which is already a deep copy
            json.dump(fixture_state['current_data'], f, indent=2)
        print(f"[Fixture] Wrote initial state to {temp_data_path}")
    except Exception as e:
        print(f"[Fixture] Error writing initial temp file: {e}") # Log JSON serializable error if baseline is wrong


    # --- Mock load_data ---
    def mock_load_data():
        print(f"[Mock Load] Returning current in-memory state (test: {os.environ.get('PYTEST_CURRENT_TEST')})")
        # Return a DEEP COPY from the fixture's state dict
        return copy.deepcopy(fixture_state['current_data'])

    # --- Mock save_data ---
    def mock_save_data(data_to_save):
        print(f"[Mock Save] Updating in-memory state (test: {os.environ.get('PYTEST_CURRENT_TEST')})")
        # Update the state stored within the fixture's container dict
        fixture_state['current_data'] = copy.deepcopy(data_to_save)
        print(f"[Mock Save] fixture_state updated. Quizzes now: {len(fixture_state['current_data'].get('quizzes',[]))}")
        # Optional: Write to temp file as well
        try:
             with open(temp_data_path, 'w') as f:
                json.dump(fixture_state['current_data'], f, indent=2)
        except Exception as e: print(f"[Mock Save] Error writing temp file (ignored): {e}")


    monkeypatch.setattr('core.json_storage.load_data', mock_load_data)
    monkeypatch.setattr('core.json_storage.save_data', mock_save_data)
    print("[Fixture] Patched core.json_storage functions.")

    yield temp_data_path # Test runs here

    print(f"[Fixture] Teardown - final state had {len(fixture_state['current_data'].get('quizzes',[]))} quizzes. Temp file: {temp_data_path}")