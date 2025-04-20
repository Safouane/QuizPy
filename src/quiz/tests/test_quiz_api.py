# src/quiz/tests/test_quiz_api.py
import pytest
import json
import uuid
import copy
from pathlib import Path
from django.urls import reverse
from django.contrib.auth.models import User
import core.json_storage # Import module to call potentially mocked functions
# REMOVE: from unittest.mock import patch

pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client(client):
    user = User.objects.create_user(username='quiztester', password='password123', is_staff=True)
    client.login(username='quiztester', password='password123')
    print("\n[Fixture api_client] Logged in quiztester")
    return client

# Fixtures baseline_test_data and isolated_json_storage (autouse) are from conftest.py

# Helper function (optional, can use core.json_storage.load_data directly)
def read_temp_data():
    print("[Test Helper] Calling core.json_storage.load_data() for verification...")
    return core.json_storage.load_data()

# --- Test Cases ---

def test_get_quiz_list_authenticated(api_client, baseline_test_data):
    """ Test fetching the list of quizzes when authenticated. """
    print("\n--- Test: test_get_quiz_list_authenticated ---")
    url = reverse('quiz:quiz_list_create')
    response = api_client.get(url)
    assert response.status_code == 200
    # No need to read file directly, view uses mocked load_data
    assert len(response.json()['quizzes']) == len(baseline_test_data['quizzes'])
    assert response.json()['quizzes'][0]['id'] == baseline_test_data['quizzes'][0]['id']

def test_get_quiz_list_unauthenticated(client):
     """ Test fetching quizzes when not authenticated fails. """
     print("\n--- Test: test_get_quiz_list_unauthenticated ---")
     url = reverse('quiz:quiz_list_create')
     response = client.get(url)
     assert response.status_code == 401

def test_create_quiz_success(api_client, baseline_test_data):
    """ Test successfully creating a new quiz via POST request. """
    print("\n--- Test: test_create_quiz_success ---")
    url = reverse('quiz:quiz_list_create')
    payload = {'title': 'New Test Quiz', 'description': 'A brand new quiz'}
    print("[Test Create] Sending POST request...")
    response = api_client.post(url, json.dumps(payload), content_type='application/json')
    print(f"[Test Create] POST Response Status: {response.status_code}")
    assert response.status_code == 201
    new_quiz_response = response.json()['quiz']
    # ... other response assertions ...

    # --- Verification: Use the mocked load_data function ---
    print("[Test Create] Verifying saved state using mocked load_data...")
    saved_data = read_temp_data() # Use helper or call core.json_storage.load_data()
    assert saved_data is not None, "Mocked load_data returned None"
    saved_quizzes = saved_data.get('quizzes', [])
    print(f"[Test Create] Mocked load_data returned quiz count: {len(saved_quizzes)}")
    assert len(saved_quizzes) == len(baseline_test_data['quizzes']) + 1
    assert any(q['id'] == new_quiz_response['id'] for q in saved_quizzes)

def test_create_quiz_fail_no_title(api_client):
    """ Test creating quiz failure when title is missing. """
    print("\n--- Test: test_create_quiz_fail_no_title ---")
    url = reverse('quiz:quiz_list_create')
    payload = {'description': 'Missing title'}
    response = api_client.post(url, json.dumps(payload), content_type='application/json')
    assert response.status_code == 400
    assert 'title is required' in response.json().get('error', '')
    # Cannot easily assert mock_save wasn't called without injecting it

def test_get_quiz_detail_success(api_client, baseline_test_data):
    """ Test fetching details of a specific existing quiz. """
    print("\n--- Test: test_get_quiz_detail_success ---")
    quiz_id = baseline_test_data['quizzes'][0]['id']
    url = reverse('quiz:quiz_detail', kwargs={'quiz_id': quiz_id})
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()['quiz']['id'] == quiz_id

def test_get_quiz_detail_not_found(api_client):
    """ Test fetching details of non-existent quiz using a valid UUID format returns 404. """
    print("\n--- Test: test_get_quiz_detail_not_found ---")
    non_existent_uuid = str(uuid.uuid4())
    url = reverse('quiz:quiz_detail', kwargs={'quiz_id': non_existent_uuid})
    response = api_client.get(url)
    assert response.status_code == 404

def test_update_quiz_success(api_client, baseline_test_data):
    """ Test updating an existing quiz via PUT request. """
    print("\n--- Test: test_update_quiz_success ---")
    quiz_id = baseline_test_data['quizzes'][0]['id']
    valid_question_id = baseline_test_data['questions'][0]['id']
    url = reverse('quiz:quiz_detail', kwargs={'quiz_id': quiz_id})
    payload = {
        'title': 'UPDATED Title', 'description': 'UPDATED Desc',
        'config': {'duration': 99, 'pass_score': 85, 'randomize_questions': True, 'allow_back': False, 'shuffle_answers': True},
        'questions': [valid_question_id]
    }
    print(f"[Test Update] Sending PUT request for quiz {quiz_id}...")
    response = api_client.put(url, json.dumps(payload), content_type='application/json')
    print(f"[Test Update] PUT Response Status: {response.status_code}")
    assert response.status_code == 200
    # ... assertions on response ...

    # --- Verification: Use the mocked load_data function ---
    print("[Test Update] Verifying saved state using mocked load_data...")
    saved_data = read_temp_data()
    assert saved_data is not None
    saved_quiz = next((q for q in saved_data['quizzes'] if q['id'] == quiz_id), None)
    print(f"[Test Update] Found saved quiz data via mock load: {saved_quiz}")
    assert saved_quiz is not None
    assert saved_quiz['title'] == 'UPDATED Title'

def test_delete_quiz_success(api_client, baseline_test_data):
     """ Test deleting an existing quiz via DELETE request. """
     print("\n--- Test: test_delete_quiz_success ---")
     quiz_id_to_delete = baseline_test_data['quizzes'][0]['id']
     initial_quiz_count = len(baseline_test_data['quizzes'])
     url = reverse('quiz:quiz_detail', kwargs={'quiz_id': quiz_id_to_delete})
     print(f"[Test Delete] Sending DELETE request for quiz {quiz_id_to_delete}...")
     response = api_client.delete(url)
     print(f"[Test Delete] DELETE Response Status: {response.status_code}")
     assert response.status_code == 200

     # --- Verification: Use the mocked load_data function ---
     print("[Test Delete] Verifying saved state using mocked load_data...")
     saved_data = read_temp_data()
     assert saved_data is not None
     saved_quizzes = saved_data.get('quizzes', [])
     print(f"[Test Delete] Mocked load_data returned quiz count: {len(saved_quizzes)}")
     assert len(saved_quizzes) == initial_quiz_count - 1
     assert not any(q['id'] == quiz_id_to_delete for q in saved_quizzes)

# ... placeholders for other tests ...