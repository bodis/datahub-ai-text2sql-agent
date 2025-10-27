# Chat API Backend

Flask-based REST API for chat thread management with in-memory storage.

## Installation

```bash
uv sync
```

## Running

### Option 1: With uvicorn (recommended)
```bash
uv run uvicorn main:app --host 0.0.0.0 --port 5001 --reload
```

### Option 2: With Flask development server
```bash
python run.py
```

The API will be available at http://localhost:5001
