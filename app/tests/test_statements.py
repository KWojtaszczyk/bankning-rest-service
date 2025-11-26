import pytest
from fastapi import status
from datetime import date, timedelta
import os

class TestStatements:
    """Test suite for statement generation endpoints"""
    
    def setup_user_with_account(self, client):
        """Helper to create user, holder, and account"""
        # Signup and login
        client.post(
            "/api/auth/signup",
            json={"email": "test_stmt@example.com", "password": "password123"}
        )
        login_response = client.post(
            "/api/auth/login",
            data={"username": "test_stmt@example.com", "password": "password123"}
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
    
    def test_generate_json_statement(self, client):
        """Test generating a JSON statement"""
        token, account_id = self.setup_user_with_account(client)
        
        # Generate statement
        today = date.today()
        start_date = today - timedelta(days=30)
        
        response = client.post(
            f"/api/accounts/{account_id}/statements",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "period_start": str(start_date),
                "period_end": str(today),
                "format": "json"
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["format"] == "json"
        assert data["file_path"].endswith(".json")
        assert os.path.exists(data["file_path"])
        
        # Clean up
        if os.path.exists(data["file_path"]):
            os.remove(data["file_path"])
            
    def test_generate_pdf_statement(self, client):
        """Test generating a PDF statement"""
        token, account_id = self.setup_user_with_account(client)
        
        # Generate statement
        today = date.today()
        start_date = today - timedelta(days=30)
        
        response = client.post(
            f"/api/accounts/{account_id}/statements",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "period_start": str(start_date),
                "period_end": str(today),
                "format": "pdf"
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["format"] == "pdf"
        assert data["file_path"].endswith(".pdf")
        assert os.path.exists(data["file_path"])
        
        # Clean up
        if os.path.exists(data["file_path"]):
            os.remove(data["file_path"])
            
    def test_list_statements(self, client):
        """Test listing statements"""
        token, account_id = self.setup_user_with_account(client)
        
        # Generate two statements
        today = date.today()
        start_date = today - timedelta(days=30)
        
        client.post(
            f"/api/accounts/{account_id}/statements",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "period_start": str(start_date),
                "period_end": str(today),
                "format": "json"
            }
        )
        
        client.post(
            f"/api/accounts/{account_id}/statements",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "period_start": str(start_date),
                "period_end": str(today),
                "format": "pdf"
            }
        )
        
        # List statements
        response = client.get(
            f"/api/accounts/{account_id}/statements",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        
    def test_download_statement(self, client):
        """Test downloading a statement"""
        token, account_id = self.setup_user_with_account(client)
        
        # Generate statement
        today = date.today()
        start_date = today - timedelta(days=30)
        
        create_response = client.post(
            f"/api/accounts/{account_id}/statements",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "period_start": str(start_date),
                "period_end": str(today),
                "format": "json"
            }
        )
        statement_id = create_response.json()["id"]
        file_path = create_response.json()["file_path"]
        
        # Download statement
        response = client.get(
            f"/api/statements/{statement_id}/download",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/json"
        
        # Clean up
        if os.path.exists(file_path):
            os.remove(file_path)
