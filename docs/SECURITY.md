# Security Documentation

## Overview
This document outlines the security measures, best practices, and considerations implemented in the Banking REST Service API.

## Authentication & Authorization

### Authentication Flow
1. **User Registration** (`POST /api/auth/signup`)
   - Email validation using Pydantic's `EmailStr`
   - Password minimum length: 8 characters
   - Passwords are pre-hashed with SHA256 before bcrypt to handle bcrypt's 72-byte limit
   - Bcrypt hashing with automatic salt generation
   - Duplicate email prevention at database level

2. **User Login** (`POST /api/auth/login`)
   - OAuth2 password flow implementation
   - JWT token generation with configurable expiration
   - Default token expiration: 30 minutes
   - Tokens include user ID in the `sub` claim

3. **Token Validation**
   - JWT tokens validated on protected endpoints
   - Algorithm: HS256 (HMAC with SHA-256)
   - Token verification includes expiration check
   - Invalid/expired tokens return 401 Unauthorized

### Password Security

#### Password Hashing Strategy
```python
# Two-stage hashing approach:
1. SHA256 pre-hash (handles passwords > 72 bytes)
2. Bcrypt hashing (industry standard, slow by design)
```

**Why SHA256 + Bcrypt?**
- Bcrypt has a 72-byte input limit
- SHA256 ensures consistent-length input to bcrypt
- Bcrypt provides adaptive hashing (resistant to brute force)
- Automatic salt generation per password

#### Password Requirements
- **Minimum length:** 8 characters
- **Recommendation:** Use strong passwords with mixed case, numbers, and symbols
- **Future enhancement:** Implement password strength meter and complexity requirements

### JWT Token Management

#### Token Structure
```json
{
  "sub": "user_id",
  "exp": "expiration_timestamp"
}
```

