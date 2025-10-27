# System Architecture

## Overview

The AI Data Agent follows a modular, pipeline-based architecture with clear separation of concerns between query understanding, planning, execution, and presentation layers.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  ChatUI      │  │  ThreadList  │  │  DataSourceBadges    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/REST API
┌────────────────────────────┴────────────────────────────────────┐
│                      Backend (Flask/Python)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                     API Routes Layer                      │  │
│  │  /threads, /messages, /tokens, /databases, /data-sources │  │
│  └─────────────────────────┬────────────────────────────────┘  │
│                             │                                    │
│  ┌─────────────────────────┴────────────────────────────────┐  │
│  │              Query Orchestrator (Pipeline)                │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │  │
│  │  │Validation│→ │Decision  │→ │Planning  │→ │Execution │ │  │
│  │  │(Haiku 4) │  │(Sonnet)  │  │(Sonnet)  │  │(Sonnet)  │ │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └────┬─────┘ │  │
│  └────────────────────────────────────────────────┼───────┘  │  │
│                                                     │          │  │
│  ┌──────────────────────────────────────────────┼───────┐   │  │
│  │            Step Executor (Agentic Loop)      │       │   │  │
│  │  ┌───────────────┐  ┌───────────────┐      │       │   │  │
│  │  │ SQL Generator │→ │ Error Analyzer│──────┘       │   │  │
│  │  │   (Sonnet)    │  │   (Sonnet)    │  (retry)     │   │  │
│  │  └───────┬───────┘  └───────────────┘              │   │  │
│  └──────────┼──────────────────────────────────────────┘   │  │
│             │                                                │  │
│  ┌──────────┴──────────────────────────────────────────┐   │  │
│  │              Datasource Manager                      │   │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐      │   │  │
│  │  │customer_db │ │accounts_db │ │loans_db    │ ...  │   │  │
│  │  │ _source    │ │ _source    │ │ _source    │      │   │  │
│  │  └─────┬──────┘ └─────┬──────┘ └─────┬──────┘      │   │  │
│  └────────┼──────────────┼──────────────┼─────────────┘   │  │
└───────────┼──────────────┼──────────────┼─────────────────┘
            │              │              │
            ▼              ▼              ▼
  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
  │ PostgreSQL   │ │ PostgreSQL   │ │ PostgreSQL   │
  │ customer_db  │ │ accounts_db  │ │ loans_db     │
  └──────────────┘ └──────────────┘ └──────────────┘
```

---

## Core Components

### 1. Frontend Layer

**Technology:** React 18 + TypeScript + Vite

**Components:**
- **ChatInterface**: Main chat UI with message display
- **ThreadList**: Sidebar for thread management
- **DataSourceBadges**: Visual database usage indicators
- **TokenDisplay**: Real-time token usage display
- **DebugPanel**: Expandable debug information

**State Management:**
- React hooks (useState, useEffect)
- API client for backend communication
- Real-time updates on message changes

### 2. API Layer

**Technology:** Flask 3.0 + ASGI (uvicorn)

**Endpoints:**
```
Threads:
  GET    /api/threads
  POST   /api/threads
  GET    /api/threads/:id
  GET    /api/threads/:id/messages
  POST   /api/threads/:id/messages    ← Main entry point
  GET    /api/threads/:id/tokens
  GET    /api/threads/:id/databases

Data:
  GET    /api/data-sources
```

**Key Routes File:** `backend/app/routes.py`

### 3. Orchestrator Layer

**File:** `backend/app/llm/orchestrator.py`

**Responsibilities:**
- Coordinates the multi-stage pipeline
- Manages conversation history
- Tracks token usage
- Records database usage
- Handles error responses

**Pipeline Stages:**

**Stage 1: Validation (Haiku 4)**
- Determines if question is relevant to available databases
- Identifies which databases are needed
- Returns: `ValidationResult` with relevant_databases list
- Token usage: ~400-600 tokens

**Stage 2: Decision (Sonnet 4.5)**
- Decides what action to take
- Options: answer_directly, ask_clarification, create_plan, reject
- Returns: `DecisionResult` with action and message
- Token usage: ~500-800 tokens

**Stage 3: Planning (Sonnet 4.5)**
- Creates step-by-step execution plan
- Identifies tables, operations, dependencies
- Returns: `QueryPlan` with ordered steps
- Token usage: ~1,000-2,000 tokens

**Stage 4: Execution (Sonnet 4.5)**
- Executes each step with agentic retry
- Generates SQL, executes, analyzes errors, retries
- Returns: List of `StepExecutionResult`
- Token usage: ~1,500-3,000 per step + retries

**Stage 5: Summary (Sonnet 4.5)**
- Synthesizes results into natural language
- Maintains language consistency
- Returns: `SummaryResult` with answer and confidence
- Token usage: ~1,500-3,000 tokens

### 4. Executor Layer

**File:** `backend/app/llm/executor.py`

**Class:** `StepExecutor`

**Agentic Loop per Step:**
```python
for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
    if attempt == 1:
        sql = generate_sql(step, previous_results)
    else:
        sql = corrected_sql_from_analysis

    result = execute_sql(sql, database)

    if result.success:
        return success_result

    if attempt == MAX_RETRY_ATTEMPTS:
        return failure_result

    error_analysis = analyze_error(sql, error, attempt)

    if not error_analysis.is_recoverable:
        return non_recoverable_error

    corrected_sql = error_analysis.suggested_sql
