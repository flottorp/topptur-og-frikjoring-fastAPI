"""
Test API Key Authentication
Tests for user and superuser API key authentication levels
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API keys from environment
SUPERUSER_KEY = os.getenv("fastapi_key_superuser")
USER_KEY = os.getenv("fast_api_key_user")
INVALID_KEY = "invalid-key-12345"

client = TestClient(app)


class TestPublicEndpoints:
    """Test endpoints that don't require API key"""
    
    def test_root_endpoint_no_key(self):
        """Root endpoint should work without API key"""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
    
    def test_health_endpoint_no_key(self):
        """Health endpoint should work without API key"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestMissingAPIKey:
    """Test endpoints without API key (should fail)"""
    
    def test_get_members_no_key(self):
        """GET /api/members/ should fail without API key"""
        response = client.get("/api/members/")
        assert response.status_code == 401
        assert "Missing API Key" in response.json()["detail"]
    
    def test_get_member_by_id_no_key(self):
        """GET /api/members/{id} should fail without API key"""
        response = client.get("/api/members/+4712345678")
        assert response.status_code == 401
        assert "Missing API Key" in response.json()["detail"]
    
    def test_sync_members_no_key(self):
        """POST /api/members/sync should fail without API key"""
        response = client.post("/api/members/sync", json={})
        assert response.status_code == 401
        assert "Missing API Key" in response.json()["detail"]
    
    def test_reset_database_no_key(self):
        """DELETE /api/members/reset should fail without API key"""
        response = client.delete("/api/members/reset")
        assert response.status_code == 401
        assert "Missing API Key" in response.json()["detail"]


class TestInvalidAPIKey:
    """Test endpoints with invalid API key (should fail)"""
    
    def test_get_members_invalid_key(self):
        """GET /api/members/ should fail with invalid key"""
        response = client.get(
            "/api/members/",
            headers={"X-API-Key": INVALID_KEY}
        )
        assert response.status_code == 403
        assert "Invalid API Key" in response.json()["detail"]
    
    def test_sync_members_invalid_key(self):
        """POST /api/members/sync should fail with invalid key"""
        response = client.post(
            "/api/members/sync",
            json={},
            headers={"X-API-Key": INVALID_KEY}
        )
        assert response.status_code == 403
        assert "Invalid API Key" in response.json()["detail"]


class TestUserAPIKey:
    """Test endpoints with user-level API key"""
    
    def test_get_members_with_user_key(self):
        """GET /api/members/ should work with user key"""
        response = client.get(
            "/api/members/",
            headers={"X-API-Key": USER_KEY}
        )
        assert response.status_code == 200
        assert "members" in response.json()
        assert "count" in response.json()
    
    def test_get_member_by_id_with_user_key(self):
        """GET /api/members/{id} should work with user key (even if not found)"""
        response = client.get(
            "/api/members/+4712345678",
            headers={"X-API-Key": USER_KEY}
        )
        # Should be 404 (not found) or 200 (found), but not 401/403
        assert response.status_code in [200, 404]
    
    def test_create_member_with_user_key_fails(self):
        """POST /api/members/ should fail with user key (requires superuser)"""
        response = client.post(
            "/api/members/",
            params={
                "name": "Test User",
                "email": "test@example.com",
                "telephone_number": "+4712345678"
            },
            headers={"X-API-Key": USER_KEY}
        )
        assert response.status_code == 403
        assert "Superuser access required" in response.json()["detail"]
    
    def test_sync_members_with_user_key_fails(self):
        """POST /api/members/sync should fail with user key"""
        response = client.post(
            "/api/members/sync",
            json={"tf_data": [], "ntnui_data": []},
            headers={"X-API-Key": USER_KEY}
        )
        assert response.status_code == 403
        assert "Superuser access required" in response.json()["detail"]
    
    def test_reset_database_with_user_key_fails(self):
        """DELETE /api/members/reset should fail with user key"""
        response = client.delete(
            "/api/members/reset",
            headers={"X-API-Key": USER_KEY}
        )
        assert response.status_code == 403
        assert "Superuser access required" in response.json()["detail"]


class TestSuperuserAPIKey:
    """Test endpoints with superuser-level API key"""
    
    def test_get_members_with_superuser_key(self):
        """GET /api/members/ should work with superuser key"""
        response = client.get(
            "/api/members/",
            headers={"X-API-Key": SUPERUSER_KEY}
        )
        assert response.status_code == 200
        assert "members" in response.json()
        assert "count" in response.json()
    
    def test_get_member_by_id_with_superuser_key(self):
        """GET /api/members/{id} should work with superuser key"""
        response = client.get(
            "/api/members/+4712345678",
            headers={"X-API-Key": SUPERUSER_KEY}
        )
        # Should be 404 (not found) or 200 (found), but not 401/403
        assert response.status_code in [200, 404]
    
    def test_create_member_with_superuser_key(self):
        """POST /api/members/ should work with superuser key"""
        response = client.post(
            "/api/members/",
            params={
                "name": "Test Superuser",
                "email": "supertest@example.com",
                "telephone_number": "+4799999999",
                "tf_valid": True,
                "ntnui_valid": False
            },
            headers={"X-API-Key": SUPERUSER_KEY}
        )
        # Should be 200 (created) or 400 (validation error), but not 401/403
        assert response.status_code in [200, 400]
    
    def test_sync_members_with_superuser_key(self):
        """POST /api/members/sync should work with superuser key"""
        response = client.post(
            "/api/members/sync",
            json={"tf_data": [], "ntnui_data": []},
            headers={"X-API-Key": SUPERUSER_KEY}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"
    
    def test_reset_database_with_superuser_key(self):
        """DELETE /api/members/reset should work with superuser key"""
        response = client.delete(
            "/api/members/reset",
            headers={"X-API-Key": SUPERUSER_KEY}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"


class TestAPIKeyComparison:
    """Compare behavior between user and superuser keys"""
    
    def test_both_keys_work_for_read_operations(self):
        """Both user and superuser keys should work for GET requests"""
        # User key
        user_response = client.get(
            "/api/members/",
            headers={"X-API-Key": USER_KEY}
        )
        
        # Superuser key
        superuser_response = client.get(
            "/api/members/",
            headers={"X-API-Key": SUPERUSER_KEY}
        )
        
        assert user_response.status_code == 200
        assert superuser_response.status_code == 200
        assert user_response.json() == superuser_response.json()
    
    def test_only_superuser_key_works_for_write_operations(self):
        """Only superuser key should work for POST/DELETE requests"""
        sync_data = {"tf_data": [], "ntnui_data": []}
        
        # User key should fail
        user_response = client.post(
            "/api/members/sync",
            json=sync_data,
            headers={"X-API-Key": USER_KEY}
        )
        
        # Superuser key should succeed
        superuser_response = client.post(
            "/api/members/sync",
            json=sync_data,
            headers={"X-API-Key": SUPERUSER_KEY}
        )
        
        assert user_response.status_code == 403
        assert superuser_response.status_code == 200
    
    def test_key_case_sensitivity(self):
        """API keys should be case-sensitive"""
        wrong_case_key = SUPERUSER_KEY.swapcase()
        
        response = client.get(
            "/api/members/",
            headers={"X-API-Key": wrong_case_key}
        )
        
        assert response.status_code == 403


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
