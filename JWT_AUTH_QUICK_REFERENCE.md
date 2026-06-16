# JWT Authentication Quick Reference

## API Endpoints

### Authentication

```bash
# Register
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "testuser",
  "password": "SecurePass123",
  "full_name": "Test User"
}

# Response
{
  "id": 1,
  "email": "user@example.com",
  "username": "testuser",
  "full_name": "Test User",
  "is_active": true,
  "created_at": "2024-06-16T...",
  "updated_at": "2024-06-16T..."
}
```

```bash
# Login
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123"
}

# Response
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

```bash
# Refresh Token
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGc..."
}

# Response
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### User Profile

```bash
# Get Current User
GET /api/v1/users/me
Authorization: Bearer <access_token>

# Response
{
  "id": 1,
  "email": "user@example.com",
  "username": "testuser",
  "full_name": "Test User",
  "is_active": true,
  "created_at": "2024-06-16T...",
  "updated_at": "2024-06-16T..."
}
```

```bash
# Update Profile
PUT /api/v1/users/me
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "email": "newemail@example.com",
  "full_name": "Updated Name",
  "password": "NewPassword123"
}
```

```bash
# Deactivate Account
POST /api/v1/users/me/deactivate
Authorization: Bearer <access_token>
```

## Frontend Usage

### Login Example

```typescript
import { useAuth } from "@/hooks/useAuth";

function LoginComponent() {
  const { login, isLoading } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(email, password);
      // Auto-redirects to dashboard
    } catch (error) {
      console.error("Login failed");
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      <button disabled={isLoading}>
        {isLoading ? "Logging in..." : "Login"}
      </button>
    </form>
  );
}
```

### Protected Page Example

```typescript
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useAuth } from "@/hooks/useAuth";

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <Dashboard />
    </ProtectedRoute>
  );
}

function Dashboard() {
  const { user, logout, updateProfile } = useAuth();

  return (
    <div>
      <h1>Welcome, {user?.full_name}</h1>
      <button onClick={logout}>Logout</button>
    </div>
  );
}
```

### Manual API Call Example

```typescript
import apiClient from "@/services/apiClient";

// Token automatically added by interceptor
const response = await apiClient.get("/v1/memories");

// On 401 (token expired):
// 1. Interceptor detects 401
// 2. Calls refresh endpoint
// 3. Gets new access token
// 4. Retries original request
// 5. Returns data to caller
```

## Token Details

### Access Token
- **Expires**: 30 minutes (configurable via ACCESS_TOKEN_EXPIRE_MINUTES)
- **Type**: "access"
- **Usage**: API requests
- **Storage**: HttpOnly cookie
- **Claims**: {sub: user_id, type: "access", exp, iat}

### Refresh Token
- **Expires**: 7 days (configurable via REFRESH_TOKEN_EXPIRE_DAYS)
- **Type**: "refresh"
- **Usage**: Getting new access tokens only
- **Storage**: HttpOnly cookie
- **Claims**: {sub: user_id, type: "refresh", exp, iat}

## Configuration

### Backend (.env)
```env
# JWT Configuration
SECRET_KEY=your-secret-key-minimum-32-characters-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/memoryos

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Environment
ENVIRONMENT=development
DEBUG=True
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 200 | Success | N/A |
| 201 | Created | N/A |
| 400 | Bad Request | Check request format, validate inputs |
| 401 | Unauthorized | Login again, token expired or invalid |
| 403 | Forbidden | Account inactive or insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 500 | Server Error | Check server logs |

## Common Issues & Solutions

### Issue: Always redirected to login
**Cause**: Auth initialization failing  
**Solution**: Check browser console for errors, verify NEXT_PUBLIC_API_URL

### Issue: Token refresh fails
**Cause**: Refresh token expired (> 7 days) or invalid  
**Solution**: User must login again

### Issue: CORS error on login
**Cause**: Backend CORS_ORIGINS doesn't match frontend URL  
**Solution**: Add frontend URL to backend CORS_ORIGINS

### Issue: Tokens not persisting after refresh
**Cause**: HttpOnly cookie handling issue  
**Solution**: Verify cookies are enabled, check secure flag in production

### Issue: Cannot update profile
**Cause**: Email already taken or invalid data  
**Solution**: Check error message, use unique email

## Testing Checklist

- [ ] Can register new account
- [ ] Can login with correct credentials
- [ ] Cannot login with wrong password
- [ ] Tokens are issued on login
- [ ] Can refresh token
- [ ] Old token stops working after refresh
- [ ] Session persists on page reload
- [ ] Can access protected pages when logged in
- [ ] Cannot access protected pages when logged out
- [ ] Token automatically refreshes when expired
- [ ] Can update profile
- [ ] Can logout
- [ ] Can deactivate account

## Security Tips

✅ **DO:**
- Use HTTPS in production
- Set strong SECRET_KEY (32+ chars, random)
- Rotate SECRET_KEY periodically
- Use unique usernames/emails
- Enforce strong passwords
- Monitor token expiration

❌ **DON'T:**
- Expose SECRET_KEY in frontend
- Store tokens in localStorage
- Use weak passwords
- Skip HTTPS in production
- Disable token expiration
- Allow unlimited login attempts

## Production Deployment

1. Generate strong SECRET_KEY
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

2. Update .env
```env
SECRET_KEY=<generated-key>
ENVIRONMENT=production
DEBUG=False
CORS_ORIGINS=https://yourdomain.com
```

3. Enable HTTPS
```env
# Cookies will only work over HTTPS
```

4. Test token refresh flow
5. Set up monitoring and logging
6. Consider token blacklist for immediate revocation
7. Implement rate limiting on auth endpoints
8. Set up password reset functionality

## Database Schema

### users table
```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  username VARCHAR(100) UNIQUE NOT NULL,
  hashed_password VARCHAR(255) NOT NULL,
  full_name VARCHAR(255),
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
```

## Next Steps

1. Add password reset functionality
2. Implement multi-factor authentication
3. Add role-based access control
4. Set up audit logging
5. Implement token blacklist (Redis)
6. Add IP whitelisting
7. Implement account lockout on failed attempts
8. Add email verification
