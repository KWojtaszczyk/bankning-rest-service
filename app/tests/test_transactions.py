import pytest
from fastapi import status
from decimal import Decimal
from datetime import datetime, timedelta

class TestTransactions:
    """Test suite for transaction features"""
    
    @pytest.fixture
    def sender_setup(self, client):
        """Setup sender with account and funds"""
        # Signup & Login
        client.post("/api/auth/signup", json={"email": "sender@test.com", "password": "password123"})
        login = client.post("/api/auth/login", data={"username": "sender@test.com", "password": "password123"})
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create Profile
        client.post("/api/account-holders/", headers=headers, 
                   json={"first_name": "Sender", "last_name": "Test", "date_of_birth": "1990-01-01"})
        
        # Create Account with funds
        acc = client.post("/api/accounts/", headers=headers,
                         json={"account_type": "checking", "initial_deposit": 1000.00}).json()
        
        return {"token": token, "headers": headers, "account": acc}

    @pytest.fixture
    def receiver_setup(self, client):
        """Setup receiver with account"""
        # Signup & Login
        client.post("/api/auth/signup", json={"email": "receiver@test.com", "password": "password123"})
        login = client.post("/api/auth/login", data={"username": "receiver@test.com", "password": "password123"})
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create Profile
        client.post("/api/account-holders/", headers=headers, 
                   json={"first_name": "Receiver", "last_name": "Test", "date_of_birth": "1995-01-01"})
        
        # Create Account (empty)
        acc = client.post("/api/accounts/", headers=headers,
                         json={"account_type": "savings", "initial_deposit": 0.00}).json()
        
        return {"token": token, "headers": headers, "account": acc}

    def test_transfer_success(self, client, sender_setup, receiver_setup):
        """Test successful money transfer"""
        response = client.post(
            "/api/transactions/transfer",
            headers=sender_setup["headers"],
            json={
                "from_account_id": sender_setup["account"]["id"],
                "to_account_number": receiver_setup["account"]["account_number"],
                "amount": 100.00,
                "description": "Test transfer"
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["amount"] == "100.00"
        assert data["status"] == "completed"
        
        # Verify balances
        sender_bal = client.get(f"/api/accounts/{sender_setup['account']['id']}/balance", 
                               headers=sender_setup["headers"]).json()
        receiver_bal = client.get(f"/api/accounts/{receiver_setup['account']['id']}/balance", 
                                 headers=receiver_setup["headers"]).json()
        
        assert float(sender_bal["balance"]) == 900.00
        assert float(receiver_bal["balance"]) == 100.00

    def test_transfer_insufficient_funds(self, client, sender_setup, receiver_setup):
        """Test transfer with insufficient funds"""
        response = client.post(
            "/api/transactions/transfer",
            headers=sender_setup["headers"],
            json={
                "from_account_id": sender_setup["account"]["id"],
                "to_account_number": receiver_setup["account"]["account_number"],
                "amount": 2000.00,  # More than balance (1000)
                "description": "Too much"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "insufficient funds" in response.json()["detail"].lower()

    def test_transfer_to_nonexistent_account(self, client, sender_setup):
        """Test transfer to invalid account number"""
        response = client.post(
            "/api/transactions/transfer",
            headers=sender_setup["headers"],
            json={
                "from_account_id": sender_setup["account"]["id"],
                "to_account_number": "INVALID123",
                "amount": 50.00
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST # Or 404 depending on implementation
        # My implementation raises ValueError "Receiver account not found" which maps to 400 in the route

    def test_transfer_unauthorized(self, client, sender_setup, receiver_setup):
        """Test user cannot transfer from account they don't own"""
        # Receiver tries to transfer from Sender's account
        response = client.post(
            "/api/transactions/transfer",
            headers=receiver_setup["headers"],
            json={
                "from_account_id": sender_setup["account"]["id"],
                "to_account_number": receiver_setup["account"]["account_number"],
                "amount": 50.00
            }
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_transaction_history(self, client, sender_setup, receiver_setup):
        """Test retrieving transaction history"""
        # Make a transfer first
        client.post(
            "/api/transactions/transfer",
            headers=sender_setup["headers"],
            json={
                "from_account_id": sender_setup["account"]["id"],
                "to_account_number": receiver_setup["account"]["account_number"],
                "amount": 50.00
            }
        )
        
        # Get history
        response = client.get(
            f"/api/transactions/accounts/{sender_setup['account']['id']}/transactions",
            headers=sender_setup["headers"]
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        # First transaction should be the transfer (or initial deposit if that's logged)
        # Note: Initial deposit is logged as a transaction too!
        # So we expect at least 2 transactions (Deposit + Transfer)
        assert any(t["amount"] == "50.00" for t in data)

    def test_rollback_transaction(self, client, sender_setup, receiver_setup):
        """Test rolling back a transaction"""
        # 1. Make transfer
        transfer = client.post(
            "/api/transactions/transfer",
            headers=sender_setup["headers"],
            json={
                "from_account_id": sender_setup["account"]["id"],
                "to_account_number": receiver_setup["account"]["account_number"],
                "amount": 100.00
            }
        ).json()
        
        # 2. Rollback
        response = client.post(
            f"/api/transactions/transactions/{transfer['id']}/rollback",
            headers=sender_setup["headers"]
        )
        
        assert response.status_code == status.HTTP_200_OK
        reversal = response.json()
        assert reversal["amount"] == "100.00"
        
        # 3. Verify Balances restored
        sender_bal = client.get(f"/api/accounts/{sender_setup['account']['id']}/balance", 
                               headers=sender_setup["headers"]).json()
        assert float(sender_bal["balance"]) == 1000.00

    def test_rollback_unauthorized(self, client, sender_setup, receiver_setup):
        """Test only sender can rollback"""
        # 1. Make transfer
        transfer = client.post(
            "/api/transactions/transfer",
            headers=sender_setup["headers"],
            json={
                "from_account_id": sender_setup["account"]["id"],
                "to_account_number": receiver_setup["account"]["account_number"],
                "amount": 100.00
            }
        ).json()
        
        # 2. Receiver tries to rollback (should fail)
        response = client.post(
            f"/api/transactions/transactions/{transfer['id']}/rollback",
            headers=receiver_setup["headers"]
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