#### Security Considerations
- **Secret Key:** Must be set via environment variable (`SECRET_KEY`)
- **Algorithm:** HS256 (symmetric signing)
- **Expiration:** Configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`
- **Storage:** Tokens should be stored securely on client (e.g., httpOnly cookies or secure storage)

#### Token Lifecycle
1. Generated on successful login
2. Included in `Authorization: Bearer <token>` header for protected endpoints
3. Validated on each request to protected resources
4. Expires after configured time period
5. Client must re-authenticate after expiration

### Authorization

#### Access Control
- Users can only access their own data
- Protected endpoints use `get_current_active_user` dependency
- Authorization checks verify:
  - Valid token
  - User exists in database
  - User account is active (`is_active = True`)

#### Endpoint Protection
All endpoints under the following routes require authentication:
- `/api/account-holders/*`
- `/api/accounts/*`
- `/api/transactions/*`
- `/api/cards/*`
- `/api/statements/*`

## Data Security

### Database Security

#### SQL Injection Prevention
- **SQLAlchemy ORM** used for all database operations
- Parameterized queries prevent SQL injection
- No raw SQL queries with user input

#### Sensitive Data Handling
- **Passwords:** Never stored in plain text, always bcrypt hashed
- **Card CVV:** Stored as hash (if implemented)
- **Card Numbers:** Should be masked (show last 4 digits only)
- **User Data:** Isolated by user_id, enforced at application level

#### Database Configuration
- SQLite for development/testing
- Connection pooling via SQLAlchemy
- `check_same_thread=False` for SQLite (FastAPI async compatibility)

### Input Validation

#### Pydantic Schemas
All API inputs validated using Pydantic models:
- Type checking
- Field validation
- Email format validation
- Required field enforcement
- Custom validators for business logic

#### Example Validations
```python
- Email: EmailStr (RFC 5322 compliant)
- Password: min_length=8
- Numeric fields: Decimal precision validation
- Enum fields: Restricted to predefined values
```

## Network Security

### CORS (Cross-Origin Resource Sharing)

#### Current Configuration
```python
allow_origins=["*"]  # ⚠️ DEVELOPMENT ONLY
```

#### Production Recommendations
```python
allow_origins=[
    "https://yourdomain.com",
    "https://app.yourdomain.com"
]
allow_credentials=True
allow_methods=["GET", "POST", "PUT", "DELETE"]
allow_headers=["Authorization", "Content-Type"]
```

### HTTPS/TLS

#### Production Requirements
- **HTTPS only** in production
- TLS 1.2 or higher
- Valid SSL certificate
- Redirect HTTP to HTTPS
- HSTS (HTTP Strict Transport Security) headers

#### Implementation
```python
# Use reverse proxy (nginx/Apache) or cloud load balancer
# Example nginx config:
server {
    listen 443 ssl http2;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
}
```

## Rate Limiting

### Current Status
⚠️ **Not Implemented** - Planned for future release

### Recommendations

#### Authentication Endpoints
- **Login:** 5 attempts per 15 minutes per IP
- **Signup:** 3 attempts per hour per IP
- **Token refresh:** 10 requests per minute per user

#### API Endpoints
- **General:** 100 requests per minute per user
- **Transaction endpoints:** 20 requests per minute per user
- **Statement generation:** 5 requests per minute per user

#### Implementation Options
1. **Redis-based:** Use Redis for distributed rate limiting
2. **slowapi:** Python library for FastAPI rate limiting
3. **API Gateway:** Cloud provider rate limiting (AWS API Gateway, etc.)

## Environment Variables

### Required Variables
```bash
SECRET_KEY=<strong-random-key>  # CRITICAL: Must be set
DATABASE_URL=sqlite:///./banking.db
```

### Optional Variables
```bash
DEBUG=False  # Set to False in production
ACCESS_TOKEN_EXPIRE_MINUTES=30
API_PREFIX=/api
```

### Secret Management

#### Development
- Use `.env` file (never commit to git)
- `.env.example` provided for reference

#### Production
- Use environment variables
- Cloud secret managers (AWS Secrets Manager, Azure Key Vault, etc.)
- Kubernetes secrets
- Never hardcode secrets in code

## Security Best Practices

### Implemented ✅
- [x] Password hashing with bcrypt
- [x] JWT token authentication
- [x] Input validation with Pydantic
- [x] SQL injection prevention (ORM)
- [x] Environment variable configuration
- [x] User data isolation
- [x] Active user checks
- [x] Token expiration
- [x] Timezone-aware datetime handling

### Planned 🔄
- [ ] Rate limiting
- [ ] Request logging and monitoring
- [ ] Failed login attempt tracking
- [ ] Account lockout after failed attempts
- [ ] Two-factor authentication (2FA)
- [ ] API key authentication for service-to-service
- [ ] Audit logging for sensitive operations
- [ ] Data encryption at rest
- [ ] PII data masking in logs

### Production Checklist 📋

Before deploying to production:

1. **Environment**
   - [ ] Set strong `SECRET_KEY` (min 32 random characters)
   - [ ] Set `DEBUG=False`
   - [ ] Configure production database (PostgreSQL recommended)
   - [ ] Set up HTTPS/TLS
   - [ ] Configure CORS with specific origins

2. **Security**
   - [ ] Implement rate limiting
   - [ ] Set up monitoring and alerting
   - [ ] Enable request logging
   - [ ] Implement audit logging
   - [ ] Review and test all authentication flows
   - [ ] Conduct security audit/penetration testing

3. **Database**
   - [ ] Enable database backups
   - [ ] Set up database connection pooling
   - [ ] Configure database access restrictions
   - [ ] Implement database encryption at rest

4. **Infrastructure**
   - [ ] Use reverse proxy (nginx/Apache)
   - [ ] Set up firewall rules
   - [ ] Implement DDoS protection
   - [ ] Configure security headers
   - [ ] Set up intrusion detection

## Vulnerability Reporting

If you discover a security vulnerability, please:
1. **Do not** open a public issue
2. Email security concerns to: [security@yourdomain.com]
3. Include detailed description and reproduction steps
4. Allow reasonable time for fix before disclosure

## Compliance Considerations

### Future Compliance Goals
- **PCI DSS:** For card payment processing
- **GDPR:** For EU user data protection
- **SOC 2:** For security and availability
- **ISO 27001:** Information security management

### Data Protection
- User consent for data collection
- Right to data access and deletion
- Data retention policies
- Privacy policy documentation

## Security Updates

### Dependency Management
```bash
# Regularly update dependencies
pip install --upgrade -r requirements.txt

# Check for security vulnerabilities
pip-audit
```

### Security Patches
- Monitor CVE databases for Python/FastAPI vulnerabilities
- Subscribe to security mailing lists
- Implement automated dependency scanning (Dependabot, Snyk)

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [NIST Password Guidelines](https://pages.nist.gov/800-63-3/)

---

**Last Updated:** 2025-11-26  
**Version:** 1.0  
**Status:** Development
