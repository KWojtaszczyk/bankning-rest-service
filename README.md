# Banking REST Service

## 🛠️ Setup Instructions

### 1. Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- Git

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd banking-rest-service

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the project root:

```bash
# Copy example file
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac
```

Edit `.env` with your settings:
```env
SECRET_KEY=your-super-secret-key-here-min-32-characters
DATABASE_URL=sqlite:///./banking.db
DEBUG=True
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 4. Database Initialization

The database is created automatically on first run. To manually initialize:
```bash
python -c "from app.database import engine, Base; from app.models import *; Base.metadata.create_all(bind=engine)"
```

### 5. Running the Application

```bash
# Using the run script
python run.py

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

---

## 📚 API Documentation

### Interactive Documentation
- **Swagger UI:** [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- **ReDoc:** [http://localhost:8000/api/redoc](http://localhost:8000/api/redoc)

### Core Endpoints

#### Authentication
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/auth/signup` | Register new user | No |
| POST | `/api/auth/login` | Login (get JWT token) | No |
| GET | `/api/auth/me` | Get current user profile | Yes |
| POST | `/api/auth/logout` | Logout | Yes |

#### Accounts
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/accounts` | Create new bank account | Yes |
| GET | `/api/accounts` | List all accounts | Yes |
| GET | `/api/accounts/{id}` | Get account details | Yes |
| GET | `/api/accounts/{id}/balance` | Check balance | Yes |

#### Transactions
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/transactions/transfer` | Transfer funds | Yes |
| GET | `/api/transactions` | Transaction history | Yes |
| GET | `/api/accounts/{id}/transactions` | Account transactions | Yes |

#### Cards
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/cards` | Issue new card | Yes |
| GET | `/api/cards/{id}` | Get card details | Yes |
| PUT | `/api/cards/{id}/activate` | Activate card | Yes |
| POST | `/api/cards/{id}/transactions` | Process card payment | Yes |
| GET | `/api/cards/{id}/daily-spending` | Check daily spending | Yes |

#### Statements
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/accounts/{id}/statements` | Generate statement (PDF/JSON) | Yes |
| GET | `/api/accounts/{id}/statements` | List generated statements | Yes |
| GET | `/api/statements/{id}/download` | Download statement file | Yes |

For detailed request/response schemas, please refer to the Swagger UI.
