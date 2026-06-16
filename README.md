# MemoryOS

A production-grade SaaS for AI-powered personal knowledge management.

## Project Structure

```
MemoryOS/
├── frontend/              # Next.js + TypeScript + Tailwind
│   ├── src/
│   │   ├── app/          # Routes & layouts
│   │   ├── components/   # React components
│   │   ├── services/     # API clients
│   │   ├── hooks/        # Custom hooks
│   │   ├── context/      # State management
│   │   ├── types/        # TypeScript types
│   │   └── middleware.ts # Auth middleware
│   ├── package.json
│   ├── tsconfig.json
│   └── README.md
│
├── backend/               # FastAPI + PostgreSQL
│   ├── app/
│   │   ├── api/          # Endpoints (auth, users, memories)
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Validation schemas
│   │   ├── core/         # Config & security
│   │   ├── db/           # Database session
│   │   └── middleware/   # CORS, etc.
│   ├── main.py           # FastAPI app
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
└── README.md             # This file
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, Shadcn |
| Backend | FastAPI, SQLAlchemy, Pydantic |
| Database | PostgreSQL |
| Auth | JWT + Passlib |
| State | Zustand (frontend), Pydantic (backend) |

## Quick Start

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
# http://localhost:3000
```

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn main:app --reload
# http://localhost:8000/docs
```

## Architecture Principles

### Clean Architecture
- **Separation of Concerns**: Routes → Schemas → Services → Models
- **Dependency Injection**: FastAPI dependencies for auth & db
- **Middleware**: CORS, error handling, logging

### Security
- JWT token-based authentication
- Password hashing with bcrypt
- Protected routes via middleware (frontend) & dependencies (backend)
- Environment-based configuration

### Scalability
- Modular API structure with versioning (`/api/v1/`)
- Pagination support for list endpoints
- Database indexing on frequently queried fields
- Ready for horizontal scaling with Postgres

### Developer Experience
- TypeScript for type safety (frontend & backend config)
- Comprehensive documentation
- Example .env files
- Clear folder structure

## Features

### Authentication
- User registration with validation
- Login with JWT token
- Protected routes
- Token refresh mechanism ready

### Dashboard
- Overview of user's memories
- Quick stats

### Upload
- Add new memories/knowledge
- Tag organization

### Search
- Full-text search (to implement)
- Filter and sort

### Profile
- User settings
- Account management

## API Routes

All routes require JWT token in `Authorization: Bearer <token>` header

```
POST   /api/v1/auth/register        # Register
POST   /api/v1/auth/login           # Login
GET    /api/v1/users/me             # Current user
GET    /api/v1/memories             # List memories
POST   /api/v1/memories             # Create memory
GET    /api/v1/memories/{id}        # Get memory
PUT    /api/v1/memories/{id}        # Update memory
DELETE /api/v1/memories/{id}        # Delete memory
```

## Environment Variables

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### Backend (.env)
```
DATABASE_URL=postgresql://user:password@localhost:5432/memoryos
SECRET_KEY=your-secret-key-min-32-chars
CORS_ORIGINS=http://localhost:3000
```

## Next Steps for Development

1. **Set up Alembic** for database migrations
2. **Implement forms** with React Hook Form + Zod
3. **Add Shadcn UI components** as needed
4. **Implement search** with Postgres full-text search or Elasticsearch
5. **Add file upload** with multipart/form-data
6. **Integrate AI** for knowledge extraction
7. **Add logging** and monitoring
8. **Deploy** to production

## Production Checklist

- [ ] Replace SECRET_KEY with strong random value
- [ ] Set up PostgreSQL with backups
- [ ] Configure CORS properly
- [ ] Enable HTTPS
- [ ] Set up CI/CD pipeline
- [ ] Add rate limiting
- [ ] Add caching (Redis)
- [ ] Set up monitoring/logging
- [ ] Database connection pooling
- [ ] Environment-specific configurations

## Development Workflow

1. Start backend: `python -m uvicorn main:app --reload`
2. Start frontend: `npm run dev`
3. Access frontend at `http://localhost:3000`
4. API docs at `http://localhost:8000/docs`
5. Make changes and test in browser

## Contributing

- Follow clean architecture principles
- Use TypeScript throughout
- Add environment validation
- Keep components small and reusable
- Document complex logic

## License

MIT