```

**Key Features:**
- Up to 5 retry attempts per step
- Error categorization (syntax, schema, permission, connection, data)
- Context from previous steps
- Graceful failure handling

### 5. LLM Client Layer

**File:** `backend/app/llm/client.py`

**Class:** `ClaudeClient`

**Capabilities:**
- Regular text completion
- Structured output (via Anthropic tool use)
- Model selection (weak/planning/developer)
- Token tracking
- Debug logging (full prompts when enabled)

**Models:**
- **Weak**: Haiku 4 (fast, cheap, validation)
- **Planning**: Sonnet 4.5 (planning, decision)
- **Developer**: Sonnet 4.5 (SQL generation, error analysis)

### 6. Storage Layer

**File:** `backend/app/storage.py`

**Interface:** `StorageInterface` (ABC)

**Implementation:** `InMemoryStorage`

**Data Stores:**
- `threads`: Thread metadata
- `messages`: Message history per thread
- `token_usage`: Token aggregation per thread
- `used_databases`: Database usage tracking per thread

**Methods:**
- Thread: create, get, get_all
- Messages: add, get
- Tokens: add_usage, get_usage
- Databases: add_used_databases, get_used_databases

**Extension Point:** Replace with PostgreSQL/Redis for persistence

### 7. Datasource Layer

**Files:**
- `backend/app/datasources/base.py` - Abstract interface
- `backend/app/datasources/postgresql.py` - PostgreSQL implementation
- `backend/app/datasources/manager.py` - Routing and validation

**Architecture:**
- One datasource per database (6 total)
- Connection pooling (psycopg3)
- Validation prevents cross-datasource queries
- Environment-based configuration

**Datasource Mapping:**
```
customer_db → customer_db_source → PostgreSQL(customer_db)
accounts_db → accounts_db_source → PostgreSQL(accounts_db)
loans_db → loans_db_source → PostgreSQL(loans_db)
insurance_db → insurance_db_source → PostgreSQL(insurance_db)
compliance_db → compliance_db_source → PostgreSQL(compliance_db)
employees_db → employees_db_source → PostgreSQL(employees_db)
```

### 8. Schema Management

**Location:** `backend/knowledge/data_schemas/`

**Files:**
- `summary.yaml` - High-level database descriptions
- `<database>.yaml` - Full schema (tables, columns, types, FKs)

**Usage:**
- Loaded by orchestrator for planning
- Loaded by executor for SQL generation
- Provides complete context for LLM

**Format:**
```yaml
databases:
  customer_db:
    schemas:
      public:
        tables:
          customers:
            description: "Customer information"
            columns:
              - name: customer_id
                type: VARCHAR(50)
                nullable: false
                description: "Unique identifier"
              - name: name
                type: VARCHAR(255)
                nullable: false
```

### 9. Prompt Management

**Location:** `backend/knowledge/prompts/`

**Format:** YAML with template variables

**Structure:**
```yaml
name: prompt_name
description: What this prompt does
model: weak | planning | developer
system_prompt: |
  ${variables} are replaced at runtime
user_prompt: |
  User's question: "${question}"
structured_output: PydanticModel
temperature: 0.3
```

**Prompts:**
- `validate_question.yaml`
- `decide_action.yaml`
- `create_plan.yaml`
- `generate_sql.yaml`
- `analyze_error.yaml`
- `write_summary.yaml`

---

## Data Flow

### Complete Request Flow

```
1. User sends message via frontend

2. Frontend POST /api/threads/:id/messages

3. API routes.py:
   - Adds user message to storage
   - Creates orchestrator
   - Calls orchestrator.process_question()

