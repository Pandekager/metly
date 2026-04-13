# Login Security Improvements

## Overview

The login system has been upgraded with industry-standard security practices to protect user credentials and prevent common authentication vulnerabilities.

## Security Fixes Implemented

### 1. Password Hashing with bcrypt

- **Before**: Passwords stored as plaintext in database
- **After**: Passwords hashed using bcrypt (industry standard)
- **Benefit**: Even if database is compromised, passwords cannot be recovered

### 2. SQL Injection Prevention

- **Before**: SQL queries used string interpolation
- **After**: All queries use parameterized statements via SQLAlchemy
- **Benefit**: Prevents attackers from injecting malicious SQL code

### 3. Email Validation

- **Before**: Email accepted as plain string
- **After**: Email validated using Pydantic's `EmailStr`
- **Benefit**: Ensures valid email format and prevents invalid inputs

### 4. Timing Attack Prevention

- **Before**: Different error messages for invalid email vs password
- **After**: Same generic error message for both cases
- **Benefit**: Prevents attackers from enumerating valid email addresses

## Setup Instructions

### 1. Install Dependencies

```bash
cd /home/rasmus/Work/metly/backend
pip install "passlib[bcrypt]"
```

### 2. Migrate Existing Passwords (One-time operation)

If you have existing users with plaintext passwords:

```bash
python scripts/migrate_passwords.py
```

This script will:

- Connect to the database
- Hash all plaintext passwords using bcrypt
- Update the database with hashed passwords
- Skip passwords that are already hashed

**WARNING**: This is a one-way operation. Original passwords cannot be recovered after migration.

### 3. Start the Backend Server

```bash
cd /home/rasmus/Work/metly/backend
uvicorn src.endpoints.getData:app --host 0.0.0.0 --port 8000
```

## API Usage

### Login Endpoint

**POST** `/auth/login`

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "SecurePassword123"
}
```

**Success Response (200):**

```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Error Response (401):**

```json
{
  "detail": "Invalid email or password"
}
```

## Creating New Users

When creating new users via `createDB.py`, passwords are automatically hashed:

```python
from src.scripts.db.createDB import createUser

# This will generate a random password and hash it automatically
createUser(
    db_usr=db_usr,
    db_pwd=db_pwd,
    platform="platform_id",
    email="newuser@example.com",
    api_key="api_key_value",
    tenant="tenant_value"
)
```

The script will output:

- Email address
- Temporary plaintext password (save this!)
- Warning to save password securely

## Security Best Practices

1. **Never log passwords**: The code ensures passwords are never logged
2. **HTTPS only**: In production, always use HTTPS to encrypt credentials in transit
3. **Password complexity**: Enforce strong password requirements on frontend
4. **Rate limiting**: Consider adding rate limiting to prevent brute force attacks
5. **Session management**: JWT tokens expire after 24 hours for security

## Testing the Login

### Using curl:

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "YourPassword"}'
```

### Using Python:

```python
import requests

response = requests.post(
    "http://localhost:8000/auth/login",
    json={
        "email": "user@example.com",
        "password": "YourPassword"
    }
)

if response.status_code == 200:
    user_id = response.json()["user_id"]
    print(f"Login successful! User ID: {user_id}")
else:
    print(f"Login failed: {response.json()}")
```

## Files Modified

1. `/home/rasmus/Work/metly/backend/src/endpoints/getData.py`

   - Added password hashing verification
   - Added email validation
   - Fixed SQL injection vulnerability
   - Improved error handling

2. `/home/rasmus/Work/metly/backend/src/scripts/db/createDB.py`

   - Added password hashing for new users
   - Display temporary password to admin

3. `/home/rasmus/Work/metly/backend/scripts/migrate_passwords.py` (new)
   - Utility to migrate existing passwords to hashed versions

## Dependencies Added

- `passlib[bcrypt]`: Password hashing library with bcrypt support
- Uses existing `pydantic` for email validation

## Frontend Compatibility

The frontend (`login.post.ts`) remains compatible with these changes:

- Same API endpoint: `/auth/login`
- Same request format: `{ email, password }`
- Same response format: `{ user_id }`

No frontend changes are required.
