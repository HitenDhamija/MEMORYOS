"""
Complete JWT Authentication Example

This file shows the complete flow of registering, logging in, and authenticating API calls.
"""

# ============================================================================
# BACKEND SETUP
# ============================================================================

# 1. Environment variables (.env)
SECRET_KEY="your-secret-key-minimum-32-characters"
DATABASE_URL="postgresql://user:password@localhost:5432/memoryos"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS="http://localhost:3000"


# 2. Core Security (app/core/security.py)
# Already implements:
# - Password hashing with bcrypt
# - JWT token creation and validation
# - Token type verification


# 3. Services Layer
# AuthService: register, authenticate, create_tokens, refresh_access_token
# UserService: get_user, update_user, deactivate_user


# 4. FastAPI Application (main.py)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="MemoryOS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# STEP 1: USER REGISTRATION
# ============================================================================

# Frontend: User visits http://localhost:3000/register

# User fills form:
# Email: alice@example.com
# Username: alice
# Password: SecurePassword123
# Full Name: Alice Smith

# Frontend calls:
"""
POST /api/v1/auth/register
{
  "email": "alice@example.com",
  "username": "alice",
  "password": "SecurePassword123",
  "full_name": "Alice Smith"
}
"""

# Backend processes:
# 1. Validate input with Pydantic schema
# 2. Check email/username not taken
# 3. Hash password with bcrypt
# 4. Create user in database
# 5. Return user data (without password)

# Response:
"""
201 Created
{
  "id": 1,
  "email": "alice@example.com",
  "username": "alice",
  "full_name": "Alice Smith",
  "is_active": true,
  "created_at": "2024-06-16T10:00:00",
  "updated_at": "2024-06-16T10:00:00"
}
"""

# Frontend: Redirects to login page


# ============================================================================
# STEP 2: USER LOGIN
# ============================================================================

# Frontend: User visits http://localhost:3000/login

# User enters credentials:
# Email: alice@example.com
# Password: SecurePassword123

# Frontend calls:
"""
POST /api/v1/auth/login
{
  "email": "alice@example.com",
  "password": "SecurePassword123"
}
"""

# Backend processes:
# 1. Query user by email
# 2. Verify password with bcrypt
# 3. Check if user is active
# 4. Create JWT access token
#    - Payload: {sub: 1, type: "access", exp: 1718531400}
#    - Sign with SECRET_KEY
#    - Expires in 30 minutes
# 5. Create JWT refresh token
#    - Payload: {sub: 1, type: "refresh", exp: 1719136200}
#    - Sign with SECRET_KEY
#    - Expires in 7 days
# 6. Return both tokens

# Response:
"""
200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
"""

# Frontend processes:
# 1. Store access_token in httpOnly cookie (1 day expiry)
# 2. Store refresh_token in httpOnly cookie (7 day expiry)
# 3. Fetch user profile via GET /api/v1/users/me (using new token)
# 4. Store user in Zustand
# 5. Redirect to dashboard


# ============================================================================
# STEP 3: PROTECTED API CALL
# ============================================================================

# Frontend: User on dashboard makes API call
# Example: Fetch list of memories

# Frontend calls:
"""
GET /api/v1/memories
"""

# Request Interceptor:
# 1. Gets access_token from cookies
# 2. Adds to header: Authorization: Bearer <token>

"""
GET /api/v1/memories
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
"""

# Backend processes:
# 1. Extract token from Authorization header
# 2. Decode token
# 3. Verify signature with SECRET_KEY
# 4. Check expiration (not expired)
# 5. Verify token type is "access"
# 6. Extract user_id from "sub" claim
# 7. Load user from database
# 8. Check user is active
# 9. Attach user to request context
# 10. Execute endpoint: return user's memories

# Response:
"""
200 OK
{
  "items": [
    {
      "id": 1,
      "user_id": 1,
      "title": "Python Notes",
      "content": "...",
      "tags": "python,programming",
      "is_archived": false,
      "created_at": "...",
      "updated_at": "..."
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 10
}
"""


# ============================================================================
# STEP 4: TOKEN EXPIRATION & REFRESH (AUTOMATIC)
# ============================================================================

# 30 minutes pass...
# User tries another API call

# Frontend calls:
"""
GET /api/v1/upload
Authorization: Bearer <expired_token>
"""

# Backend returns:
"""
401 Unauthorized
{
  "detail": "Invalid or expired token"
}
"""

# Response Interceptor:
# 1. Detects 401 status
# 2. Gets refresh_token from cookies
# 3. Queues current request
# 4. Calls:

"""
POST /api/v1/auth/refresh
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
"""

# Backend processes:
# 1. Decode refresh token
# 2. Verify token type is "refresh"
# 3. Verify not expired
# 4. Extract user_id
# 5. Load user from database
# 6. Check user is active
# 7. Generate NEW access token
# 8. Return new token

# Response:
"""
200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
"""

# Frontend Interceptor:
# 1. Stores new access_token in cookie
# 2. Retries original GET /api/v1/upload with new token
# 3. Returns data to caller
# ALL TRANSPARENT TO USER


# ============================================================================
# STEP 5: UPDATE PROFILE
# ============================================================================

# Frontend: User on profile page updates full_name