4. Orchestrator:
   a. Validation → ValidationResult
   b. Track databases → storage.add_used_databases()
   c. Decision → DecisionResult
   d. Planning → QueryPlan
   e. Create executor
   f. Execution → List[StepExecutionResult]
   g. Summary → SummaryResult

5. For each step in execution:
   a. executor._generate_sql() → SQLGenerationResult
   b. datasource_manager.execute_query() → QueryResult
   c. If error:
      - executor._analyze_error() → ErrorAnalysisResult
      - If recoverable: retry with corrected SQL
      - If not: return error
   d. If success: store result, continue to next step

6. Orchestrator returns:
   {
     "type": "answer",
     "message": "Natural language answer...",
     "metadata": {
       "validation": {...},
       "plan": {...},
       "execution_results": [...],
       "summary": {...}
     }
   }

7. API routes.py:
   - Adds server message to storage
   - Returns both user and server messages

8. Frontend:
   - Updates messages list
   - Refreshes database badges
   - Refreshes token display
```

---

## Design Principles

### 1. Modularity
- Each component has a single responsibility
- Clear interfaces between layers
- Easy to extend or replace components

### 2. Abstraction
- Storage interface can be swapped (memory → DB)
- Datasource interface supports multiple DB types
- LLM client abstracts API details

### 3. Composability
- Pipeline stages are independent
- Steps can be reordered or added
- Prompts are externalized in YAML

### 4. Observability
- Token tracking at every stage
- Debug logging with full prompts
- Metadata in every response

### 5. Resilience
- Automatic error recovery
- Graceful degradation
- Clear error messages

---

## Scalability Considerations

### Current Limitations
- In-memory storage (single instance)
- No caching (every query is fresh)
- No connection pooling across instances
- No rate limiting

### Scaling Options

**Horizontal:**
- Add Redis for shared storage
- Load balancer for multiple backend instances
- PostgreSQL for persistent data

**Vertical:**
- Connection pool sizing
- Async execution with queues
- Caching layer (Redis)

**Optimization:**
- Result caching by query hash
- Schema caching (refresh periodically)
- Prompt template caching

---

## Security Considerations

### Current State
- No authentication/authorization
- SQL injection prevention via parameterized queries
- Environment-based credentials
- No rate limiting

### Production Requirements
- [ ] Add authentication (JWT, OAuth)
- [ ] Role-based access control
- [ ] API rate limiting
- [ ] SQL query whitelisting
- [ ] Audit logging
- [ ] Encrypted credentials storage
- [ ] CORS configuration

---

## Extension Points

### Adding New Stages
1. Define Pydantic schema in `schemas.py`
2. Create prompt template in `prompts/`
3. Add method to orchestrator
4. Wire into pipeline

### Adding New Datasources
1. Implement `DataSourceBase` interface
2. Add configuration to `datasources.yaml`
3. Register in manager's `_load_configurations()`

### Adding New Storage
1. Implement `StorageInterface`
2. Update `storage.py` initialization
3. Handle persistence/migration

### Custom Error Handlers
1. Extend error types in `schemas.py`
2. Add handling logic in executor
3. Update `analyze_error.yaml` prompt

---

## Performance Metrics

### Response Times (Typical)
- Validation: 500-800ms
- Decision: 600-1000ms
- Planning: 1000-2000ms
- SQL generation: 1000-2000ms per step
- Error analysis: 800-1500ms per retry
- Summary: 1000-2000ms

### Token Usage (Typical)
- Simple query (1 step): 4,000-6,000 tokens
- Complex query (3 steps): 10,000-20,000 tokens
- With retries: +2,000 per retry

### Database Queries
- Metadata queries: <10ms
- Simple SELECT: 10-100ms
- Complex JOIN: 100-500ms
- Aggregations: 50-200ms

---

## Technology Choices

### Why Flask + ASGI?
- Simple, Pythonic API
- ASGI support for future async features
- Easy to extend with blueprints

### Why Anthropic Claude?
- Excellent structured output support
- Strong reasoning capabilities
- Multiple model tiers for cost optimization

### Why PostgreSQL?
- Industry standard for relational data
- Excellent psycopg3 Python support
- Rich SQL feature set

### Why React + TypeScript?
- Type safety
- Component reusability
- Large ecosystem

### Why YAML for Config?
- Human-readable
- Easy to edit
- Supports comments
- Version control friendly

---

**See Also:**
- [Datasource Architecture](./DATASOURCE_ARCHITECTURE.md)
- [LLM Pipeline](../implementation/AGENTIC_EXECUTION.md)
- [Error Recovery](../implementation/ERROR_RECOVERY.md)
