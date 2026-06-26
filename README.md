# MemoryOS

An AI-powered personal knowledge operating system that turns your documents into an intelligent, self-organizing second brain.

Upload PDFs, DOCX, text files, images, bookmarks, and Markdown. MemoryOS automatically extracts text, detects document types, generates semantic embeddings, builds knowledge graphs, and helps you rediscover and connect ideas — all running locally with no cloud AI APIs.

---

## Why MemoryOS?

| Problem | Solution |
|---------|----------|
| "I saved a PDF but can't find it" | **Semantic search** — search by meaning, not just keywords |
| "I have 500 files scattered everywhere" | **Centralized memory library** with auto-processing and tagging |
| "I forgot about documents from months ago" | **Forgotten Memories** tracker alerts you to inactive documents |
| "I can't see how my notes connect" | **Knowledge Graph** visualization of document relationships |
| "Organizing files manually is tedious" | **AI Collection Suggestions** based on your content |
| "I don't know what I've been learning" | **Knowledge Evolution** tracker with learning streaks and milestones |
| "Note-taking apps don't understand my files" | **Document Intelligence V5** with type-aware extraction |
| "I need answers, not just search" | **Knowledge Assistant** — ask natural-language questions |

---

## Key Features

### Document Intelligence V5

Unlike simple keyword extractors, MemoryOS **understands** your documents:

- **10+ Document Types** — Resume, Research Paper, Study Material, Certificate, Documentation, Book, Cheat Sheet, Tutorial, Lecture Notes
- **Semantic Concept Extraction** — sentence-transformers embeddings for concept deduplication
- **Concept Graph** — parent-child relationships where only meaningful concepts become topics
- **Type-Aware Summaries** — resumes explain who/skills, papers explain problem/method, study materials explain subject/concepts
- **Confidence Validation** — output quality loop ensures another person would understand the summary

### 100% Local AI

No data leaves your machine. No OpenAI, Claude, or Gemini API calls.

- **Sentence Transformers** (`all-MiniLM-L6-v2`) for semantic embeddings
- **ChromaDB** for local vector storage
- **scikit-learn** for clustering and similarity
- **networkx** for concept graph construction

### Semantic Search & Knowledge Assistant

Search by meaning, not keywords. The Knowledge Assistant answers natural-language questions by retrieving from metadata, collections, tags, topics, keywords, and semantic embeddings.

### Knowledge Graph

Interactive visualization connecting Memories, Topics, and Collections with force-directed layout, auto-zoom, search highlighting, and cluster detection.

### Smart Collections

AI-powered groupings, bulk operations, rename/merge suggestions, and per-collection intelligence views.

### Timeline & Gamification

Learning streaks, achievement milestones, monthly knowledge evolution, and forgotten memory alerts.

### Security

JWT authentication, CSRF protection, rate limiting, Argon2 password hashing, structured security logging.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, Zustand |
| Backend | FastAPI, SQLAlchemy, Pydantic |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Vector DB | ChromaDB (persistent local storage) |
| AI/ML | Sentence Transformers, scikit-learn, networkx |
| Auth | JWT (HS256) + Argon2/bcrypt + CSRF + Rate Limiting |

---

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.10+
- pip

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn main:app --reload
```

Open [http://localhost:8000/docs](http://localhost:8000/docs) for the API documentation.

---

## API

All endpoints are under `/api/v1/` and require JWT authentication.

| Module | Key Endpoints |
|--------|---------------|
| Auth | `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout` |
| Users | `GET /users/me`, `PUT /users/me`, `POST /users/me/avatar` |
| Memories | `POST /memories/upload`, `GET /memories`, `GET /memories/{id}` |
| Search | `POST /embeddings/search`, `GET /memories/semantic/search` |
| Collections | CRUD + membership, suggestions, smart collections, bulk ops |
| Graph | `GET /graph`, `GET /graph/nodes`, `GET /graph/edges` |
| Timeline | `GET /timeline/events`, `GET /timeline/achievements`, `GET /timeline/streak` |
| Insights | `GET /insights/dashboard` |
| Q&A | `POST /qa/ask`, `GET /qa/suggested-questions` |

---

## Architecture

```
Upload → File Router → Processor (PDF/DOCX/Text/MD/Image/Bookmark)
  → Text Extraction → Document Classification (10+ types)
  → Named Entity Recognition → Semantic Concept Extraction
  → Concept Graph Building (networkx) → Topic Ranking (7-factor scoring)
  → Type-Aware Summary Generation → Confidence Validation Loop
  → Embedding → ChromaDB Storage → Collection Suggestion
  → Timeline Event → Knowledge Graph Update
```

### Database Schema

| Table | Purpose |
|-------|---------|
| `users` | User accounts with auth |
| `memories` | Uploaded files metadata |
| `processed_documents` | Extracted text, topics, concepts, summaries |
| `collections` | User-created collections |
| `collection_memberships` | Memory-collection links |
| `timeline_events` | Activity timeline |
| `milestones` | Achievement tracking |

---

## License

[MIT](LICENSE)
