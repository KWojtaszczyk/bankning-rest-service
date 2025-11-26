# AI Usage Report

## Project Summary
**Project:** Banking REST Service with Frontend  
**Development Period:** November 2025  
**AI Assistant:** Claude AI (Anthropic)  
**Total Development Time:** ~15 hours  
**Lines of Code:** ~2,500 (Backend + Frontend)

---

## Example Prompts & Iterations

### 1. Database Schema Design
**Prompt:**
> "Design a normalized SQLite database schema for a banking system with Users, AccountHolders, Accounts, Transactions, and Cards. Include appropriate relationships, constraints, and indexes."

**Result:** Complete ERD and SQLAlchemy models  
**Iterations:** 1  
**Manual Changes:** Added timezone-aware datetime handling

### 2. Authentication System
**Prompt:**
> "Implement a secure JWT-based authentication system with signup and login endpoints, including password hashing with bcrypt and token expiration."

**Result:** Complete auth service and routes  
**Iterations:** 2  
**Manual Changes:** Added SHA256 pre-hashing for bcrypt 72-byte limit

### 3. Statement Generation
**Prompt:**
> "Implement statement generation (PDF/JSON), card transaction validation with daily limits, and create API routes for card transactions."

**Result:** Complete statement service with reportlab PDF generation  
**Iterations:** 1  
**Manual Changes:** Simplified opening balance calculation for MVP

### 4. Frontend Interface
**Prompt:**
> "Create a visually stunning, premium web interface for the banking app using Vanilla HTML, CSS, and JavaScript, served directly by FastAPI."

**Result:** Full SPA-like frontend with glassmorphism and dark mode  
**Iterations:** 1  
**Manual Changes:** None

### 5. Test Suite Development
**Prompt:**
> "Create comprehensive test suites for statements and card transactions including validation checks."

**Result:** 9 tests across 2 new test files  
**Iterations:** 2  
**Manual Changes:** Fixed database session handling in auth tests

---

## Challenges Faced & AI Solutions

### Challenge 1: Bcrypt Password Limit
**Issue:** Bcrypt has a 72-byte input limit  
**AI Solution:** Suggested SHA256 pre-hashing before bcrypt  
**Manual Intervention:** Verified security implications and documented in SECURITY.md  
**Outcome:** Implemented secure two-stage hashing

### Challenge 2: Deprecated datetime.utcnow()
**Issue:** AI initially used deprecated `datetime.utcnow()`  
**AI Solution:** N/A (AI generated the deprecated code)  
**Manual Intervention:** Identified during code review, updated to `datetime.now(timezone.utc)`  
**Outcome:** All models updated with timezone-aware datetime

### Challenge 3: Test Database Session Handling
**Issue:** `test_password_hashed_in_database` failed due to "Two Databases" problem  
**AI Solution:** Created `db_session` fixture in conftest.py  
**Manual Intervention:** Explained the root cause (SessionLocal vs TestingSessionLocal)  
**Outcome:** All 51 tests passing

### Challenge 4: Type Mismatch in KYC Field
**Issue:** `kyc_verified` was String instead of Boolean  
**AI Solution:** Identified during code review  
**Manual Intervention:** Confirmed fix and tested  
**Outcome:** Type corrected across models and schemas

### Challenge 5: Card Number Security
**Issue:** Card numbers stored in plain text (MVP)  
**AI Solution:** Added comprehensive warnings and documentation  
**Manual Intervention:** Decided to keep plain text for MVP with clear warnings  
**Outcome:** Documented PCI DSS requirements in SECURITY.md

---

## Areas Requiring Manual Intervention

### 1. Security-Critical Decisions
- **SHA256 pre-hashing strategy:** Required domain expertise to verify
- **SECRET_KEY validation:** Manual implementation of runtime checks
- **CORS configuration:** Security review for production readiness
- **Card number encryption:** Decision to defer to production phase

### 2. Business Logic Validation
- **KYC field types:** Required understanding of real-world KYC processes
- **Account status workflows:** Validated against banking domain knowledge
- **Transaction integrity:** Manual review of ACID compliance

### 3. Test Debugging
- **Logout assertion fix:** Changed `"logout"` to `"successfully logged out"`
- **Database session fixture:** Created proper test DB session sharing
- **Transaction schema updates:** Added `card_id` and `merchant_name` fields

### 4. Documentation Refinement
- **README.md:** Condensed to setup + API docs only
- **FUTURE_ROADMAP.md:** Removed completed features, shortened content
- **SECURITY.md:** Added card/statement-specific security considerations

---

## AI Effectiveness Metrics

### Code Generation
- **Total Lines:** ~2,500
- **AI-Generated:** ~2,100 (84%)
- **Manually Modified:** ~400 (16%)

### Time Efficiency
- **Estimated Manual Time:** 30 hours
- **Actual Time:** 15 hours
- **Time Saved:** 50%

### Quality Metrics
- **Tests Written:** 51 (all passing)
- **Bugs Fixed:** 12+
- **Security Issues Identified:** 7
- **Documentation Pages:** 4 (comprehensive)

---

## Key Learnings

### What AI Excelled At
1. **Boilerplate Generation:** FastAPI routes, SQLAlchemy models, Pydantic schemas
2. **Pattern Implementation:** JWT auth, OAuth2, database relationships
3. **Documentation:** SECURITY.md, FUTURE_ROADMAP.md, API docs
4. **Frontend Development:** Premium UI with glassmorphism, responsive design
5. **Test Generation:** Comprehensive test suites with edge cases

### What Required Human Oversight
1. **Security Decisions:** Encryption strategies, token management
2. **Business Logic:** KYC workflows, transaction validation
3. **Debugging:** Test failures, database session issues
4. **Production Readiness:** Environment config, deployment considerations

### Best Practices Discovered
1. **Clear Prompts:** Specific requirements + context = better results
2. **Iterative Review:** Always review AI output, especially security code
3. **Documentation First:** Use AI to draft, then refine manually
4. **Test Early:** AI-generated tests catch AI-generated bugs

---

**Overall AI Contribution Score:** 9/10  
**Recommendation:** AI is highly effective for rapid prototyping and full-stack development when paired with human oversight for security and business logic.

---

**Last Updated:** 2025-11-26  
**Compiled by:** Human Developer with AI Assistance
