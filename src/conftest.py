# src/conftest.py
# Defines shared fixtures for pytest.

import pytest
import json
import os
import sys  # Needed for sys.modules check
from pathlib import Path
import copy
import uuid
from unittest.mock import patch  # Keep for patching targets if needed

# Import the module containing the functions to be mocked
import core.json_storage

# --- Generate Consistent UUIDs for Baseline Data ---
# (Ensures IDs used in baseline data definition are valid UUIDs)
quiz_1_id = str(uuid.uuid4())
q_mcq_1_id = str(uuid.uuid4())
q_st_1_id = str(uuid.uuid4())
q_bank_1_id = str(uuid.uuid4())
opt_a_id = str(uuid.uuid4())
opt_b_id = str(uuid.uuid4())
opt_x_id = str(uuid.uuid4())
opt_y_id = str(uuid.uuid4())

# --- Define the Baseline Test Data Structure ---
# Using correct types (lists, dicts, strings, numbers, booleans, None)
BASELINE_TEST_DATA = {
    "quizzes": [
        {
            "id": quiz_1_id,
            "title": "Baseline Quiz 1",
            "description": "For testing.",
            "questions": [q_mcq_1_id, q_st_1_id],  # List of UUIDs
            "config": {
                "duration": 10,
                "pass_score": 50,
                "presentation_mode": "all",
                "allow_back": True,
                "randomize_questions": False,
                "shuffle_answers": False,
            },
            "access_key": "KEY123",
            "archived": False,
            "versions": [],
        }
    ],
    "questions": [
        {
            "id": q_mcq_1_id,
            "quiz_ids": [quiz_1_id],
            "text": "MCQ Question 1?",
            "type": "MCQ",
            "media_filename": None,
            "options": [
                {"id": opt_a_id, "text": "A", "media_filename": None},
                {"id": opt_b_id, "text": "B", "media_filename": None},
            ],
            "correct_answer": [opt_b_id],
            "score": 10,
            "difficulty": "Easy",
            "category": "Test",
            "mcq_is_single_choice": False,
        },
        {
            "id": q_st_1_id,
            "quiz_ids": [quiz_1_id],
            "text": "Short Text Question 1?",
            "type": "SHORT_TEXT",
            "media_filename": None,
            "options": [],
            "correct_answer": [],
            "score": 5,
            "difficulty": "Medium",
            "category": "Test",
            "short_answer_review_mode": "manual",
            "short_answer_correct_text": None,
            "mcq_is_single_choice": False,
        },
        {
            "id": q_bank_1_id,
            "quiz_ids": [],
            "text": "Bank Question?",
            "type": "MCQ",
            "media_filename": None,
            "options": [
                {"id": opt_x_id, "text": "X", "media_filename": None},
                {"id": opt_y_id, "text": "Y", "media_filename": None},
            ],
            "correct_answer": [opt_x_id],
            "score": 2,
            "difficulty": "Hard",
            "category": "Bank",
            "mcq_is_single_choice": False,
        },
    ],
    "attempts": [],
}
# --- End BASELINE_TEST_DATA ---


# --- Fixtures ---


@pytest.fixture(scope="session")
def baseline_test_data():
    """Provides a deep copy of the baseline dictionary for tests to use."""
    print("\n[Fixture baseline_test_data] Creating deep copy for session.")
    return copy.deepcopy(BASELINE_TEST_DATA)


