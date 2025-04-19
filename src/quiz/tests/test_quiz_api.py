# src/quiz/tests/test_quiz_api.py
import pytest
import json
import uuid # For testing 404 with valid UUID format
import copy # For potentially modifying baseline data if needed in specific tests
from pathlib import Path # To interact with the fixture path object
from django.urls import reverse
from django.contrib.auth.models import User
# Import the module to make patching easier via string path
import core.json_storage
from unittest.mock import patch # Import patch for decorating tests

# Mark tests as needing DB access for user creation/login
pytestmark = pytest.mark.django_db

# --- Fixtures ---

@pytest.fixture
def api_client(client):
    """ Creates a teacher user and returns a logged-in client """
    user = User.objects.create_user(username='quiztester', password='password123', is_staff=True)
    client.login(username='quiztester', password='password123')
    print("\n[Fixture api_client] Logged in quiztester")
    return client

# Note: 'baseline_test_data' fixture (session-scoped) comes from src/conftest.py
# Note: 'isolated_json_file' fixture (function-scoped) comes from src/conftest.py

# --- Helper Function ---
def read_json_from_file(file_path: Path):
    """ Reads and parses JSON from the given file path. """
    print(f"[Helper Read] Reading JSON from: {file_path}")
    if not file_path.exists():
        print(f"[Helper Read] File not found: {file_path}")
        return None # Or maybe raise error? Returning None for now.
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            print(f"[Helper Read] Success. Quizzes: {len(data.get('quizzes',[]))}")
            return data
    except Exception as e:
        print(f"[Helper Read] Error reading file: {e}")
        return None # Return None on error

# --- Test Cases ---

# --- Quiz List/Create Tests (API-1) ---

def test_get_quiz_list_authenticated(api_client, baseline_test_data):
    print("\n--- Test: test_get_quiz_list_authenticated ---")
    url = reverse('quiz:quiz_list_create')
    response = api_client.get(url)
    assert response.status_code == 200
    assert len(response.json()['quizzes']) == len(baseline_test_data['quizzes'])
    assert response.json()['quizzes'][0]['id'] == baseline_test_data['quizzes'][0]['id']

def test_get_quiz_list_unauthenticated(client): # Uses basic non-logged-in client
     """ Test fetching quizzes when not authenticated """
     print("\n--- Test: test_get_quiz_list_unauthenticated ---")
     url = reverse('quiz:quiz_list_create')
     response = client.get(url)
     assert response.status_code == 401 # Expect Unauthorized (due to @api_teacher_required)


def test_create_quiz_success(api_client, baseline_test_data):
    """ Test successfully creating a new quiz """
    print("\n--- Test: test_create_quiz_success ---")
    url = reverse('quiz:quiz_list_create')
    payload = {'title': 'New Test Quiz', 'description': 'A brand new quiz'}
    print("[Test Create] Sending POST request...")
    response = api_client.post(url, json.dumps(payload), content_type='application/json')
    print(f"[Test Create] POST Response Status: {response.status_code}")

    assert response.status_code == 201
    # ... other response assertions ...
    new_quiz_response = response.json()['quiz']

    # --- Verification: Use the mocked load_data ---
    print("[Test Create] Reloading data using mocked load_data...")
    saved_data = core.json_storage.load_data() # Call the MOCKED function
    print(f"[Test Create] Data loaded for assertion. Quiz count: {len(saved_data.get('quizzes',[]))}")
    # Check count
    assert len(saved_data['quizzes']) == len(baseline_test_data['quizzes']) + 1
    # Check content
    assert any(q['id'] == new_quiz_response['id'] for q in saved_data['quizzes'])



# No explicit patching needed
def test_create_quiz_fail_no_title(api_client):
    """ Test creating quiz failure when title is missing """
    print("\n--- Test: test_create_quiz_fail_no_title ---")
    url = reverse('quiz:quiz_list_create')
    payload = {'description': 'Missing title'}
    response = api_client.post(url, json.dumps(payload), content_type='application/json')
    assert response.status_code == 400
    assert 'title is required' in response.json()['error']


# --- Quiz Detail Tests (API-1) ---

