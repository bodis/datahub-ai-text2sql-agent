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

### LLM Query Planning System
**AI-Powered Data Analysis**: Multi-stage LLM orchestration for natural language to SQL
- **Multi-Model Support**:
  - Weak model (Haiku 4): Fast validation tasks
  - Planning model (Sonnet 4.5): Query planning and decision making
  - Developer model (Sonnet 4.5): SQL generation
- **LLM Client**: Anthropic Claude with structured outputs using tool use
- **Prompt Templates**: YAML-based templates with model selection
- **Orchestrator**: Three-stage pipeline (validate → decide → plan)
- **Structured Outputs**: Pydantic schemas for type-safe LLM responses
- **Token Tracking**: Per-thread token usage tracking and display
- **Debug Logging**: Comprehensive logging of all LLM interactions
- **Language Consistency**: Responses always match user's language

### Backend Structure
```
backend/
  app/
    __init__.py      # Flask app factory & initialization
    storage.py       # Storage abstraction layer (ABC interface)
    routes.py        # API endpoints
    llm/
      client.py      # Anthropic Claude client with structured output
      schemas.py     # Pydantic models for LLM responses
      prompts.py     # Prompt template loader
      orchestrator.py # Multi-stage query planning orchestrator
    datasources/
      base.py        # Abstract datasource interface
      postgresql.py  # PostgreSQL implementation (psycopg3)
      manager.py     # Datasource manager and routing
  knowledge/
    data_schemas/    # Database schema YAMLs and documentation
    prompts/         # LLM prompt templates (YAML)
    docs/            # Documentation (datasources, schema_usage)
    datasources.yaml # Datasource connection configurations
  run.py             # Entry point
  main.py            # ASGI app for uvicorn
  .env              # Environment config (ANTHROPIC_API_KEY, POSTGRES_*)
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
- `POST /api/threads/:id/messages` - Send message (uses LLM orchestrator)
- `GET /api/threads/:id/tokens` - Get token usage for thread
- `GET /api/data-sources` - Get available data sources

## Development Commands

**Backend**
```bash
cd backend
cp .env.example .env                               # Create .env file
# Edit .env and configure:
#   ANTHROPIC_API_KEY - Your API key
#   ANTHROPIC_WEAK_MODEL - Haiku for fast tasks
#   ANTHROPIC_PLANNING_MODEL - Sonnet for planning
#   ANTHROPIC_DEVELOPER_MODEL - Sonnet for SQL generation
#   LLM_DEBUG=true - Enable debug logging
uv sync                                            # Install deps
uv run uvicorn main:app --host 0.0.0.0 --port 5001 --reload  # Run server
```

**Frontend**
```bash
cd frontend
npm install    # Install deps
npm run dev    # Run dev server
```

## LLM Query Planning Flow

1. **Validation Stage** (`validate_question.yaml` - uses weak model)
   - Checks if question is relevant to available databases
   - Uses `summary.yaml` for quick data source lookup
   - Returns `ValidationResult` with relevant databases
   - Tracks input/output tokens

2. **Decision Stage** (`decide_action.yaml` - uses planning model)
   - Decides: ask_clarification, create_plan, answer_directly, or reject
   - Based on question clarity and context
   - Returns `DecisionResult` with action and reasoning
   - Tracks input/output tokens

3. **Planning Stage** (`create_plan.yaml` - uses planning model)
   - Creates step-by-step SQL query plan
   - Identifies tables, joins, and operations needed
   - Returns `QueryPlan` with executable steps
   - Tracks input/output tokens

**Token Tracking**: All token usage is aggregated at thread level and displayed in UI

## Extension Points

1. **New Storage Backend**: Implement `StorageInterface` in storage.py
2. **New API Endpoints**: Add routes to routes.py
3. **New UI Components**: Add to frontend/src/components/
4. **New LLM Prompts**: Add YAML templates to knowledge/prompts/
5. **New Structured Outputs**: Add Pydantic models to app/llm/schemas.py

## Key Files to Know

**Backend Core**
- `backend/app/storage.py` - Storage layer (all DB operations)
- `backend/app/routes.py` - All API endpoints
- `backend/app/llm/orchestrator.py` - LLM query planning flow
- `backend/app/llm/client.py` - Claude API client with structured outputs

**Knowledge Base**
- `backend/knowledge/data_schemas/summary.yaml` - Data source descriptions
- `backend/knowledge/data_schemas/knowledge.md` - Detailed DB documentation
- `backend/knowledge/prompts/*.yaml` - LLM prompt templates

**Frontend**
- `frontend/src/lib/api.ts` - Backend API client
- `frontend/src/components/ChatInterface.tsx` - Main chat UI
- `frontend/src/components/DataSourceBadges.tsx` - Data source display
- `frontend/src/components/TokenDisplay.tsx` - Token usage display

## Datasource Management

**Flexible Multi-Database Architecture**:
- Abstract datasource interface for extensibility
- PostgreSQL implementation with connection pooling (psycopg3)
- Logical database mapping (customer_db, accounts_db, etc. → PostgreSQL schemas)
- Cross-datasource query validation
- Environment-based configuration

**Configuration**:
- `datasources.yaml`: Physical datasource definitions
- `summary.yaml`: Logical DB to datasource mapping
- `.env`: Connection credentials

## Current State
- In-memory chat storage (data lost on restart)
- LLM-powered query understanding and planning
- Multi-model support (Haiku 4 + Sonnet 4.5) with model selection per prompt
- Structured outputs using Anthropic tool use
- Multi-stage orchestration (validate → decide → plan)
- Comprehensive debug logging of all LLM interactions
- Token tracking per thread with real-time UI display
- Language consistency (responses match user's language)
- Datasource management with PostgreSQL support
- 6 database schemas available (customer, accounts, loans, insurance, compliance, employees)
- Cross-datasource query validation
- SQL execution not yet implemented (infrastructure ready)

**Note**: Always ensure `.env` is properly configured before running backend. Use `.env.example` as template.

## Features Implemented

✅ Multi-model configuration (weak/planning/developer)
✅ Token tracking and aggregation per thread
✅ Debug logging for all LLM communications
✅ Model selection in prompt templates
✅ Language consistency across responses
✅ Real-time token display in UI
✅ Comprehensive error handling with traceback logging
✅ Datasource abstraction layer
✅ PostgreSQL implementation with connection pooling
✅ Cross-datasource query validation
✅ Logical database to physical datasource mapping

## Important Implementation Details

### Environment Configuration
- `.env.example` provides template with all required variables
- Required: `ANTHROPIC_API_KEY` for LLM functionality
- Optional: `LLM_DEBUG=true` for detailed logging of all LLM interactions
- PostgreSQL credentials required only if connecting to actual databases

### Token Tracking
- All LLM calls track input/output tokens via `usage` object in API response
- Tokens aggregated at thread level in storage layer
- Frontend fetches token data via `GET /api/threads/:id/tokens`
- TokenDisplay component shows real-time usage

### Model Selection
- Prompt templates specify which model to use via `model` field in YAML
- Three model types: weak (Haiku), planning (Sonnet), developer (Sonnet)
- Client automatically selects correct model based on prompt template

### Error Handling
- All LLM errors caught and logged with full traceback
- Structured error responses returned to frontend
- Debug mode prints all prompts, responses, and token usage
