import pytest
from fastapi import status

class TestCards:
    """Test suite for card management endpoints"""
    
    def setup_user_with_account(self, client):
        """Helper to create user, holder, and account"""
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
        
        # Create account
        account_response = client.post(
            "/api/accounts/",
            headers={"Authorization": f"Bearer {token}"},
            json={"account_type": "checking", "initial_deposit": 1000.00}
        )
        account_id = account_response.json()["id"]
        
        return token, account_id
    
    def test_create_card_success(self, client):
        """Test successful card creation"""
        token, account_id = self.setup_user_with_account(client)
        
        response = client.post(
            "/api/cards/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "account_id": account_id,
                "card_type": "debit",
                "cardholder_name": "John Doe",
                "pin": "1234",
                "is_contactless": True,
                "daily_limit": 1000.00
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        # Check full card number is provided (only on creation)
        assert "card_number_full" in data
        assert len(data["card_number_full"].replace(" ", "")) == 16
        
        # Check CVV is provided (only on creation)
        assert "cvv" in data
        assert len(data["cvv"]) == 3
        
        # Check masked number
        assert "card_number_masked" in data
        assert data["card_number_masked"].startswith("**** **** ****")
        
        # Check card starts inactive
        assert data["status"] == "inactive"
        assert data["card_type"] == "debit"
    
    def test_create_virtual_card(self, client):
        """Test creating a virtual card"""
        token, account_id = self.setup_user_with_account(client)
        
        response = client.post(
            "/api/cards/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "account_id": account_id,
                "card_type": "virtual",
                "cardholder_name": "John Doe",
                "pin": "5678"
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["card_type"] == "virtual"
    
    def test_create_card_without_account_holder(self, client):
        """Test creating card without account holder profile fails"""
        # Just login, no holder/account
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
            "/api/cards/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "account_id": 999,
                "card_type": "debit",
                "cardholder_name": "John Doe",
                "pin": "1234"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_list_my_cards(self, client):
        """Test listing user's cards"""
        token, account_id = self.setup_user_with_account(client)
        
        # Create two cards
        client.post(
            "/api/cards/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "account_id": account_id,
                "card_type": "debit",
                "cardholder_name": "John Doe",
                "pin": "1234"
            }
        )
        client.post(
            "/api/cards/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "account_id": account_id,
                "card_type": "virtual",
                "cardholder_name": "John Doe",
                "pin": "5678"
            }
        )
        
        # List cards
        response = client.get(
            "/api/cards/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        
        # Check that card numbers are masked in list
        for card in data:
            assert card["card_number_masked"].startswith("**** **** ****")
            assert "card_number_full" not in card  # Full number not in list
            assert "cvv" not in card  # CVV not in list
    
    def test_get_card_details(self, client):
        """Test getting card details by ID"""
        token, account_id = self.setup_user_with_account(client)
        
        # Create card
        create_response = client.post(
            "/api/cards/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "account_id": account_id,
                "card_type": "debit",
                "cardholder_name": "John Doe",
                "pin": "1234"
            }
        )
        card_id = create_response.json()["id"]
        
        # Get card details
        response = client.get(
            f"/api/cards/{card_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Card number should be masked (not full)
        assert data["card_number_masked"].startswith("**** **** ****")
        assert "card_number_full" not in data
        assert "cvv" not in data  # CVV never shown again
    
    def test_activate_card_success(self, client):
        """Test successful card activation"""
        token, account_id = self.setup_user_with_account(client)
        
        # Create card
        create_response = client.post(
            "/api/cards/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "account_id": account_id,
                "card_type": "debit",
                "cardholder_name": "John Doe",
                "pin": "1234"
            }
        )
        card_id = create_response.json()["id"]
        
        # Activate card
        response = client.post(
            f"/api/cards/{card_id}/activate",
            headers={"Authorization": f"Bearer {token}"},
            json={"pin": "1234"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "active"
        assert data["activated_at"] is not None
    
    def test_activate_card_wrong_pin(self, client):
        """Test card activation with wrong PIN fails"""
        token, account_id = self.setup_user_with_account(client)
        
        # Create card with PIN 1234
        create_response = client.post(
            "/api/cards/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "account_id": account_id,
                "card_type": "debit",
                "cardholder_name": "John Doe",
                "pin": "1234"
            }
        )
        card_id = create_response.json()["id"]
        
        # Try to activate with wrong PIN
        response = client.post(
            f"/api/cards/{card_id}/activate",
            headers={"Authorization": f"Bearer {token}"},
            json={"pin": "9999"}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid pin" in response.json()["detail"].lower()
    
    def test_deactivate_card(self, client):
        """Test card deactivation"""
        token, account_id = self.setup_user_with_account(client)
        
        # Create and activate card
        create_response = client.post(
            "/api/cards/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "account_id": account_id,
                "card_type": "debit",
                "cardholder_name": "John Doe",
                "pin": "1234"
            }
        )
        card_id = create_response.json()["id"]
        
        client.post(
            f"/api/cards/{card_id}/activate",
            headers={"Authorization": f"Bearer {token}"},
            json={"pin": "1234"}
        )
        
        # Deactivate card
        response = client.post(
            f"/api/cards/{card_id}/deactivate",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "blocked"
    
    def test_update_card_limit(self, client):
        """Test updating card daily limit"""
        token, account_id = self.setup_user_with_account(client)
        
        # Create card
        create_response = client.post(
            "/api/cards/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "account_id": account_id,
                "card_type": "debit",
                "cardholder_name": "John Doe",
                "pin": "1234",
                "daily_limit": 1000.00
            }
        )
        card_id = create_response.json()["id"]
        
        # Update limit
        response = client.put(
            f"/api/cards/{card_id}/limit",
            headers={"Authorization": f"Bearer {token}"},
            json={"new_limit": 2000.00}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert float(data["daily_limit"]) == 2000.00
    
    def test_cannot_access_other_users_card(self, client):
        """Test authorization: cannot access another user's card"""
        # User 1 creates card
        token1, account_id1 = self.setup_user_with_account(client)
        create_response = client.post(
            "/api/cards/",
            headers={"Authorization": f"Bearer {token1}"},
            json={
                "account_id": account_id1,
                "card_type": "debit",
                "cardholder_name": "John Doe",
                "pin": "1234"
            }
        )
        card_id = create_response.json()["id"]
        
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
            f"/api/cards/{card_id}",
            headers={"Authorization": f"Bearer {token2}"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_card_number_masking(self, client):
        """Test that card numbers are properly masked"""
        token, account_id = self.setup_user_with_account(client)
        
        # Create card
        create_response = client.post(
            "/api/cards/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "account_id": account_id,
                "card_type": "debit",
                "cardholder_name": "John Doe",
                "pin": "1234"
            }
        )
        
        full_number = create_response.json()["card_number_full"]
        masked_number = create_response.json()["card_number_masked"]
        
        # Check last 4 digits match
        last_four = full_number.replace(" ", "")[-4:]
        assert masked_number.endswith(last_four)
        
        # Check rest is masked
        assert masked_number.startswith("**** **** ****")