# JWT Authentication Implementation

Complete JWT authentication system for MemoryOS with access & refresh tokens.

## Overview

The authentication system uses:
- **Access Tokens**: Short-lived (30 minutes) for API requests
- **Refresh Tokens**: Long-lived (7 days) for obtaining new access tokens
- **HttpOnly Cookies**: Secure token storage (browser cannot access via JavaScript)
- **Automatic Refresh**: Transparently refreshes tokens when expired
- **Token Type Verification**: Ensures tokens are used for their intended purpose

## Backend Architecture

### Security Module (`app/core/security.py`)

**Key Functions:**

```python
create_token(data, token_type, expires_delta)  # Create access/refresh token
create_access_token(data)                      # Shortcut for access token
create_refresh_token(data)                     # Shortcut for refresh token
verify_token_type(token, expected_type)        # Verify token type
decode_token(token)                            # Decode and validate JWT
verify_password(plain, hashed)                 # Verify password
get_password_hash(password)                    # Hash password with bcrypt
```

**Token Structure:**
```json
{
  "sub": 123,              // User ID
  "type": "access",        // "access" or "refresh"
  "exp": 1718534400,       // Expiration timestamp
  "iat": 1718531400        // Issued at timestamp
}
```

### Authentication Service (`app/services/auth_service.py`)

**Methods:**

```python
register(db, user_data)              # Register new user
authenticate(db, email, password)    # Validate credentials
create_tokens(user_id)               # Create access + refresh tokens
refresh_access_token(user_id)        # Generate new access token
```

**Usage:**
```python
user = AuthService.authenticate(db, email, password)
tokens = AuthService.create_tokens(user.id)
return {"access_token": tokens["access_token"], "refresh_token": tokens["refresh_token"]}
```

### User Service (`app/services/user_service.py`)

**Methods:**

```python
get_user_by_id(db, user_id)          # Get user by ID
get_user_by_email(db, email)         # Get user by email
update_user(db, user_id, data)       # Update profile
deactivate_user(db, user_id)         # Deactivate account
```

### Dependencies (`app/api/deps.py`)

**get_current_user(credentials, db)**
- Extracts JWT token from Authorization header
- Verifies token type is "access"
- Validates token signature and expiration
- Returns authenticated User or raises HTTPException

**get_refresh_token_user(token, db)**
- Extracts user from refresh token
- Used for refresh endpoint
- Validates token type is "refresh"

### API Endpoints

```
POST   /api/v1/auth/register          # Register user
  Request:  {email, username, password, full_name?}
  Response: {id, email, username, full_name, is_active, created_at, updated_at}

POST   /api/v1/auth/login             # Login & get tokens
  Request:  {email, password}
  Response: {access_token, refresh_token, token_type}

POST   /api/v1/auth/refresh           # Refresh access token
  Request:  {refresh_token}
  Response: {access_token, token_type}

POST   /api/v1/auth/logout            # Logout (client-side token removal)
  Response: {message}

GET    /api/v1/users/me               # Get current user (requires token)
  Response: {id, email, username, full_name, is_active, created_at, updated_at}

PUT    /api/v1/users/me               # Update profile (requires token)
  Request:  {email?, full_name?, password?}
  Response: {id, email, username, full_name, is_active, created_at, updated_at}

POST   /api/v1/users/me/deactivate    # Deactivate account (requires token)
  Response: {message}
```

## Frontend Architecture

### Auth Service (`src/services/authService.ts`)

**Token Management:**
```typescript
setTokens(accessToken, refreshToken)     // Store both tokens
setAccessToken(token)                    // Store access token only
getAccessToken()                         // Retrieve access token
getRefreshToken()                        // Retrieve refresh token
clearTokens()                            // Remove all tokens
isAuthenticated()                        // Check if logged in
hasRefreshToken()                        // Check for refresh token
```

**Auth Operations:**
```typescript
register(data)                           // Create new account
login(credentials)                       // Login and get tokens
refreshAccessToken()                     // Get new access token
logout()                                 // Clear tokens
getProfile()                             // Fetch user info
updateProfile(data)                      // Update profile
deactivateAccount()                      // Deactivate account
```

