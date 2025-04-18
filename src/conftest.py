# --- Fixtures ---# src/conftest.py
import pytest
import json
import os
import shutil
from pathlib import Path
from unittest.mock import patch
import copy
import uuid
import time # For potential delay debugging if needed


# --- Define BASELINE_TEST_DATA (with UUIDs and lists) ---
# (Keep the UUID-updated version from previous steps)
quiz_1_id = str(uuid.uuid4())
q_mcq_1_id = str(uuid.uuid4())
q_st_1_id = str(uuid.uuid4())
q_bank_1_id = str(uuid.uuid4())
opt_a_id = str(uuid.uuid4())
opt_b_id = str(uuid.uuid4())
opt_x_id = str(uuid.uuid4())
opt_y_id = str(uuid.uuid4())

BASELINE_TEST_DATA = {
    "quizzes": [
        {
            "id": quiz_1_id, "title": "Baseline Quiz 1", "description": "For testing.",
            "questions": [q_mcq_1_id, q_st_1_id],
            "config": {"duration": 10, "pass_score": 50, "presentation_mode": "all", "allow_back": True, "randomize_questions": False, "shuffle_answers": False},
            "access_key": "KEY123", "archived": False, "versions": []
        }
    ],
    "questions": [
        {
            "id": q_mcq_1_id, "quiz_ids": [quiz_1_id], "text": "MCQ Question 1?", "type": "MCQ",
            "options": [{"id": opt_a_id, "text": "A"}, {"id": opt_b_id, "text": "B"}],
            "correct_answer": [opt_b_id], "score": 10, "difficulty": "Easy", "category": "Test",
             "media_url": None, "short_answer_review_mode": "manual", "short_answer_correct_text": None
        },
        {
            "id": q_st_1_id, "quiz_ids": [quiz_1_id], "text": "Short Text Question 1?", "type": "SHORT_TEXT",
            "options": [], "correct_answer": [], "score": 5, "difficulty": "Medium", "category": "Test",
            "media_url": None, "short_answer_review_mode": "manual", "short_answer_correct_text": None
        },
        {
            "id": q_bank_1_id, "quiz_ids": [], "text": "Bank Question?", "type": "MCQ",
            "options": [{"id": opt_x_id, "text": "X"}, {"id": opt_y_id, "text": "Y"}],
            "correct_answer": [opt_x_id], "score": 2, "difficulty": "Hard", "category": "Bank",
            "media_url": None, "short_answer_review_mode": "manual", "short_answer_correct_text": None
        }
    ],
    "attempts": []
}
# --- End BASELINE_TEST_DATA ---

@pytest.fixture(scope='session')
def baseline_test_data():
    return copy.deepcopy(BASELINE_TEST_DATA)

@pytest.fixture(scope='function', autouse=True)
def isolated_json_storage(tmp_path, monkeypatch, baseline_test_data):
    temp_data_path = tmp_path / "test_quiz_data.json"
    print(f"\n[Fixture Start] Test: {os.environ.get('PYTEST_CURRENT_TEST')}, Path: {temp_data_path}")

    # Write baseline data initially
    try:
        with open(temp_data_path, 'w') as f:
            json.dump(baseline_test_data, f, indent=2)
        print(f"[Fixture Write Baseline] Success. Quizzes: {len(baseline_test_data.get('quizzes',[]))}")
    except Exception as e:
        print(f"[Fixture Write Baseline] ERROR: {e}")
        pytest.fail(f"Fixture failed to write baseline data: {e}") # Fail fast if setup fails

    # --- Define Mocks referencing the specific temp_data_path of this fixture instance ---
    current_test_file_path = temp_data_path # Capture path for mocks

    def mock_load_data():
        test_name = os.environ.get('PYTEST_CURRENT_TEST', 'unknown test')
        print(f"[Mock Load] Attempting read from: {current_test_file_path} (test: {test_name})")
        if not current_test_file_path.exists():
            print("[Mock Load] File does not exist! Returning baseline copy.")
            return copy.deepcopy(baseline_test_data)
        try:
            # Explicitly open and read the file *every time* load is called
            with open(current_test_file_path, 'r') as f:
                loaded_data = json.load(f)
            print(f"[Mock Load] Success. Quizzes loaded: {len(loaded_data.get('quizzes',[]))}")
            return loaded_data # Return fresh content from file
        except Exception as e:
             print(f"[Mock Load] Error reading/parsing file: {e}. Returning baseline copy.")
             return copy.deepcopy(baseline_test_data)

    def mock_save_data(data_to_save):
        test_name = os.environ.get('PYTEST_CURRENT_TEST', 'unknown test')
        print(f"[Mock Save] Attempting write to: {current_test_file_path} (test: {test_name})")
        print(f"[Mock Save] Data to save has {len(data_to_save.get('quizzes',[]))} quizzes.")
        try:
             # Explicitly open, write, and close the file *every time* save is called
             with open(current_test_file_path, 'w') as f:
                json.dump(data_to_save, f, indent=2)
             print(f"[Mock Save] Successfully wrote data to file.")
             # Optional: Short delay sometimes helps file system catch up in tests
             # time.sleep(0.01)
        except Exception as e:
             print(f"[Mock Save] Error writing file: {e}")
             # Consider failing the test if save fails
             # pytest.fail(f"Mock save failed: {e}")


    monkeypatch.setattr('core.json_storage.load_data', mock_load_data)
    monkeypatch.setattr('core.json_storage.save_data', mock_save_data)
    print("[Fixture] Patched core.json_storage functions.")

    yield temp_data_path # Test runs here

    print(f"[Fixture Teardown] Test finished for {current_test_file_path}")
    # Add final check of file content on teardown for debugging
    if current_test_file_path.exists():
        try:
            with open(current_test_file_path, 'r') as f:
                final_data = json.load(f)
            print(f"[Fixture Teardown] Final quiz count in file: {len(final_data.get('quizzes', []))}")
        except Exception as e:
            print(f"[Fixture Teardown] Error reading final file state: {e}")