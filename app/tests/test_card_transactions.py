import pytest
from fastapi import status
from decimal import Decimal
from datetime import datetime, timezone

class TestCardTransactions:
    """Test suite for card transaction processing"""
    
    def setup_user_with_card(self, client):
        """Helper to create user, account, and card"""
        # Signup and login
        client.post(
            "/api/auth/signup",
            json={"email": "test_card_txn@example.com", "password": "password123"}
        )
        login_response = client.post(
            "/api/auth/login",
            data={"username": "test_card_txn@example.com", "password": "password123"}
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
        
        # Create account with funds
        account_response = client.post(
            "/api/accounts/",
            headers={"Authorization": f"Bearer {token}"},
            json={"account_type": "checking", "initial_deposit": 1000.00}
        )
        account_id = account_response.json()["id"]
        
        # Create card
        card_response = client.post(
            "/api/cards/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "account_id": account_id,
                "card_type": "debit",
                "cardholder_name": "John Doe",
                "pin": "1234",
                "daily_limit": 500.00
            }
        )
        card_id = card_response.json()["id"]
        
        # Activate card
        client.post(
            f"/api/cards/{card_id}/activate",
            headers={"Authorization": f"Bearer {token}"},
            json={"pin": "1234"}
        )
        
        return token, card_id, account_id
    
    def test_process_card_payment_success(self, client):
        """Test successful card payment"""
        token, card_id, account_id = self.setup_user_with_card(client)
        
        response = client.post(
            f"/api/cards/{card_id}/transactions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "amount": 100.00,
                "merchant_name": "Test Merchant",
                "description": "Groceries"
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["status"] == "completed"
        assert float(data["amount"]) == 100.00
        assert data["merchant_name"] == "Test Merchant"
        
        # Verify account balance updated
        acc_response = client.get(
            f"/api/accounts/{account_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert float(acc_response.json()["balance"]) == 900.00
        
    def test_exceed_daily_limit(self, client):
        """Test transaction exceeding daily limit fails"""
        token, card_id, _ = self.setup_user_with_card(client)
        
        # Limit is 500. Try to spend 600.
        response = client.post(
            f"/api/cards/{card_id}/transactions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "amount": 600.00,
                "merchant_name": "Luxury Store"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "exceed daily limit" in response.json()["detail"].lower()
        
    def test_insufficient_funds(self, client):
        """Test transaction with insufficient funds fails"""
        token, card_id, _ = self.setup_user_with_card(client)
        
        # Account has 1000. Limit is 500. Update limit to allow 2000.
        client.put(
            f"/api/cards/{card_id}/limit",
            headers={"Authorization": f"Bearer {token}"},
            json={"new_limit": 2000.00}
        )
        
        # Try to spend 1500 (more than account balance)
        response = client.post(
            f"/api/cards/{card_id}/transactions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "amount": 1500.00,
                "merchant_name": "Car Dealership"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "insufficient funds" in response.json()["detail"].lower()
        
    def test_inactive_card_transaction(self, client):
        """Test transaction on inactive card fails"""
        # Create new user/card but don't activate it
        client.post(
            "/api/auth/signup",
            json={"email": "inactive@example.com", "password": "password123"}
        )
        login_response = client.post(
            "/api/auth/login",
            data={"username": "inactive@example.com", "password": "password123"}
        )
        token = login_response.json()["access_token"]
        
        # Create holder & account
        client.post(
            "/api/account-holders/",
            headers={"Authorization": f"Bearer {token}"},
            json={"first_name": "Jane", "last_name": "Doe", "date_of_birth": "1990-01-01"}
        )
        acc_resp = client.post(
            "/api/accounts/",
            headers={"Authorization": f"Bearer {token}"},
            json={"account_type": "checking", "initial_deposit": 1000.00}
        )
        account_id = acc_resp.json()["id"]
        
        # Create card (starts inactive)
        card_resp = client.post(
            "/api/cards/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "account_id": account_id,
                "card_type": "debit",
                "cardholder_name": "Jane Doe",
                "pin": "1234"
            }
        )
        card_id = card_resp.json()["id"]
        
        # Try transaction
        response = client.post(
            f"/api/cards/{card_id}/transactions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "amount": 50.00,
                "merchant_name": "Store"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "inactive" in response.json()["detail"].lower()
        
    def test_get_daily_spending(self, client):
        """Test retrieving daily spending"""
        token, card_id, _ = self.setup_user_with_card(client)
        
        # Make a purchase
        client.post(
            f"/api/cards/{card_id}/transactions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "amount": 100.00,
                "merchant_name": "Store 1"
            }
        )
        
        # Check spending
        response = client.get(
            f"/api/cards/{card_id}/daily-spending",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert float(data["spent_today"]) == 100.00
        assert float(data["remaining_limit"]) == 400.00  # 500 - 100
