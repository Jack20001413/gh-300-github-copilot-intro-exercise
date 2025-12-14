"""
Test suite for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities
from src import auth


@pytest.fixture
def client():
    """Create a test client for the FastAPI application"""
    return TestClient(app)


def create_test_session(client, email="testuser@mergington.edu", name="Test User"):
    """Helper function to create an authenticated session for testing"""
    user = {
        "email": email,
        "name": name,
        "id": "test123",
        "avatar_url": None
    }
    # Create a session token
    session_token = "test-session-token"
    auth.sessions[session_token] = {
        "user": user,
        "expires": auth.datetime.utcnow() + auth.timedelta(hours=1)
    }
    # Set the cookie on the client
    client.cookies.set("session_token", session_token)
    return user


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Basketball": {
            "description": "Competitive basketball team and practice sessions",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["james@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Tennis training and friendly matches",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:00 PM",
            "max_participants": 10,
            "participants": ["sarah@mergington.edu"]
        }
    })
    # Clear auth sessions
    auth.sessions.clear()
    auth.refresh_tokens.clear()


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static(self, client):
        """Test that root redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the GET /activities endpoint"""

    def test_get_all_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Basketball" in data
        assert "Tennis Club" in data

    def test_activities_structure(self, client):
        """Test that activities have correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        create_test_session(client, email="newstudent@mergington.edu")
        response = client.post(
            "/activities/Chess%20Club/signup"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]

    def test_signup_nonexistent_activity(self, client):
        """Test signup for an activity that doesn't exist"""
        create_test_session(client, email="student@mergington.edu")
        response = client.post(
            "/activities/Nonexistent%20Club/signup"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_signup_already_registered(self, client):
        """Test signup when student is already registered"""
        create_test_session(client, email="michael@mergington.edu")
        response = client.post(
            "/activities/Chess%20Club/signup"
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Student already signed up for this activity"
    
    def test_signup_requires_auth(self, client):
        """Test that signup requires authentication"""
        response = client.post(
            "/activities/Chess%20Club/signup"
        )
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Authentication required"

    def test_signup_multiple_students(self, client):
        """Test multiple students can sign up for same activity"""
        # First student
        create_test_session(client, email="student1@mergington.edu")
        response1 = client.post(
            "/activities/Basketball/signup"
        )
        assert response1.status_code == 200
        
        # Second student - need new session
        auth.sessions.clear()
        client.cookies.clear()
        create_test_session(client, email="student2@mergington.edu")
        response2 = client.post(
            "/activities/Basketball/signup"
        )
        assert response2.status_code == 200
        
        # Verify both were added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        participants = activities_data["Basketball"]["participants"]
        assert "student1@mergington.edu" in participants
        assert "student2@mergington.edu" in participants


class TestUnregisterFromActivity:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        create_test_session(client, email="michael@mergington.edu")
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]

    def test_unregister_nonexistent_activity(self, client):
        """Test unregister from an activity that doesn't exist"""
        create_test_session(client, email="student@mergington.edu")
        response = client.delete(
            "/activities/Nonexistent%20Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_unregister_not_registered(self, client):
        """Test unregister when student is not registered"""
        create_test_session(client, email="notregistered@mergington.edu")
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Student is not signed up for this activity"
    
    def test_unregister_requires_auth(self, client):
        """Test that unregister requires authentication"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Authentication required"

    def test_unregister_then_signup_again(self, client):
        """Test that student can sign up again after unregistering"""
        create_test_session(client, email="james@mergington.edu")
        # Unregister
        response1 = client.delete(
            "/activities/Basketball/unregister?email=james@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Sign up again
        response2 = client.post(
            "/activities/Basketball/signup"
        )
        assert response2.status_code == 200
        
        # Verify participant is back
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "james@mergington.edu" in activities_data["Basketball"]["participants"]


class TestIntegrationScenarios:
    """Integration tests for complete user workflows"""

    def test_complete_signup_workflow(self, client):
        """Test a complete signup and unregister workflow"""
        email = "testuser@mergington.edu"
        activity = "Tennis Club"
        
        create_test_session(client, email=email)
        
        # Get initial participant count
        initial_response = client.get("/activities")
        initial_data = initial_response.json()
        initial_count = len(initial_data[activity]["participants"])
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity.replace(' ', '%20')}/signup"
        )
        assert signup_response.status_code == 200
        
        # Verify count increased
        after_signup = client.get("/activities")
        after_signup_data = after_signup.json()
        assert len(after_signup_data[activity]["participants"]) == initial_count + 1
        assert email in after_signup_data[activity]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity.replace(' ', '%20')}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify count decreased
        after_unregister = client.get("/activities")
        after_unregister_data = after_unregister.json()
        assert len(after_unregister_data[activity]["participants"]) == initial_count
        assert email not in after_unregister_data[activity]["participants"]

    def test_multiple_activities_signup(self, client):
        """Test signing up for multiple activities"""
        email = "multitasker@mergington.edu"
        
        create_test_session(client, email=email)
        
        # Sign up for multiple activities
        response1 = client.post(f"/activities/Chess%20Club/signup")
        assert response1.status_code == 200
        
        response2 = client.post(f"/activities/Basketball/signup")
        assert response2.status_code == 200
        
        response3 = client.post(f"/activities/Tennis%20Club/signup")
        assert response3.status_code == 200
        
        # Verify participant is in all activities
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data["Chess Club"]["participants"]
        assert email in activities_data["Basketball"]["participants"]
        assert email in activities_data["Tennis Club"]["participants"]


class TestOAuthEndpoints:
    """Tests for OAuth authentication endpoints"""
    
    def test_auth_user_without_session(self, client):
        """Test getting current user without session returns 401"""
        response = client.get("/auth/user")
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Not authenticated"
    
    def test_auth_user_with_session(self, client):
        """Test getting current user with valid session"""
        user = create_test_session(client, email="test@example.com", name="Test User")
        response = client.get("/auth/user")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
    
    def test_logout(self, client):
        """Test logout endpoint"""
        create_test_session(client)
        response = client.post("/auth/logout")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Logged out successfully"
        
        # Verify session is cleared
        user_response = client.get("/auth/user")
        assert user_response.status_code == 401
