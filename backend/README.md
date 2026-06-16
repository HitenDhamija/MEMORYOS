# MemoryOS - Backend

AI-powered personal knowledge operating system. Built with FastAPI, PostgreSQL, and JWT authentication.

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL + SQLAlchemy ORM
- **Authentication**: JWT + Passlib
- **Validation**: Pydantic
- **Server**: Uvicorn
- **Migrations**: Alembic

## Project Structure

```
app/
├── api/
│   ├── v1/
│   │   ├── endpoints/
│   │   │   ├── auth.py       # Authentication endpoints
│   │   │   ├── users.py      # User profile endpoints
│   │   │   └── memories.py   # Memory CRUD endpoints
│   │   └── __init__.py       # Route aggregation
│   └── deps.py               # Dependencies (auth, db)
├── models/
│   └── models.py             # SQLAlchemy ORM models
├── schemas/
│   └── schemas.py            # Pydantic request/response schemas
├── services/                 # Business logic (optional)
├── core/
│   ├── config.py             # Settings from env
│   └── security.py           # JWT & password utils
├── db/
│   └── session.py            # Database session
├── middleware/
│   └── cors.py               # CORS configuration
├── utils/                    # Helper functions
└── __init__.py
main.py                        # FastAPI application entry
```

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 12+
- pip or Poetry

### Installation

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Update database and JWT settings:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/memoryos
SECRET_KEY=your-secret-key-change-in-production
CORS_ORIGINS=http://localhost:3000
```

### Database Setup

```bash
# Create database
createdb memoryos

# Run migrations (when Alembic is set up)
alembic upgrade head
```

### Running

```bash
# Development
python -m uvicorn main:app --reload

# Production
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Visit http://localhost:8000/docs for API documentation (Swagger UI)

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get token

### Users
- `GET /api/v1/users/me` - Get current user
- `GET /api/v1/users/{user_id}` - Get user by ID

### Memories
- `POST /api/v1/memories` - Create memory
- `GET /api/v1/memories` - List user's memories (paginated)
- `GET /api/v1/memories/{memory_id}` - Get specific memory
- `PUT /api/v1/memories/{memory_id}` - Update memory
- `DELETE /api/v1/memories/{memory_id}` - Delete memory

## Authentication Flow

1. User calls `/auth/register` → User created with hashed password
2. User calls `/auth/login` → JWT token returned
3. Client sends token in `Authorization: Bearer <token>` header
4. Server validates token via `get_current_user` dependency
5. Protected endpoints require valid token

## Database Models

### User
- id, email, username, full_name, hashed_password
- is_active, created_at, updated_at

### Memory
- id, user_id, title, content, tags, source
- is_archived, created_at, updated_at

## Key Features

### Security
- Password hashing with bcrypt
- JWT token-based authentication
- CORS protection
- Protected routes

### Scalability
- Modular endpoint structure
- Separate schemas and models
- Dependency injection
- Middleware support

### Best Practices
- Environment configuration
- Request validation
- Error handling
- Pagination support

## Development

### Adding New Endpoints

1. Create schema in `app/schemas/schemas.py`
2. Create model in `app/models/models.py`
3. Create route in `app/api/v1/endpoints/`
4. Include router in `app/api/v1/__init__.py`

### Testing

```bash
pytest tests/
```

## Next Steps

1. Set up Alembic migrations
2. Add file upload endpoints
3. Implement search functionality
4. Add AI/embedding features
5. Implement logging and monitoring
6. Add rate limiting
7. Add caching (Redis)