### API Client (`src/services/apiClient.ts`)

**Request Interceptor:**
- Dynamically adds Bearer token to all requests
- Runs before each API call

**Response Interceptor:**
- Catches 401 responses (token expired)
- Attempts automatic token refresh
- Queues failed requests during refresh
- Retries with new token
- Redirects to login if refresh fails

**Token Queue System:**
```
Request 1 expires → Trigger refresh
Request 2 queued  → Wait for refresh
Request 3 queued  → Wait for refresh
Refresh completes → Execute all queued requests
```

### Auth Store (`src/context/authStore.ts`)

**State (Zustand):**
```typescript
user: User | null              // Current user
isAuthenticated: boolean       // Auth status
isLoading: boolean            // Loading state
```

**Persistence:**
- User data cached in localStorage
- Survives page reloads
- Tokens stay in HttpOnly cookies (secure)

**Actions:**
```typescript
setUser(user)                  // Set authenticated user
clearUser()                    // Clear user data
setLoading(loading)           // Update loading state
logout()                      // Clear on logout
```

### Auth Hook (`src/hooks/useAuth.ts`)

**Initialization:**
- Runs on app mount via AuthProvider
- Checks for valid access token
- Falls back to refresh token if needed
- Fetches user profile if authenticated

**Methods:**
```typescript
login(email, password)         // Login user
register(email, username, password, fullName?) // Register
logout()                       // Logout
updateProfile(data)           // Update profile
deactivateAccount()           // Deactivate account
refreshSession()              // Manual refresh
```

### Auth Provider (`src/components/auth/AuthProvider.tsx`)

**Global Auth State:**
- Wraps entire app in root layout
- Initializes auth on mount
- Restores session from tokens
- Handles refresh failures

**Usage:**
```typescript
<AuthProvider>
  {children}
</AuthProvider>
```

### Protected Route (`src/components/auth/ProtectedRoute.tsx`)

**Client-Side Protection:**
- Prevents rendering until auth check completes
- Redirects to login if not authenticated
- Shows loading state

**Usage:**
```typescript
<ProtectedRoute>
  <Dashboard />
</ProtectedRoute>
```

## Authentication Flow

### 1. Registration
```
User Form
  ↓
authService.register()
  ↓
POST /api/v1/auth/register
  ↓
Backend validates & creates user
  ↓
Redirect to login
```

### 2. Login
```
User enters credentials
  ↓
authService.login()
  ↓
POST /api/v1/auth/login
  ↓
Backend validates password
  ↓
Backend returns access + refresh tokens
  ↓
Frontend stores in cookies
  ↓
Fetch user profile
  ↓
Store in Zustand
  ↓
Redirect to dashboard
```

### 3. Protected API Calls
```
Component calls API
  ↓
apiClient interceptor adds token
  ↓
Request sent with Authorization header
  ↓
Backend validates token & user
  ↓
Backend returns data
```

### 4. Token Refresh (Automatic)
```
API call returns 401
  ↓
Response interceptor detects expired token
  ↓
Call refreshAccessToken()
  ↓
POST /api/v1/auth/refresh with refresh_token
  ↓
Backend validates refresh token
  ↓
Backend returns new access token
  ↓
Frontend stores new token
  ↓
Retry original request
  ↓
Success or re-queue if multiple requests
```

### 5. Logout
```
User clicks Logout
  ↓
authService.logout()
  ↓
Clear all tokens
  ↓
Clear user from store
  ↓
Redirect to login
```

## Security Features

### Password Security
- **Hashing**: bcrypt with cost factor 12
- **Verification**: Constant-time comparison
- **Never Stored**: Plain passwords not stored

### Token Security
- **Signing**: HS256 algorithm with SECRET_KEY
- **Expiration**: Access tokens expire after 30 minutes
- **Type Verification**: Each token has a "type" claim
- **Claims**: Include user_id, expiration, issue time
- **Refresh Limitation**: Refresh tokens don't grant API access

### Storage Security
- **HttpOnly Cookies**: JS cannot access tokens
- **Secure Flag**: Only transmitted over HTTPS in production
- **SameSite Policy**: Prevents CSRF attacks
- **Separate Tokens**: Access and refresh stored separately

### API Security
- **Authorization Header**: Bearer token scheme
- **Request Validation**: Pydantic schemas
- **User Isolation**: Users can only access their own data
- **Account Status**: Inactive users cannot authenticate
- **Rate Limiting**: Ready to implement

## Configuration

### Backend (.env)
```env
DATABASE_URL=postgresql://user:password@localhost:5432/memoryos
SECRET_KEY=your-secret-key-min-32-chars  # Change in production!
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=http://localhost:3000
ENVIRONMENT=development
DEBUG=True
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## Testing

### Via Swagger UI (http://localhost:8000/docs)

1. **Register User**
   - POST /api/v1/auth/register
   - Fill in details

2. **Login**
   - POST /api/v1/auth/login
   - Copy access_token

3. **Authorize in UI**
   - Click "Authorize" button
   - Paste: `Bearer <token>`

4. **Test Protected Endpoint**
   - GET /api/v1/users/me
   - Should return user data

5. **Refresh Token**
   - POST /api/v1/auth/refresh
   - Pass refresh_token

### Via Frontend

1. Visit http://localhost:3000/register
2. Create account
3. Redirected to login
4. Login with credentials
5. Redirected to dashboard
6. Try protected pages
7. Tokens automatically refresh when needed

### Via cURL

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "SecurePassword123",
    "full_name": "Test User"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123"
  }'

# Use token (replace TOKEN with actual token)
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer TOKEN"

# Refresh (replace REFRESH_TOKEN)
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "REFRESH_TOKEN"}'
```

## Best Practices Implemented

✅ **Separation of Concerns**
- Auth service for business logic
- Security module for cryptography
- Dependencies for injection

✅ **Clean API Design**
- RESTful endpoints
- Clear request/response schemas
- Proper HTTP status codes

✅ **Type Safety**
- TypeScript frontend
- Pydantic validation backend
- Explicit type hints

✅ **Error Handling**
- Detailed error messages
- Proper HTTP status codes
- Graceful degradation

✅ **Token Management**
- Automatic refresh
- Queue for parallel requests
- Proper expiration handling

✅ **Security**
- Password hashing
- Token signing
- User isolation
- Input validation

✅ **User Experience**
- Session persistence
- Automatic token refresh
- Loading states
- Error feedback

## Scaling Considerations

### Stateless Design
- No server-side sessions
- Tokens valid across instances
- Load balanced deployments supported

### Token Blacklisting
- Optional Redis implementation
- For immediate token revocation
- Useful for forced logouts

### Multi-Factor Authentication
- Ready to extend
- Additional token types
- Second factor verification

### Permission System
- Scope-based tokens possible
- Role claims in JWT
- Authorization middleware ready

## Troubleshooting

### Token Expired Error
**Cause**: Access token expired  
**Solution**: Automatic retry with refresh token or manual login

### Refresh Token Invalid
**Cause**: Refresh token expired (7 days)  
**Solution**: User must login again

### 401 Unauthorized
**Cause**: Missing or invalid token  
**Solution**: Check Authorization header format: `Bearer <token>`

### CORS Error
**Cause**: Frontend/backend mismatch  
**Solution**: Verify CORS_ORIGINS in backend .env

### Token in localStorage
**Security Issue**: Vulnerable to XSS  
**Solution**: Use HttpOnly cookies (implemented)

## Production Checklist

- [ ] Generate strong SECRET_KEY (32+ characters)
- [ ] Set ENVIRONMENT=production
- [ ] Set DEBUG=False
- [ ] Enable HTTPS (Secure cookie flag)
- [ ] Set SameSite=Strict
- [ ] Configure CORS_ORIGINS properly
- [ ] Use managed PostgreSQL
- [ ] Set up monitoring
- [ ] Enable rate limiting
- [ ] Consider token blacklist/Redis
- [ ] Test token refresh flow
- [ ] Implement logout endpoint
