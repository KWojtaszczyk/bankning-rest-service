import pytest
from fastapi import status
from datetime import date

class TestAccountHolders:
    """Test suite for account holder endpoints"""
    
    def setup_user_and_login(self, client):
        """Helper to create user and get token"""
        client.post(
            "/api/auth/signup",
            json={"email": "test@example.com", "password": "password123"}
        )
        login_response = client.post(
            "/api/auth/login",
            data={"username": "test@example.com", "password": "password123"}
        )
        return login_response.json()["access_token"]
    
    def test_create_account_holder_success(self, client):
        """Test successful account holder creation"""
        token = self.setup_user_and_login(client)
        
        response = client.post(
            "/api/account-holders/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1990-01-01",
                "phone_number": "+1234567890",
                "address": "123 Main St",
                "city": "New York",
                "country": "USA",
                "postal_code": "10001"
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["kyc_verified"] is False
    
    def test_create_duplicate_account_holder(self, client):
        """Test creating duplicate account holder fails"""
        token = self.setup_user_and_login(client)
        
        holder_data = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-01"
        }
        
        # Create first time
        client.post(
            "/api/account-holders/",
            headers={"Authorization": f"Bearer {token}"},
            json=holder_data
        )
        
        # Try to create again
        response = client.post(
            "/api/account-holders/",
            headers={"Authorization": f"Bearer {token}"},
            json=holder_data
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already has" in response.json()["detail"].lower()
    
    def test_get_my_account_holder(self, client):
        """Test getting current user's account holder"""
        token = self.setup_user_and_login(client)
        
        # Create account holder
        client.post(
            "/api/account-holders/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1990-01-01"
            }
        )
        
        # Get account holder
        response = client.get(
            "/api/account-holders/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["first_name"] == "John"
    
    def test_get_account_holder_without_profile(self, client):
        """Test getting account holder when none exists"""
        token = self.setup_user_and_login(client)
        
        response = client.get(
            "/api/account-holders/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestAccounts:
    """Test suite for account endpoints"""
    
    def setup_user_with_holder(self, client):
        """Helper to create user, login, and create account holder"""
        # Signup and login
        client.post(
            "/api/auth/signup",
            json={"email": "test@example.com", "password": "password123"}
        )
        login_response = client.post(
            "/api/auth/login",
            data={"username": "test@example.com", "password": "password123"}
        )
        token = login_response.json()["access_token"]
        
        # Create account holder
        client.post(
            "/api/account-holders/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1990-01-01"
            }
        )
        
        return token
    
    def test_create_account_success(self, client):
        """Test successful account creation"""
        token = self.setup_user_with_holder(client)
        
        response = client.post(
            "/api/accounts/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "account_type": "checking",
                "currency": "USD",
                "initial_deposit": 1000.00
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["account_type"] == "checking"
        assert float(data["balance"]) == 1000.00
        assert data["status"] == "active"
        assert len(data["account_number"]) == 12
    
    def test_create_account_without_holder(self, client):
        """Test creating account without account holder profile fails"""
        # Just login, don't create holder
        client.post(
            "/api/auth/signup",
            json={"email": "test@example.com", "password": "password123"}
        )
        login_response = client.post(
            "/api/auth/login",
            data={"username": "test@example.com", "password": "password123"}
        )
        token = login_response.json()["access_token"]
        
        response = client.post(
            "/api/accounts/",
            headers={"Authorization": f"Bearer {token}"},
            json={"account_type": "checking"}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "account holder profile" in response.json()["detail"].lower()
    
    def test_create_multiple_accounts(self, client):
        """Test user can create multiple accounts"""
        token = self.setup_user_with_holder(client)
        
        # Create checking account
        response1 = client.post(
            "/api/accounts/",
            headers={"Authorization": f"Bearer {token}"},
            json={"account_type": "checking", "initial_deposit": 500.00}
        )
        
        # Create savings account
        response2 = client.post(
            "/api/accounts/",
            headers={"Authorization": f"Bearer {token}"},
            json={"account_type": "savings", "initial_deposit": 1500.00}
        )
        
        assert response1.status_code == status.HTTP_201_CREATED
        assert response2.status_code == status.HTTP_201_CREATED
        assert response1.json()["account_number"] != response2.json()["account_number"]
    
    def test_list_my_accounts(self, client):
        """Test listing user's accounts"""
        token = self.setup_user_with_holder(client)
        
        # Create two accounts
        client.post(
            "/api/accounts/",
            headers={"Authorization": f"Bearer {token}"},
            json={"account_type": "checking"}
        )
        client.post(
            "/api/accounts/",
            headers={"Authorization": f"Bearer {token}"},
            json={"account_type": "savings"}
        )
        
        # List accounts
        response = client.get(
            "/api/accounts/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert any(acc["account_type"] == "checking" for acc in data)
        assert any(acc["account_type"] == "savings" for acc in data)
    
    def test_get_account_by_id(self, client):
        """Test getting specific account by ID"""
        token = self.setup_user_with_holder(client)
        
        # Create account
        create_response = client.post(
            "/api/accounts/",
            headers={"Authorization": f"Bearer {token}"},
            json={"account_type": "checking", "initial_deposit": 250.00}
        )
        account_id = create_response.json()["id"]
        
        # Get account
        response = client.get(
            f"/api/accounts/{account_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == account_id
        assert float(data["balance"]) == 250.00
    
    def test_get_account_balance(self, client):
        """Test getting account balance"""
        token = self.setup_user_with_holder(client)
        
        # Create account
        create_response = client.post(
            "/api/accounts/",
            headers={"Authorization": f"Bearer {token}"},
            json={"account_type": "savings", "initial_deposit": 5000.00}
        )
        account_id = create_response.json()["id"]
        
        # Get balance
        response = client.get(
            f"/api/accounts/{account_id}/balance",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert float(data["balance"]) == 5000.00
        assert data["currency"] == "USD"
    
    def test_cannot_access_other_users_account(self, client):
        """Test authorization: cannot access another user's account"""
        # User 1 creates account
        token1 = self.setup_user_with_holder(client)
        create_response = client.post(
            "/api/accounts/",
            headers={"Authorization": f"Bearer {token1}"},
            json={"account_type": "checking"}
        )
        account_id = create_response.json()["id"]
        
        # User 2 tries to access it
        client.post(
            "/api/auth/signup",
            json={"email": "user2@example.com", "password": "password123"}
        )
        login_response = client.post(
            "/api/auth/login",
            data={"username": "user2@example.com", "password": "password123"}
        )
        token2 = login_response.json()["access_token"]
        
        response = client.get(
            f"/api/accounts/{account_id}",
            headers={"Authorization": f"Bearer {token2}"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN