# src/authentication/tests/test_api.py
import pytest
import json
from django.urls import reverse
from django.contrib.auth.models import User # Assuming standard User model

# Mark all tests in this module to use the database
pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client(client):
    """ Basic API client fixture """
    return client

@pytest.fixture
def teacher_user(db):
    """ Fixture to create a teacher user """
    user = User.objects.create_user(username='testteacher', password='password123', is_staff=True)
    return user

@pytest.fixture
def non_teacher_user(db):
    """ Fixture to create a non-teacher user """
    user = User.objects.create_user(username='teststudent', password='password123', is_staff=False)
    return user

def test_teacher_login_success(api_client, teacher_user):
    """ Test successful login for a staff user """
    url = reverse('authentication:api_login')
    payload = {'username': 'testteacher', 'password': 'password123'}
    response = api_client.post(url, json.dumps(payload), content_type='application/json')

    assert response.status_code == 200
    assert response.json()['message'] == 'Login successful'
    assert response.json()['username'] == 'testteacher'
    assert '_auth_user_id' in api_client.session # Check if session is set

def test_teacher_login_fail_wrong_password(api_client, teacher_user):
    """ Test login failure with wrong password """
    url = reverse('authentication:api_login')
    payload = {'username': 'testteacher', 'password': 'wrongpassword'}
    response = api_client.post(url, json.dumps(payload), content_type='application/json')

    assert response.status_code == 401 # Unauthorized
    assert 'Invalid credentials' in response.json()['error']
    assert '_auth_user_id' not in api_client.session

def test_teacher_login_fail_not_staff(api_client, non_teacher_user):
    """ Test login failure for a user who is not staff """
    url = reverse('authentication:api_login')
    payload = {'username': 'teststudent', 'password': 'password123'}
    response = api_client.post(url, json.dumps(payload), content_type='application/json')

    assert response.status_code == 403 # Forbidden
    assert 'Not a teacher account' in response.json()['error']
    assert '_auth_user_id' not in api_client.session

def test_teacher_logout(api_client, teacher_user):
    """ Test successful logout """
    # Log in first
    login_url = reverse('authentication:api_login')
    login_payload = {'username': 'testteacher', 'password': 'password123'}
    api_client.post(login_url, json.dumps(login_payload), content_type='application/json')
    assert '_auth_user_id' in api_client.session

    # Then logout
    logout_url = reverse('authentication:api_logout')
    # Logout might be GET or POST depending on implementation, assume POST for safety
    response = api_client.post(logout_url) # No payload needed

    assert response.status_code == 200
    assert 'logged out successfully' in response.json()['message']
    assert '_auth_user_id' not in api_client.session # Session should be cleared

def test_auth_status_logged_in(api_client, teacher_user):
    """ Test auth status check when logged in """
    api_client.login(username='testteacher', password='password123') # Use test client login helper
    url = reverse('authentication:api_auth_status')
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json() == {'isAuthenticated': True, 'username': 'testteacher'}

def test_auth_status_logged_out(api_client):
    """ Test auth status check when logged out """
    url = reverse('authentication:api_auth_status')
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json() == {'isAuthenticated': False}