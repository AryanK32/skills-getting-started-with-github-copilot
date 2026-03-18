"""
Tests for the Mergington High School activities API endpoints.
Uses AAA (Arrange-Act-Assert) pattern for clear, readable tests.
Each test has a fresh, isolated app state via pytest fixtures.
"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client):
        """Arrange: Client ready
        Act: GET /activities
        Assert: Returns 200 with all activities"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0

    def test_get_activities_has_correct_structure(self, client):
        """Arrange: Client ready
        Act: GET /activities
        Assert: Each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_get_activities_participants_are_strings(self, client):
        """Arrange: Client ready
        Act: GET /activities
        Assert: All participants are email strings"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            for participant in activity_data["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant  # Basic email validation


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_successful(self, client):
        """Arrange: Valid activity and email
        Act: POST /signup
        Assert: Returns 200 with success message and participant is added"""
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_adds_participant_to_activity(self, client):
        """Arrange: Valid activity and new email
        Act: POST /signup and GET /activities
        Assert: Participant appears in the activity's participants list"""
        # Signup
        client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        # Verify
        response = client.get("/activities")
        activities = response.json()
        participants = activities["Chess Club"]["participants"]
        assert "newstudent@mergington.edu" in participants

    def test_signup_increments_participant_count(self, client):
        """Arrange: Get initial count, then signup
        Act: POST /signup
        Assert: Participant count increases by 1"""
        # Get initial count
        initial = client.get("/activities").json()
        initial_count = len(initial["Chess Club"]["participants"])
        
        # Signup
        client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "counter@mergington.edu"}
        )
        
        # Verify count increased
        updated = client.get("/activities").json()
        updated_count = len(updated["Chess Club"]["participants"])
        assert updated_count == initial_count + 1

    def test_signup_duplicate_email_returns_400(self, client):
        """Arrange: Student already in activity
        Act: POST /signup with same email twice
        Assert: Second signup returns 400 error"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            "/activities/Tennis%20Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            "/activities/Tennis%20Club/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]

    def test_signup_nonexistent_activity_returns_404(self, client):
        """Arrange: Non-existent activity name
        Act: POST /signup to fake activity
        Assert: Returns 404 error"""
        response = client.post(
            "/activities/Fake%20Activity/signup",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_with_valid_email_formats(self, client):
        """Arrange: Different valid email formats
        Act: POST /signup with various emails
        Assert: All signup successfully"""
        emails = [
            "student123@mergington.edu",
            "j.doe@mergington.edu",
            "a@b.c",
        ]
        
        for email in emails:
            response = client.post(
                "/activities/Art%20Studio/signup",
                params={"email": email}
            )
            assert response.status_code == 200


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint."""

    def test_remove_participant_successful(self, client):
        """Arrange: Activity with participants
        Act: DELETE /participants/{email}
        Assert: Returns 200 and participant is removed"""
        # First, signup to have a participant
        client.post(
            "/activities/Programming%20Class/signup",
            params={"email": "removeme@mergington.edu"}
        )
        
        # Remove the participant
        response = client.delete(
            "/activities/Programming%20Class/participants/removeme@mergington.edu"
        )
        
        assert response.status_code == 200
        assert "Removed" in response.json()["message"]

    def test_remove_participant_decreases_count(self, client):
        """Arrange: Signup a participant, get initial count
        Act: DELETE /participants/{email}
        Assert: Participant count decreases by 1"""
        email = "tobedeleted@mergington.edu"
        
        # Signup
        client.post(
            "/activities/Gym%20Class/signup",
            params={"email": email}
        )
        
        # Get count after signup
        before = client.get("/activities").json()
        before_count = len(before["Gym Class"]["participants"])
        
        # Remove
        client.delete(
            f"/activities/Gym%20Class/participants/{email}"
        )
        
        # Verify count decreased
        after = client.get("/activities").json()
        after_count = len(after["Gym Class"]["participants"])
        assert after_count == before_count - 1

    def test_remove_participant_actually_removes_from_list(self, client):
        """Arrange: Signup a participant
        Act: DELETE /participants/{email}
        Assert: Participant no longer in participants list"""
        email = "verifyremoval@mergington.edu"
        
        # Signup
        client.post(
            "/activities/Music%20Band/signup",
            params={"email": email}
        )
        
        # Remove
        client.delete(
            f"/activities/Music%20Band/participants/{email}"
        )
        
        # Verify removed
        activities = client.get("/activities").json()
        participants = activities["Music Band"]["participants"]
        assert email not in participants

    def test_remove_nonexistent_participant_returns_404(self, client):
        """Arrange: Non-existent participant email
        Act: DELETE /participants/{fake_email}
        Assert: Returns 404 error"""
        response = client.delete(
            "/activities/Debate%20Society/participants/fakestudent@mergington.edu"
        )
        
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]

    def test_remove_from_nonexistent_activity_returns_404(self, client):
        """Arrange: Non-existent activity name
        Act: DELETE from fake activity
        Assert: Returns 404 error"""
        response = client.delete(
            "/activities/Fake%20Activity/participants/test@mergington.edu"
        )
        
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_remove_participant_twice_returns_404(self, client):
        """Arrange: Remove a participant
        Act: Remove the same participant again
        Assert: Second removal returns 404"""
        email = "doubleremove@mergington.edu"
        
        # Signup
        client.post(
            "/activities/Science%20Club/signup",
            params={"email": email}
        )
        
        # First removal should succeed
        response1 = client.delete(
            f"/activities/Science%20Club/participants/{email}"
        )
        assert response1.status_code == 200
        
        # Second removal should fail
        response2 = client.delete(
            f"/activities/Science%20Club/participants/{email}"
        )
        assert response2.status_code == 404


class TestRootEndpoint:
    """Tests for GET / endpoint."""

    def test_root_redirects_to_index(self, client):
        """Arrange: Client ready
        Act: GET /
        Assert: Returns redirect to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestIntegration:
    """Integration tests combining multiple operations."""

    def test_signup_and_remove_workflow(self, client):
        """Arrange: Activity ready
        Act: Signup, verify, remove, verify again
        Assert: Participant added then removed correctly"""
        activity = "Basketball%20Team"
        email = "player@mergington.edu"
        
        # Signup
        assert client.post(f"/activities/{activity}/signup", params={"email": email}).status_code == 200
        
        # Verify signup
        participants = client.get("/activities").json()["Basketball Team"]["participants"]
        assert email in participants
        
        # Remove
        assert client.delete(f"/activities/{activity}/participants/{email}").status_code == 200
        
        # Verify removal
        participants = client.get("/activities").json()["Basketball Team"]["participants"]
        assert email not in participants

    def test_multiple_signups_same_activity(self, client):
        """Arrange: Activity ready
        Act: Multiple different students signup
        Assert: All are added successfully"""
        activity = "Tennis%20Club"
        emails = [f"player{i}@mergington.edu" for i in range(3)]
        
        # Signup multiple
        for email in emails:
            response = client.post(f"/activities/{activity}/signup", params={"email": email})
            assert response.status_code == 200
        
        # Verify all added
        participants = client.get("/activities").json()["Tennis Club"]["participants"]
        for email in emails:
            assert email in participants