# Frontend calls:
"""
PUT /api/v1/users/me
Authorization: Bearer <valid_token>
{
  "full_name": "Alice Johnson"
}
"""

# Backend processes:
# 1. Authenticate user (get current user from token)
# 2. Validate new email is unique (if changed)
# 3. Hash new password (if provided)
# 4. Update user in database
# 5. Return updated user

# Response:
"""
200 OK
{
  "id": 1,
  "email": "alice@example.com",
  "username": "alice",
  "full_name": "Alice Johnson",
  "is_active": true,
  "created_at": "...",
  "updated_at": "..."
}
"""

# Frontend:
# 1. Updates user in Zustand store
# 2. Navigation shows new name


# ============================================================================
# STEP 6: LOGOUT
# ============================================================================

# Frontend: User clicks "Logout" button

# Frontend:
# 1. Calls authService.logout()
# 2. Makes optional API call:

"""
POST /api/v1/auth/logout
Authorization: Bearer <token>
"""

# Backend:
# 1. Acknowledges logout (optional)
# 2. Returns success message
# (Note: Actual token cleanup happens on client)

# Frontend:
# 1. Removes access_token cookie
# 2. Removes refresh_token cookie
# 3. Clears user from Zustand
# 4. Redirects to /login


# ============================================================================
# STEP 7: LOGOUT & REFRESH TOKEN EXPIRED
# ============================================================================

# User logged out yesterday
# 7 days pass
# User tries to login again
# Browser still has (now invalid) refresh_token

# Frontend:
# 1. App initializes
# 2. Finds refresh_token in cookies
# 3. Tries to refresh:

"""
POST /api/v1/auth/refresh
{
  "refresh_token": "<expired_refresh_token>"
}
"""

# Backend:
"""
401 Unauthorized
{
  "detail": "Invalid or expired refresh token"
}
"""

# Frontend:
# 1. Catches error
# 2. Clears both tokens
# 3. Redirects to login
# User must login again


# ============================================================================
# SECURITY FLOW EXAMPLE
# ============================================================================

# Scenario: Attacker tries to use a stolen token

# Attacker has: access_token from intercepted request

# Attacker calls:
"""
GET /api/v1/users/me
Authorization: Bearer <stolen_token>
"""

# Backend:
# 1. Decode token
# 2. Check signature → OK (same SECRET_KEY)
# 3. Check expiration:
#    - If expired: Return 401
#    - If not expired: Process normally (legitimate 30-min window)
#
# Security: Token expires in 30 minutes, not reusable after that
# Attacker would need to get NEW tokens, which requires password


# ============================================================================
# DATABASE STATE AFTER COMPLETE FLOW
# ============================================================================

# users table:
"""
id | email              | username | hashed_password (bcrypt) | is_active | created_at
1  | alice@example.com  | alice    | $2b$12$N9q...           | true      | 2024-06-16
"""

# JWT Token History (in logs or monitoring):
"""
2024-06-16 10:00:00 - Register user alice
2024-06-16 10:05:00 - Login: issue token #1 (expires 10:35)
2024-06-16 10:20:00 - Request with token #1
2024-06-16 10:32:00 - Token #1 expired, refresh issued token #2
2024-06-16 10:35:00 - Request with token #2
2024-06-16 10:40:00 - Logout requested
"""


# ============================================================================
# KEY CONCEPTS
# ============================================================================

"""
1. PASSWORD HASHING
   - User password never stored in plain text
   - Stored as bcrypt hash: $2b$12$...
   - On login: verify(password, hash) using bcrypt
   - Attacker cannot reverse hash to get password

2. ACCESS TOKEN
   - Short-lived (30 min)
   - Contains user_id
   - Cannot be used to get new tokens (type: "access")
   - Used for API requests
   - If exposed, attacker only has 30-min window

3. REFRESH TOKEN
   - Long-lived (7 days)
   - Contains user_id
   - Can ONLY get new access tokens (type: "refresh")
   - Stored securely in HttpOnly cookie
   - If exposed, attacker could get new access tokens BUT:
     * Would need to act within 7 days
     * User can deactivate account immediately

4. TOKEN TYPE VERIFICATION
   - Each token has a "type" claim
   - Access token with type: "access" can ONLY be used for API calls
   - Refresh token with type: "refresh" can ONLY be used for refresh
   - Prevents token misuse

5. AUTOMATIC REFRESH
   - Frontend automatically refreshes when token expires
   - No user action required
   - Transparent to user
   - Keeps user logged in

6. HTTPONLY COOKIES
   - Stored in secure, encrypted cookie
   - JavaScript cannot access (prevents XSS theft)
   - Automatically sent with every request
   - Cannot be stolen by malicious JavaScript

7. USER ISOLATION
   - Each user can only access their own data
   - user_id in token ensures this
   - API checks: memory.user_id == current_user.id
   - Cannot access other user's memories/data
"""


# ============================================================================
# TESTING THE COMPLETE FLOW
# ============================================================================

# Using curl:

# 1. Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "username": "alice",
    "password": "SecurePassword123",
    "full_name": "Alice"
  }'

# 2. Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "SecurePassword123"
  }' | jq -r '.access_token')

# 3. Protected call
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"

# 4. Update profile
curl -X PUT http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"full_name": "Alice Johnson"}'

# 5. Logout (optional)
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer $TOKEN"
