# Banking REST Service

AI-driven development of a secure banking REST API with authentication, accounts, transactions, and card management.

## 🚀 Features

- ✅ **User Authentication** - JWT-based authentication with bcrypt password hashing
- ✅ **Account Management** - Support for checking, savings, and business accounts
- ✅ **Transaction System** - Transfers, deposits, withdrawals with ACID compliance
- ✅ **Card Management** - Debit, credit, and virtual card support
- ✅ **KYC Support** - Account holder verification and identification
- ✅ **Secure API** - OAuth2 password flow, token-based authorization
- ✅ **Auto-generated Docs** - Interactive API documentation with Swagger UI

## 📋 Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git

## 🛠️ Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd banking-rest-service
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Copy the example file
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac
```

Edit `.env` and set your secret key:

```env
SECRET_KEY=your-super-secret-key-here-min-32-characters
DATABASE_URL=sqlite:///./banking.db
DEBUG=True
ACCESS_TOKEN_EXPIRE_MINUTES=30
API_PREFIX=/api
```

**⚠️ Important:** Generate a strong SECRET_KEY for production:

```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 5. Initialize Database

The database will be created automatically on first run. To manually initialize:

```bash
python -c "from app.database import engine, Base; from app.models import *; Base.metadata.create_all(bind=engine)"
```

### 6. Run the Application

```bash
# Using the run script
python run.py

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

### 7. Access API Documentation

- **Swagger UI:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc
- **Health Check:** http://localhost:8000/health

## 📚 API Endpoints

### Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/signup` | Create new user account | No |
| POST | `/api/auth/login` | Login and get JWT token | No |
| GET | `/api/auth/me` | Get current user info | Yes |
| POST | `/api/auth/logout` | Logout (client-side token discard) | Yes |

### Account Holders

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/account-holders` | Create account holder profile | Yes |
| GET | `/api/account-holders/{id}` | Get account holder details | Yes |

### Accounts

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/accounts` | Create new account | Yes |
| GET | `/api/accounts` | List user's accounts | Yes |
| GET | `/api/accounts/{id}` | Get account details | Yes |
| GET | `/api/accounts/{id}/balance` | Get account balance | Yes |

### Transactions

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/transactions/transfer` | Transfer money between accounts | Yes |
| GET | `/api/transactions` | Get transaction history | Yes |
| GET | `/api/accounts/{id}/transactions` | Get account transactions | Yes |

### Cards

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/cards` | Create new card | Yes |
| GET | `/api/cards/{id}` | Get card details | Yes |
| PUT | `/api/cards/{id}/activate` | Activate card | Yes |
| PUT | `/api/cards/{id}/deactivate` | Deactivate card | Yes |

### Statements

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/statements/{account_id}` | Generate account statement | Yes |

## 🔐 Security

This application implements several security best practices:

- **Password Hashing:** SHA256 + bcrypt for secure password storage
- **JWT Tokens:** Secure token-based authentication with expiration
- **Input Validation:** Pydantic schemas for all API inputs
- **SQL Injection Prevention:** SQLAlchemy ORM with parameterized queries
- **Environment Variables:** Sensitive data stored in .env file
- **Authorization:** Users can only access their own data

For detailed security information, see [SECURITY.md](docs/SECURITY.md)

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_auth.py -v
```

## 📖 Documentation

- **[SECURITY.md](docs/SECURITY.md)** - Security practices and guidelines
- **[FUTURE_ROADMAP.md](docs/FUTURE_ROADMAP.md)** - Planned features and enhancements
- **[AI_USAGE_LOG.md](docs/AI_USAGE_LOG.md)** - AI assistance documentation
- **[banking_service_roadmap.md](docs/banking_service_roadmap.md)** - Development roadmap

## 🏗️ Project Structure

```
banking-rest-service/
├── app/
│   ├── models/          # SQLAlchemy database models
│   ├── routes/          # API route handlers
│   ├── schemas/         # Pydantic validation schemas
│   ├── services/        # Business logic services
│   ├── middleware/      # Authentication middleware
│   ├── tests/           # Unit and integration tests
│   ├── main.py          # FastAPI application
│   ├── database.py      # Database configuration
│   └── config.py        # Application settings
├── docs/                # Documentation files
├── .env                 # Environment variables (not in git)
├── .env.example         # Environment template
├── requirements.txt     # Python dependencies
└── run.py              # Application entry point
```

## 🔧 Technology Stack

- **Framework:** FastAPI 0.104.1
- **Database:** SQLite with SQLAlchemy 2.0.23
- **Authentication:** JWT (python-jose) + OAuth2
- **Password Hashing:** bcrypt (passlib)
- **Validation:** Pydantic 2.5.0
- **Testing:** pytest, pytest-cov, httpx
- **Server:** Uvicorn

## 🚀 Deployment

### Production Checklist

Before deploying to production:

- [ ] Set strong `SECRET_KEY` (min 32 random characters)
- [ ] Set `DEBUG=False`
- [ ] Configure production database (PostgreSQL recommended)
- [ ] Set up HTTPS/TLS
- [ ] Configure CORS with specific origins
- [ ] Implement rate limiting
- [ ] Set up monitoring and logging
- [ ] Enable database backups
- [ ] Review security documentation

See [SECURITY.md](docs/SECURITY.md) for complete production checklist.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Built with assistance from Claude AI (Anthropic)
- FastAPI framework by Sebastián Ramírez
- SQLAlchemy ORM

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Version:** 1.0  
**Status:** Development  
**Last Updated:** 2025-11-26
