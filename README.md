# Chat Thread Application

A simple chat application with thread management built with Flask (Python) and React (TypeScript).

## Features

- Create and manage multiple chat threads
- Real-time messaging within threads
- In-memory storage with abstraction layer for easy migration
- Clean separation between backend and frontend
- Modern UI with shadcn/ui components

## Project Structure

```
.
├── backend/                 # Flask API backend
│   ├── app/
│   │   ├── __init__.py     # Flask app factory
│   │   ├── storage.py      # Storage abstraction layer
│   │   └── routes.py       # API endpoints
│   ├── run.py              # Application entry point
│   └── pyproject.toml      # Python dependencies (uv)
│
└── frontend/               # React frontend
    ├── src/
    │   ├── components/     # React components
    │   ├── lib/           # Utilities and API client
    │   ├── App.tsx        # Main application component
    │   └── main.tsx       # Application entry point
    ├── package.json       # Node dependencies
    └── vite.config.ts     # Vite configuration
```

## Backend Architecture

### Storage Layer
The backend uses an abstract storage interface (`StorageInterface`) with an in-memory implementation (`InMemoryStorage`). This design allows easy migration to other storage systems (PostgreSQL, Redis, etc.) by implementing the same interface.

### API Endpoints

- `GET /api/threads` - Get all threads
- `POST /api/threads` - Create a new thread
- `GET /api/threads/:id` - Get a specific thread
- `GET /api/threads/:id/messages` - Get messages for a thread
- `POST /api/threads/:id/messages` - Send a message (server echoes back)

## Prerequisites

- Python 3.10+
- Node.js 18+
- [uv](https://github.com/astral-sh/uv) - Python package manager

### Installing uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Setup and Installation

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Run the server (choose one):

**Option A: Uvicorn (recommended)**
```bash
uv run uvicorn main:app --host 0.0.0.0 --port 5001 --reload
```

**Option B: Flask development server**
```bash
python run.py
```

The backend will start at `http://localhost:5001`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will start at `http://localhost:3001`

## Usage

1. Start both the backend and frontend servers
2. Open your browser to `http://localhost:3001`
3. Click "New Thread" to create a chat thread
4. Type a message and press Enter or click Send
5. The server will echo your message back immediately
6. Create multiple threads and switch between them

## Development

### Backend Development

The backend uses:
- **Flask** - Web framework
- **Flask-CORS** - Cross-Origin Resource Sharing
- **uv** - Fast Python package installer and resolver

To add new dependencies:
```bash
# Edit pyproject.toml, then:
uv pip install -e .
```

### Frontend Development

The frontend uses:
- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **shadcn/ui** - Component library
- **Radix UI** - Headless UI components

To add new dependencies:
```bash
npm install <package-name>
```

## Future Enhancements

- [ ] Replace in-memory storage with persistent database
- [ ] Add user authentication
- [ ] Implement real-time updates with WebSockets
- [ ] Add message editing and deletion
- [ ] Thread search and filtering
- [ ] Message attachments
- [ ] Deploy to production

## License

MIT
