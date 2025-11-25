import pytest
from fastapi import status


class TestAuthentication:
    """Test suite for authentication endpoints"""

    def test_signup_success(self, client):
        """Test successful user signup"""
        response = client.post(
            "/api/auth/signup",
            json={
                "email": "test@example.com",
                "password": "securepassword123"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "id" in data
        assert data["is_active"] is True
        assert "hashed_password" not in data  # Should not return password

    def test_signup_duplicate_email(self, client):
        """Test signup with duplicate email"""
        # Create first user
        client.post(
            "/api/auth/signup",
            json={
                "email": "test@example.com",
                "password": "password123"
            }
        )

        # Try to create duplicate
        response = client.post(
            "/api/auth/signup",
            json={
                "email": "test@example.com",
                "password": "differentpassword"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"].lower()

    def test_signup_invalid_email(self, client):
        """Test signup with invalid email"""
        response = client.post(
            "/api/auth/signup",
            json={
                "email": "not-an-email",
                "password": "password123"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_signup_short_password(self, client):
        """Test signup with password too short"""
        response = client.post(
            "/api/auth/signup",
            json={
                "email": "test@example.com",
                "password": "short"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_success(self, client):
        """Test successful login"""
        # Create user
        client.post(
            "/api/auth/signup",
            json={
                "email": "test@example.com",
                "password": "securepassword123"
            }
        )

        # Login
        response = client.post(
            "/api/auth/login",
            data={
                "username": "test@example.com",  # OAuth2 uses 'username'
                "password": "securepassword123"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        """Test login with incorrect password"""
        # Create user
        client.post(
            "/api/auth/signup",
            json={
                "email": "test@example.com",
                "password": "correctpassword"
            }
        )

        # Try wrong password
        response = client.post(
            "/api/auth/login",
            data={
                "username": "test@example.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent email"""
        response = client.post(
            "/api/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user(self, client):
        """Test getting current user info with valid token"""
        # Create and login
        client.post(
            "/api/auth/signup",
            json={
                "email": "test@example.com",
                "password": "password123"
            }
        )
        login_response = client.post(
            "/api/auth/login",
            data={
                "username": "test@example.com",
                "password": "password123"
            }
        )
        token = login_response.json()["access_token"]

        # Get user info
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "test@example.com"

    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token"""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_no_token(self, client):
        """Test getting current user without token"""
        response = client.get("/api/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout(self, client):
        """Test logout endpoint"""
        # Create and login
        client.post(
            "/api/auth/signup",
            json={
                "email": "test@example.com",
                "password": "password123"
            }
        )
        login_response = client.post(
            "/api/auth/login",
            data={
                "username": "test@example.com",
                "password": "password123"
            }
        )
        token = login_response.json()["access_token"]

        # Logout
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert "logout" in response.json()["message"].lower()


class TestPasswordSecurity:
    """Test password hashing and security"""

    def test_password_not_returned(self, client):
        """Ensure password is never returned in responses"""
        response = client.post(
            "/api/auth/signup",
            json={
                "email": "test@example.com",
                "password": "securepassword123"
            }
        )
        data = response.json()
        assert "password" not in data
        assert "hashed_password" not in data

    def test_password_hashed_in_database(self, client):
        """Verify passwords are hashed in database"""
        from app.database import SessionLocal
        from app.models.user import User

        # Create user
        client.post(
            "/api/auth/signup",
            json={
                "email": "test@example.com",
                "password": "plainpassword"
            }
        )

        # Check database
        db = SessionLocal()
        user = db.query(User).filter(User.email == "test@example.com").first()
        assert user.hashed_password != "plainpassword"
        assert user.hashed_password.startswith("$2b$")  # bcrypt hash format
        db.close()