@pytest.fixture(
    scope="function", autouse=True
)  # autouse applies this to all tests found
def isolated_json_storage(tmp_path, monkeypatch, baseline_test_data):
    """
    Pytest fixture using monkeypatch to redirect core.json_storage functions
    to use a temporary file for test isolation. This runs for every test function.
    """
    # tmp_path is unique per test function, provided by pytest
    temp_file = tmp_path / f"test_data_{uuid.uuid4()}.json"
    current_test_name = (
        os.environ.get("PYTEST_CURRENT_TEST", "unknown test")
        .split(":")[-1]
        .split(" ")[0]
    )
    print(
        f"\n[Fixture isolated_json_storage START] Test: {current_test_name}, Temp File: {temp_file}"
    )

    # Initialize file content with a DEEP COPY of the baseline data for this test run
    initial_data = copy.deepcopy(baseline_test_data)
    try:
        temp_file.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
        with open(temp_file, "w", encoding="utf-8") as f:  # Use utf-8
            json.dump(initial_data, f, indent=2, ensure_ascii=False)
        print(
            f"[Fixture isolated_json_storage] Wrote baseline data ({len(initial_data.get('quizzes',[]))} quizzes) to {temp_file}"
        )
    except Exception as e:
        print(f"[Fixture isolated_json_storage] ERROR writing baseline data: {e}")
        pytest.fail(
            f"Fixture failed to write baseline data: {e}"
        )  # Fail test if setup fails

    # --- Define Mock Functions that operate on this specific temp_file ---
    def mock_load_data_from_file():
        """Reads directly from the specific temp file for this test."""
        print(f"[Mock Load] Reading from {temp_file} (Test: {current_test_name})")
        if not temp_file.exists():
            print("[Mock Load] File does not exist! Returning deep copy of baseline.")
            return copy.deepcopy(baseline_test_data)  # Use baseline copy
        try:
            with open(temp_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(
                f"[Mock Load] Success. Loaded {len(data.get('quizzes', []))} quizzes."
            )
            return data  # Return fresh content from file
        except Exception as e:
            print(f"[Mock Load] ERROR reading file {e}. Returning baseline copy.")
            return copy.deepcopy(baseline_test_data)  # Use baseline copy

    def mock_save_data_to_file(data_to_save):
        """Writes directly to the specific temp file for this test."""
        print(f"[Mock Save] Writing to {temp_file} (Test: {current_test_name})")
        print(
            f"[Mock Save] Data to save has {len(data_to_save.get('quizzes',[]))} quizzes."
        )
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)
            print(f"[Mock Save] Successfully wrote data to file.")
        except Exception as e:
            print(f"[Mock Save] ERROR writing file: {e}")
            # Optionally fail test if save fails:
            # pytest.fail(f"Mock save failed: {e}")

    # --- Apply monkeypatch to replace functions where they are looked up ---
    print("[Fixture] Applying monkeypatch...")

    # 1. Patch the functions in the core.json_storage module itself
    monkeypatch.setattr(core.json_storage, "load_data", mock_load_data_from_file)
    monkeypatch.setattr(core.json_storage, "save_data", mock_save_data_to_file)
    print("[Fixture] Patched core.json_storage.load/save")

    # 2. Patch the functions where they are imported in quiz.views
    #    This is crucial if quiz.views uses "from core.json_storage import ..."
    quiz_views_module = sys.modules.get("quiz.views")
    if quiz_views_module:
        monkeypatch.setattr(
            quiz_views_module, "load_data", mock_load_data_from_file, raising=False
        )
        monkeypatch.setattr(
            quiz_views_module, "save_data", mock_save_data_to_file, raising=False
        )
        print("[Fixture] Patched quiz.views.load/save")
    else:
        print(
            "[Fixture] WARNING: quiz.views module not found in sys.modules during patching."
        )

    # Add patches for other modules if they also import load/save directly
    # Example:
    # core_views_module = sys.modules.get('core.views')
    # if core_views_module:
    #     monkeypatch.setattr(core_views_module, 'load_data', mock_load_data_from_file, raising=False)
    #     monkeypatch.setattr(core_views_module, 'save_data', mock_save_data_to_file, raising=False)
    #     print("[Fixture] Patched core.views.load/save")

    yield temp_file  # Test runs here (the yielded value isn't strictly needed anymore)

    # Teardown: tmp_path fixture handles directory removal automatically
    print(
        f"[Fixture isolated_json_storage END] Test {current_test_name} finished. Temp file was: {temp_file}"
    )
    # Monkeypatch automatically reverts changes after the test function finishes.
