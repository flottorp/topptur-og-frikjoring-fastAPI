"""
Test Different User Scenarios
Tests simulating different user types accessing the API
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
import os
from dotenv import load_dotenv

load_dotenv()

SUPERUSER_KEY = os.getenv("fastapi_key_superuser")
USER_KEY = os.getenv("fast_api_key_user")

client = TestClient(app)


class TestReadOnlyUser:
    """
    Scenario: Read-only user with user-level API key
    - Can view members
    - Cannot create, update, or delete
    """
    
    def setup_method(self):
        """Setup: User has read-only access"""
        self.headers = {"X-API-Key": USER_KEY}
    
    def test_readonly_user_can_list_members(self):
        """Read-only user can list all members"""
        response = client.get("/api/members/", headers=self.headers)
        assert response.status_code == 200
        assert "members" in response.json()
    
    def test_readonly_user_can_view_member_details(self):
        """Read-only user can view specific member details"""
        response = client.get("/api/members/+4791110001", headers=self.headers)
        # 200 if exists, 404 if not found - both are valid responses
        assert response.status_code in [200, 404]
    
    def test_readonly_user_cannot_create_member(self):
        """Read-only user cannot create new members"""
        response = client.post(
            "/api/members/",
            params={
                "name": "Unauthorized User",
                "email": "unauthorized@test.com",
                "telephone_number": "+4700000000"
            },
            headers=self.headers
        )
        assert response.status_code == 403
        assert "Superuser" in response.json()["detail"]
    
    def test_readonly_user_cannot_sync(self):
        """Read-only user cannot trigger sync operations"""
        response = client.post(
            "/api/members/sync",
            json={"tf_data": [], "ntnui_data": []},
            headers=self.headers
        )
        assert response.status_code == 403
    
    def test_readonly_user_cannot_reset_database(self):
        """Read-only user cannot reset database"""
        response = client.delete("/api/members/reset", headers=self.headers)
        assert response.status_code == 403


class TestAdminUser:
    """
    Scenario: Admin user with superuser-level API key
    - Full access to all operations
    - Can perform sync and maintenance tasks
    """
    
    def setup_method(self):
        """Setup: User has full admin access"""
        self.headers = {"X-API-Key": SUPERUSER_KEY}
    
    def test_admin_can_list_members(self):
        """Admin user can list all members"""
        response = client.get("/api/members/", headers=self.headers)
        assert response.status_code == 200
        assert "members" in response.json()
    
    def test_admin_can_view_member_details(self):
        """Admin user can view specific member details"""
        response = client.get("/api/members/+4791110001", headers=self.headers)
        assert response.status_code in [200, 404]
    
    def test_admin_can_create_member(self):
        """Admin user can create new members"""
        response = client.post(
            "/api/members/",
            params={
                "name": "Admin Created User",
                "email": "admin.created@test.com",
                "telephone_number": "+4788888888",
                "tf_valid": True,
                "ntnui_valid": True
            },
            headers=self.headers
        )
        # 200 for success, 400 for validation error (e.g., duplicate)
        assert response.status_code in [200, 400]
    
    def test_admin_can_sync_members(self):
        """Admin user can trigger sync operations"""
        response = client.post(
            "/api/members/sync",
            json={
                "tf_data": [
                    {
                        "billing": {
                            "first_name": "Test",
                            "last_name": "Admin",
                            "email": "admin@test.com",
                            "phone": "+4777777777"
                        },
                        "date_paid": "2025-01-01T10:00:00"
                    }
                ],
                "ntnui_data": []
            },
            headers=self.headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"
    
    def test_admin_can_reset_database(self):
        """Admin user can reset database"""
        response = client.delete("/api/members/reset", headers=self.headers)
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()


class TestAnonymousUser:
    """
    Scenario: Anonymous user without API key
    - Can only access public endpoints
    - All protected endpoints should be blocked
    """
    
    def test_anonymous_can_access_root(self):
        """Anonymous user can access root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_anonymous_can_check_health(self):
        """Anonymous user can check health status"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_anonymous_cannot_list_members(self):
        """Anonymous user cannot list members"""
        response = client.get("/api/members/")
        assert response.status_code == 401
    
    def test_anonymous_cannot_view_member(self):
        """Anonymous user cannot view member details"""
        response = client.get("/api/members/+4791110001")
        assert response.status_code == 401
    
    def test_anonymous_cannot_create_member(self):
        """Anonymous user cannot create members"""
        response = client.post(
            "/api/members/",
            params={
                "name": "Anonymous",
                "email": "anon@test.com"
            }
        )
        assert response.status_code == 401
    
    def test_anonymous_cannot_sync(self):
        """Anonymous user cannot trigger sync"""
        response = client.post("/api/members/sync", json={})
        assert response.status_code == 401
    
    def test_anonymous_cannot_reset(self):
        """Anonymous user cannot reset database"""
        response = client.delete("/api/members/reset")
        assert response.status_code == 401


class TestMaliciousUser:
    """
    Scenario: Malicious user trying various attack vectors
    - Attempts to bypass authentication
    - Tests edge cases and security boundaries
    """
    
    def test_malicious_user_with_fake_key(self):
        """Malicious user with fabricated API key"""
        fake_keys = [
            "fake-key-12345",
            "admin",
            "superuser",
            "password123",
            "Bearer " + USER_KEY,  # Wrong auth scheme
        ]
        
        for fake_key in fake_keys:
            response = client.get(
                "/api/members/",
                headers={"X-API-Key": fake_key}
            )
            assert response.status_code == 403, f"Fake key '{fake_key}' was accepted!"
    
    def test_malicious_user_with_empty_key(self):
        """Malicious user with empty API key"""
        response = client.get(
            "/api/members/",
            headers={"X-API-Key": ""}
        )
        assert response.status_code in [401, 403]
    
    def test_malicious_user_with_wrong_header_name(self):
        """Malicious user using wrong header name"""
        wrong_headers = [
            {"Authorization": f"Bearer {SUPERUSER_KEY}"},
            {"API-Key": SUPERUSER_KEY},
            {"Api-Key": SUPERUSER_KEY},
            {"ApiKey": SUPERUSER_KEY},
        ]
        
        for headers in wrong_headers:
            response = client.get("/api/members/", headers=headers)
            assert response.status_code == 401
    
    def test_header_case_insensitivity(self):
        """HTTP headers are case-insensitive (correct behavior)"""
        # These should all work because HTTP headers are case-insensitive
        valid_header_variations = [
            {"X-API-Key": SUPERUSER_KEY},
            {"x-api-key": SUPERUSER_KEY},
            {"X-Api-Key": SUPERUSER_KEY},
        ]
        
        for headers in valid_header_variations:
            response = client.get("/api/members/", headers=headers)
            assert response.status_code == 200, f"Headers {headers} should work (HTTP headers are case-insensitive)"
    
    def test_malicious_user_trying_sql_injection_in_key(self):
        """Malicious user attempting SQL injection via API key"""
        malicious_keys = [
            "'; DROP TABLE members; --",
            "1' OR '1'='1",
            "<script>alert('xss')</script>",
        ]
        
        for key in malicious_keys:
            response = client.get(
                "/api/members/",
                headers={"X-API-Key": key}
            )
            assert response.status_code == 403
    
    def test_privilege_escalation_attempt(self):
        """User trying to escalate privileges from user to superuser"""
        # User key trying to perform superuser action
        response = client.delete(
            "/api/members/reset",
            headers={"X-API-Key": USER_KEY}
        )
        assert response.status_code == 403
        assert "Superuser" in response.json()["detail"]


class TestAutomatedSystem:
    """
    Scenario: Automated system (like GitHub Actions)
    - Uses superuser key for scheduled tasks
    - Performs batch operations
    """
    
    def setup_method(self):
        """Setup: Automated system with superuser access"""
        self.headers = {"X-API-Key": SUPERUSER_KEY}
    
    def test_automated_system_can_perform_scheduled_sync(self):
        """Automated system can run scheduled sync"""
        response = client.post(
            "/api/members/sync",
            json={
                "tf_data": [],
                "ntnui_data": []
            },
            headers=self.headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"
    
    def test_automated_system_can_check_member_count(self):
        """Automated system can check member count"""
        response = client.get("/api/members/", headers=self.headers)
        assert response.status_code == 200
        assert "count" in response.json()
    
    def test_automated_system_batch_operations(self):
        """Automated system performs multiple operations in sequence"""
        # First, reset database
        reset_response = client.delete("/api/members/reset", headers=self.headers)
        assert reset_response.status_code == 200
        
        # Then, sync new data
        sync_response = client.post(
            "/api/members/sync",
            json={
                "tf_data": [
                    {
                        "billing": {
                            "first_name": "Batch",
                            "last_name": "User",
                            "email": "batch@test.com",
                            "phone": "+4766666666"
                        },
                        "date_paid": "2025-01-01T00:00:00"
                    }
                ],
                "ntnui_data": []
            },
            headers=self.headers
        )
        assert sync_response.status_code == 200
        
        # Finally, verify the data
        verify_response = client.get("/api/members/", headers=self.headers)
        assert verify_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