# GET test doesn't modify data, only needs load mocked
# No explicit patching needed
def test_get_quiz_detail_success(api_client, baseline_test_data):
    """ Test fetching details of a specific quiz """
    print("\n--- Test: test_get_quiz_detail_success ---")
    quiz_id = baseline_test_data['quizzes'][0]['id']
    url = reverse('quiz:quiz_detail', kwargs={'quiz_id': quiz_id})
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()['quiz']['id'] == quiz_id

# GET test doesn't modify data, only needs load mocked
def test_get_quiz_detail_not_found(api_client):
    """ Test fetching details of non-existent quiz using a valid UUID format """
    print("\n--- Test: test_get_quiz_detail_not_found ---")
    non_existent_uuid = str(uuid.uuid4()) # Generate valid UUID format
    print(f"DEBUG: Testing 404 with non-existent UUID: {non_existent_uuid}")
    url = reverse('quiz:quiz_detail', kwargs={'quiz_id': non_existent_uuid})
    response = api_client.get(url)
    assert response.status_code == 404



def test_update_quiz_success(api_client, baseline_test_data):
    """ Test updating a quiz """
    print("\n--- Test: test_update_quiz_success ---")
    quiz_id = baseline_test_data['quizzes'][0]['id']
    valid_question_id = baseline_test_data['questions'][0]['id'] # Get correct UUID
    url = reverse('quiz:quiz_detail', kwargs={'quiz_id': quiz_id})
    payload = {
        'title': 'UPDATED Title',
        'description': 'UPDATED Desc',
        'config': {'duration': 99, 'pass_score': 85, 'randomize_questions': True, 'allow_back': False},
        'questions': [valid_question_id] # Use correct UUID
    }
    print(f"[Test Update] Sending PUT request for quiz {quiz_id}...")
    response = api_client.put(url, json.dumps(payload), content_type='application/json')
    print(f"[Test Update] PUT Response Status: {response.status_code}")

    assert response.status_code == 200
    # ... assertions on response ...
    updated_quiz_response = response.json()['quiz']
    assert updated_quiz_response['title'] == 'UPDATED Title'
    assert updated_quiz_response['questions'] == [valid_question_id] # Assert using correct UUID

    # --- Verification: Use mocked load_data ---
    print("[Test Update] Reloading data using mocked load_data...")
    saved_data = core.json_storage.load_data() # Call MOCKED function
    print(f"[Test Update] Data loaded for assertion. Quiz count: {len(saved_data.get('quizzes',[]))}")
    saved_quiz = next((q for q in saved_data['quizzes'] if q['id'] == quiz_id), None)
    print(f"[Test Update] Found saved quiz data: {saved_quiz}")
    assert saved_quiz is not None
    assert saved_quiz['title'] == 'UPDATED Title'


def test_delete_quiz_success(api_client, baseline_test_data):
     """ Test deleting a quiz """
     print("\n--- Test: test_delete_quiz_success ---")
     quiz_id_to_delete = baseline_test_data['quizzes'][0]['id']
     initial_quiz_count = len(baseline_test_data['quizzes'])
     url = reverse('quiz:quiz_detail', kwargs={'quiz_id': quiz_id_to_delete})
     print(f"[Test Delete] Sending DELETE request for quiz {quiz_id_to_delete}...")
     response = api_client.delete(url)
     print(f"[Test Delete] DELETE Response Status: {response.status_code}")
     assert response.status_code == 200

     # --- Verification: Use mocked load_data ---
     print("[Test Delete] Reloading data using mocked load_data...")
     saved_data = core.json_storage.load_data() # Call MOCKED function
     print(f"[Test Delete] Data loaded for assertion. Quiz count: {len(saved_data.get('quizzes',[]))}")
     assert len(saved_data['quizzes']) == initial_quiz_count - 1
     assert not any(q['id'] == quiz_id_to_delete for q in saved_data['quizzes'])



# --- TODO: Add tests for Question APIs (API-2) ---
# --- TODO: Add tests for Quiz Access API (API-3) ---
# --- TODO: Add tests for Quiz Submission API (API-4) ---
# --- TODO: Add tests for Export APIs ---