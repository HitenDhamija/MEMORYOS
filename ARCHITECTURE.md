# Architecture Documentation

## System Overview

MemoryOS is a full-stack SaaS application with:
- **Frontend**: Next.js with app directory routing
- **Backend**: FastAPI with PostgreSQL
- **Authentication**: JWT-based with role/permission ready

## Frontend Architecture

### Pages & Routing (App Directory)

```
(auth)/
  ├── login/page.tsx              # Public - Login form
  └── register/page.tsx           # Public - Registration form

(dashboard)/                       # Group requires auth middleware
  ├── dashboard/page.tsx          # Dashboard overview
  ├── upload/page.tsx             # Upload new memory
  ├── search/page.tsx             # Search memories
  └── profile/page.tsx            # User settings
```

**Middleware**: Protects (dashboard) routes, redirects unauthenticated users to login

### Component Structure

- **UI Components** (`components/ui/`): Shadcn-based reusable components
- **Layout Components** (`components/layout/`): Navigation, sidebars
- **Form Components** (`components/forms/`): Login, register, memory forms

### Data Flow

```
Page Component
    ↓
Hook (useAuth, custom hooks)
    ↓
Service (memoryService, authService)
    ↓
API Client (axios instance)
    ↓
Backend API
```

### State Management

- **Auth State**: Zustand store (minimal, performant)
- **UI State**: Local component state with React hooks
- **Server State**: API responses managed per request

## Backend Architecture

### API Structure

```
/api/v1/
├── /auth/
│   ├── POST register
│   └── POST login
├── /users/
│   ├── GET me (current user)
│   └── GET /{id} (user profile)
└── /memories/
    ├── POST (create)
    ├── GET (list with pagination)
    ├── GET /{id} (get one)
    ├── PUT /{id} (update)
    └── DELETE /{id} (delete)
```

### Layered Architecture

```
Endpoint (route handler)
    ↓ Uses
Schema (Pydantic validation)
    ↓ Uses
Service (business logic - optional)
    ↓ Uses
Model (SQLAlchemy ORM)
    ↓ Uses
Database (PostgreSQL)
```

### Dependency Injection

- **`get_current_user`**: Validates JWT, returns authenticated user
- **`get_db`**: Provides SQLAlchemy session
- Stack these to require authentication + db access

### Database Models

**Users Table**
```
id (PK)
email (unique, indexed)
username (unique, indexed)
hashed_password
full_name
is_active
created_at
updated_at
```

**Memories Table**
```
id (PK)
user_id (indexed, FK to users)
title
content
tags (comma-separated, searchable)
source (file, manual, api, etc.)
is_archived (indexed, filterable)
created_at (indexed for sorting)
updated_at
```

## Authentication Flow

### Registration
```
1. User fills form → /register
2. Validate email, username unique
3. Hash password with bcrypt
4. Create user record
5. Redirect to login
```

### Login
```
1. User enters email + password → /login
2. Query user by email
3. Verify password hash
4. Generate JWT token
5. Return token to client
6. Client stores in cookie
7. Redirect to dashboard
```

### Protected Routes
```
1. Client sends token in Authorization header
2. Server validates token
3. Extract user_id from claims
4. Load user from database
5. Allow request if user is active
6. Return 401 if token invalid/expired
```

## Security Measures

### Password
- Hashed with bcrypt (cost factor 12)
- Never stored in plain text

### JWT Token
- Signed with SECRET_KEY
- Includes user_id as subject
- Expires after 30 minutes (configurable)
- Stored in HttpOnly cookies (frontend)

### Database
- User queries by primary key (efficient)
- Indexed on frequently queried fields
- SQL injection prevented by ORM

### CORS
- Whitelist frontend origin
- Credentials allowed for cookie auth
- Preflight requests handled

## Scaling Considerations

### Frontend
- **Caching**: Next.js automatic caching
- **Code splitting**: Per-route code splitting
- **Image optimization**: Next.js Image component ready
- **Deployment**: Vercel, self-hosted Node.js

### Backend
- **Database**: Connection pooling configured
- **Async support**: FastAPI native async/await
- **Load balancing**: Stateless design (JWT auth)
- **Caching**: Redis ready (add to requirements)
- **Pagination**: Implemented for list endpoints

### Horizontal Scaling
- Stateless architecture (no server sessions)
- JWT tokens valid across instances
- PostgreSQL as central data store
- Ready for multiple backend instances

## Development Workflow

### Add New Endpoint

**Backend:**
1. Define Pydantic schema in `schemas/schemas.py`
2. Add SQLAlchemy model if needed in `models/models.py`
3. Create endpoint function in `api/v1/endpoints/`
4. Include router in `api/v1/__init__.py`

**Frontend:**
1. Create service function in `services/`
2. Create custom hook in `hooks/`
3. Create component in `components/`
4. Add page/route in `app/`

### Testing Endpoints
1. Backend: FastAPI docs at `http://localhost:8000/docs`
2. Frontend: Direct API calls via browser dev tools

## Production Deployment

### Backend
```bash
# Environment
export DATABASE_URL=production_db_url
export SECRET_KEY=strong_random_key_32_chars
export ENVIRONMENT=production
export DEBUG=False

# Run
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

### Frontend
```bash
npm run build
export NEXT_PUBLIC_API_URL=https://api.example.com
npm start
```

### Infrastructure
- PostgreSQL on managed service (RDS, Neon, etc.)
- Backend on container platform (Docker, K8s, ECS)
- Frontend on CDN (Vercel, Cloudflare, S3+CloudFront)
- Monitoring & logging (DataDog, New Relic, etc.)

## File Organization Rationale

### Why This Structure?

**Frontend**
- App directory for modern routing
- Route groups `(auth)`, `(dashboard)` for layout reuse
- Services layer separates API logic from components
- Zustand for minimal state (avoids prop drilling)
- Middleware for auth protection

**Backend**
- API versioning (`v1/`) for backward compatibility
- Endpoint grouping by domain (auth, users, memories)
- Schemas for validation (contract-first)
- Models for persistence (single source of truth)
- Dependencies for auth (composable, testable)

Both follow **Clean Architecture** principles:
- ✅ Independent of frameworks
- ✅ Testable (dependencies injectable)
- ✅ Scalable (modular structure)
- ✅ Maintainable (clear responsibilities)
