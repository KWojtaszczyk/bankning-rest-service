#!/bin/bash

# Banking REST Service - Project Initialization Script
# Run this script to set up your project structure

echo "🏦 Initializing Banking REST Service Project..."

# Create project directory
mkdir -p banking-rest-service
cd banking-rest-service

# Initialize git
echo "📝 Setting up Git..."
git init

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/

# Environment
.env
.env.local

# Database
*.db
*.sqlite
*.sqlite3

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.coverage
htmlcov/
.pytest_cache/

# Logs
*.log
EOF

# Create README.md placeholder
cat > README.md << 'EOF'
# Banking REST Service

AI-driven development of a secure banking REST API.

## Setup Instructions

Coming soon...
EOF

# Create project structure
echo "📁 Creating project structure..."
mkdir -p app/{models,routes,services,middleware,tests,schemas}
touch app/__init__.py

# Create main application files
touch app/main.py
touch app/database.py
touch app/config.py

# Create model files
touch app/models/__init__.py
touch app/models/user.py
touch app/models/account_holder.py
touch app/models/account.py
touch app/models/transaction.py
touch app/models/card.py

# Create route files
touch app/routes/__init__.py
touch app/routes/auth.py
touch app/routes/account_holders.py
touch app/routes/accounts.py
touch app/routes/transactions.py
touch app/routes/cards.py
touch app/routes/statements.py

# Create service files
touch app/services/__init__.py
touch app/services/auth_service.py
touch app/services/account_service.py
touch app/services/transaction_service.py

# Create middleware files
touch app/middleware/__init__.py
touch app/middleware/auth.py

# Create schema files (for request/response validation)
touch app/schemas/__init__.py
touch app/schemas/user.py
touch app/schemas/account.py
touch app/schemas/transaction.py

# Create test structure
touch app/tests/__init__.py
touch app/tests/test_auth.py
touch app/tests/test_accounts.py
touch app/tests/test_transactions.py
touch app/tests/conftest.py

# Create requirements.txt
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
pytest==7.4.3
pytest-cov==4.1.0
pytest-asyncio==0.21.1
httpx==0.25.2
EOF

# Create .env.example
cat > .env.example << 'EOF'
# Application
APP_NAME=Banking REST Service
DEBUG=True
API_VERSION=v1

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=sqlite:///./banking.db

# API
API_PREFIX=/api
EOF

# Create initial .env
cp .env.example .env

# Create docs directory
mkdir -p docs
touch docs/SECURITY.md
touch docs/FUTURE_ROADMAP.md
touch docs/AI_USAGE_LOG.md

echo "✅ Project structure created!"
echo ""
echo "Next steps:"
echo "1. cd banking-rest-service"
echo "2. python -m venv venv"
echo "3. source venv/bin/activate  (On Windows: venv\\Scripts\\activate)"
echo "4. pip install -r requirements.txt"
echo ""
echo "🚀 Ready to start development!"