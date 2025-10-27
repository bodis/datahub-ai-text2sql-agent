# Project Context for Claude

## Overview
Chat thread application with Flask backend and React frontend. Designed as a foundational architecture for future feature expansion.

## Tech Stack

**Backend**
- Flask 3.0+ (Python 3.10+)
- Flask-CORS for cross-origin requests
- uv package manager
- Runs on port 5001

**Frontend**
- React 18 + TypeScript
- Vite build tool
- Tailwind CSS + shadcn/ui components
- Runs on port 3001

## Architecture Principles

### Storage Abstraction
**Critical Pattern**: All data access goes through `StorageInterface` (backend/app/storage.py)
- Current: `InMemoryStorage` implementation
- Design: Easy swap to PostgreSQL/Redis/etc by implementing same interface
- Methods: `create_thread`, `get_thread`, `get_all_threads`, `add_message`, `get_messages`

### Backend Structure
```
backend/
  app/
    __init__.py      # Flask app factory & initialization
    storage.py       # Storage abstraction layer (ABC interface)
    routes.py        # API endpoints
  run.py             # Entry point
  main.py            # ASGI app for uvicorn
  pyproject.toml     # Dependencies
```

### Frontend Structure
```
frontend/src/
  components/
    ChatInterface.tsx  # Main chat UI
    ThreadList.tsx     # Thread sidebar
    ui/               # shadcn/ui primitives
  lib/
    api.ts            # Backend API client
    utils.ts          # Utility functions
  App.tsx             # Root component
```

## API Endpoints
- `GET /api/threads` - List all threads
- `POST /api/threads` - Create thread (body: `{name}`)
- `GET /api/threads/:id` - Get thread details
- `GET /api/threads/:id/messages` - Get thread messages
- `POST /api/threads/:id/messages` - Send message (body: `{content, sender}`)

## Development Commands

**Backend**
```bash
cd backend
uv sync                                            # Install deps
uv run uvicorn main:app --host 0.0.0.0 --port 5001 --reload  # Run server
```

**Frontend**
```bash
cd frontend
npm install    # Install deps
npm run dev    # Run dev server
```

## Extension Points

1. **New Storage Backend**: Implement `StorageInterface` in storage.py
2. **New API Endpoints**: Add routes to routes.py
3. **New UI Components**: Add to frontend/src/components/
4. **New Features**: Follow existing separation of concerns pattern

## Key Files to Know
- `backend/app/storage.py` - Storage layer (all DB operations)
- `backend/app/routes.py` - All API endpoints
- `frontend/src/lib/api.ts` - Frontend API client
- `frontend/src/components/ChatInterface.tsx` - Main chat UI

## Current State
- In-memory storage (data lost on restart)
- Basic thread and message CRUD
- Simple echo-back messaging
- No auth, no persistence, no real-time updates yet
