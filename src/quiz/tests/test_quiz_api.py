# src/quiz/tests/test_api.py
import pytest
import json
from django.urls import reverse
from django.contrib.auth.models import User # Import User if needed for login

pytestmark = pytest.mark.django_db # Needed for login

@pytest.fixture
def api_client(client):
    # Log in the teacher user for most tests in this module
    user = User.objects.create_user(username='quiztester', password='password123', is_staff=True)
    client.login(username='quiztester', password='password123')
    return client

# --- Quiz List/Create Tests (API-1) ---

def test_get_quiz_list_authenticated(api_client, isolated_json_storage, baseline_test_data):
    """ Test fetching the list of quizzes when authenticated """
    url = reverse('quiz:quiz_list_create')
    response = api_client.get(url)
    assert response.status_code == 200
    # Check if the response contains the quiz from baseline data
    assert len(response.json()['quizzes']) == 1
    assert response.json()['quizzes'][0]['id'] == baseline_test_data['quizzes'][0]['id']
    assert response.json()['quizzes'][0]['title'] == baseline_test_data['quizzes'][0]['title']

def test_get_quiz_list_unauthenticated(client): # Use base 'client' fixture (not logged in)
     """ Test fetching quizzes when not authenticated """
     url = reverse('quiz:quiz_list_create')
     response = client.get(url)
     assert response.status_code == 401 # Expect Unauthorized (due to @api_teacher_required)

def test_create_quiz_success(api_client, isolated_json_storage):
     """ Test successfully creating a new quiz """
     url = reverse('quiz:quiz_list_create')
     payload = {'title': 'New Test Quiz', 'description': 'A brand new quiz'}
     response = api_client.post(url, json.dumps(payload), content_type='application/json')

     assert response.status_code == 201 # Created
     assert response.json()['message'] == 'Quiz created successfully.'
     new_quiz = response.json()['quiz']
     assert new_quiz['title'] == 'New Test Quiz'
     assert 'id' in new_quiz
     assert 'access_key' in new_quiz # Check key was generated
     assert len(new_quiz['id']) > 10 # Basic UUID check
     assert len(new_quiz['access_key']) > 3 # Basic key check

     # Verify it was saved (by reloading data from the mock)
     from core.json_storage import load_data
     saved_data = load_data()
     assert len(saved_data['quizzes']) == 2 # Baseline + new one
     assert any(q['id'] == new_quiz['id'] for q in saved_data['quizzes'])

def test_create_quiz_fail_no_title(api_client, isolated_json_storage):
     """ Test creating quiz failure when title is missing """
     url = reverse('quiz:quiz_list_create')
     payload = {'description': 'Missing title'}
     response = api_client.post(url, json.dumps(payload), content_type='application/json')
     assert response.status_code == 400 # Bad Request
     assert 'title is required' in response.json()['error']


# --- Quiz Detail Tests (API-1) ---

def test_get_quiz_detail_success(api_client, isolated_json_storage, baseline_test_data):
    """ Test fetching details of a specific quiz """
    quiz_id = baseline_test_data['quizzes'][0]['id']
    url = reverse('quiz:quiz_detail', kwargs={'quiz_id': quiz_id})
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()['quiz']['id'] == quiz_id
    assert response.json()['quiz']['title'] == baseline_test_data['quizzes'][0]['title']

def test_get_quiz_detail_not_found(api_client, isolated_json_storage):
    """ Test fetching details of non-existent quiz """
    url = reverse('quiz:quiz_detail', kwargs={'quiz_id': 'non-existent-uuid'})
    response = api_client.get(url)
    assert response.status_code == 404

def test_update_quiz_success(api_client, isolated_json_storage, baseline_test_data):
    """ Test updating a quiz """
    quiz_id = baseline_test_data['quizzes'][0]['id']
    url = reverse('quiz:quiz_detail', kwargs={'quiz_id': quiz_id})
    payload = {
        'title': 'UPDATED Title',
        'description': 'UPDATED Desc',
        'config': {'duration': 99, 'pass_score': 85, 'randomize_questions': True},
        'questions': ['q-mcq-1'] # Update questions list
    }
    response = api_client.put(url, json.dumps(payload), content_type='application/json')
    assert response.status_code == 200
    updated_quiz = response.json()['quiz']
    assert updated_quiz['title'] == 'UPDATED Title'
    assert updated_quiz['config']['duration'] == 99
    assert updated_quiz['config']['randomize_questions'] == True
    assert updated_quiz['questions'] == ['q-mcq-1']

    # Verify save
    from core.json_storage import load_data
    saved_data = load_data()
    saved_quiz = next(q for q in saved_data['quizzes'] if q['id'] == quiz_id)
    assert saved_quiz['title'] == 'UPDATED Title'
    assert saved_quiz['config']['duration'] == 99
    assert saved_quiz['questions'] == ['q-mcq-1']


def test_delete_quiz_success(api_client, isolated_json_storage, baseline_test_data):
     """ Test deleting a quiz """
     quiz_id = baseline_test_data['quizzes'][0]['id']
     url = reverse('quiz:quiz_detail', kwargs={'quiz_id': quiz_id})
     response = api_client.delete(url)
     assert response.status_code == 200
     assert 'deleted successfully' in response.json()['message']

     # Verify deletion
     from core.json_storage import load_data
     saved_data = load_data()
     assert len(saved_data['quizzes']) == 0 # Should be empty now

# --- TODO: Add tests for Question APIs (API-2) ---
# test_get_question_list_...
# test_create_question_... (MCQ, Short Text)
# test_get_question_detail_...
# test_update_question_...
# test_delete_question_... (check associated quiz lists update)

# --- TODO: Add tests for Quiz Access API (API-3) ---
# test_quiz_access_success_... (check returned structure, randomization)
# test_quiz_access_invalid_key_...
# test_quiz_access_archived_...

# --- TODO: Add tests for Quiz Submission API (API-4) ---
# test_submit_success_... (check score, passed status, attempt saved)
# test_submit_mcq_grading_correct_incorrect_...
# test_submit_short_text_auto_manual_...
# test_submit_invalid_payload_...

# --- TODO: Add tests for Export APIs ---
# test_export_quiz_attempts_json_...
# test_export_quiz_attempts_excel_...
# test_export_quiz_structure_...