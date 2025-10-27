# Agentic SQL Execution Implementation

## Overview

This document describes the new agentic execution flow for SQL query generation and execution with automatic error recovery.

## Architecture

The system now follows a 5-stage pipeline:

1. **Validation Stage** (Haiku 4) - Validates if the question is relevant to available databases
2. **Decision Stage** (Sonnet 4.5) - Decides what action to take
3. **Planning Stage** (Sonnet 4.5) - Creates a step-by-step query plan
4. **Execution Stage** (Sonnet 4.5) - **NEW** - Executes each step with agentic retry
5. **Summary Stage** (Sonnet 4.5) - **NEW** - Generates final answer from results

## New Components

### 1. Pydantic Schemas (`app/llm/schemas.py`)

Added four new schemas:

- **SQLGenerationResult**: Contains generated SQL, reasoning, and target database
- **ErrorAnalysisResult**: Analyzes if error is recoverable and provides corrected SQL
- **StepExecutionResult**: Stores execution result (data/value/error) for each step
- **SummaryResult**: Final answer with confidence level and data sources used

### 2. Prompt Templates (`knowledge/prompts/`)

Created three new YAML templates:

- **generate_sql.yaml**: Generates PostgreSQL SQL for a plan step
  - Takes: question, step details, previous results, database schemas
  - Returns: SQL query with reasoning

- **analyze_error.yaml**: Analyzes SQL execution errors
  - Takes: failed SQL, error message, previous attempts
  - Returns: Error type, recoverability, suggested fix
  - Error types: syntax, schema, permission, connection, data, other

- **write_summary.yaml**: Generates final user-facing answer
  - Takes: question, plan summary, all execution results
  - Returns: Natural language answer in user's language
  - Includes confidence level (high/medium/low)

### 3. Step Executor (`app/llm/executor.py`)

The `StepExecutor` class implements the agentic execution loop:

**Key Features:**
- Loads all database schemas from YAML files
- Executes query plan steps sequentially
- For each step:
  - Generates SQL using LLM
  - Executes via datasource manager
  - On error: analyzes and retries up to 5 times
  - On success: stores result (CSV-like or single value)
- Passes previous step results to subsequent steps
- Generates final summary from all results

**Retry Logic:**
```
Attempt 1: Generate SQL → Execute
  ↓ (if error)
Attempt 2: Analyze error → Generate fixed SQL → Execute
  ↓ (if error)
Attempt 3: Analyze error → Generate fixed SQL → Execute
  ↓ (if error)
...up to 5 attempts

If error is marked as non-recoverable (connection, permission), stop immediately
If 5 attempts fail, return error to user
```

**Result Types:**
- **Single value**: COUNT, SUM, single record (stored in `result_value`)
- **Dataset**: Multiple rows/columns (stored in `result_data`)

### 4. Updated Orchestrator (`app/llm/orchestrator.py`)

The orchestrator now includes execution and summary stages:

**Old flow:**
```
Validation → Decision → Planning → Return plan text
```

**New flow:**
```
Validation → Decision → Planning → Execution (with retry) → Summary → Return answer
```

**New response types:**
- `execution_error`: Step execution failed after retries
- `answer`: Successful execution with final answer

## Error Recovery Strategy

The system categorizes errors and handles them intelligently:

### Recoverable Errors
- **Syntax errors**: Missing commas, wrong keywords → Fix SQL syntax
- **Schema errors**: Wrong table/column name → Use correct schema reference
- **Data errors**: Type mismatches, NULL handling → Add casts, NULL checks

### Non-Recoverable Errors
- **Connection errors**: Database unavailable, timeout
- **Permission errors**: Access denied, insufficient privileges
- **Resource errors**: Out of memory, disk full

## Data Flow

### Step Execution
```python
{
  "step_number": 1,
  "success": true,
  "sql": "SELECT COUNT(*) as total FROM customer_db.public.customers",
  "result_value": "1500",  # Single value
  "attempts": 1
}
```

### Execution with Dataset
```python
{
  "step_number": 2,
  "success": true,
  "sql": "SELECT customer_id, name FROM customer_db.public.customers LIMIT 10",
  "result_data": [
    {"customer_id": "C001", "name": "John Doe"},
    {"customer_id": "C002", "name": "Jane Smith"},
    ...
  ],
  "attempts": 1
}
```

### Failed Execution
```python
{
  "step_number": 3,
  "success": false,
  "sql": "SELECT * FROM wrong_table",
  "error": "Non-recoverable error (schema): Table 'wrong_table' does not exist and no similar table found",
  "attempts": 3
}
```

## Token Tracking

All LLM interactions are tracked:
- SQL generation attempts
- Error analysis attempts
- Summary generation
- Total pipeline time

Token usage is aggregated at thread level and displayed in the UI.

## Testing

### 1. Start Backend
```bash
cd backend
# Ensure .env is configured with ANTHROPIC_API_KEY
uv run uvicorn main:app --host 0.0.0.0 --port 5001 --reload
```

### 2. Test Questions

**Simple question (single step):**
```
"How many customers do we have?"
```
Expected: Single COUNT query, immediate answer

**Complex question (multiple steps):**
```
"Show me the top 5 customers by account balance"
```
Expected: JOIN across customer_db and accounts_db, aggregate, sort

**Question requiring retry:**
```
"What's the average loan amount?"
```
Expected: May require retry if wrong table name used initially

### 3. Monitor Debug Logs

With `LLM_DEBUG=true`, you'll see:
```
INFO - Generating SQL for step 1
DEBUG - Generated SQL: SELECT COUNT(*) ...
INFO - Step 1 executed successfully on attempt 1
WARNING - Step 2 failed on attempt 1: table not found
INFO - Retrying step 2 with corrected SQL (attempt 2)
INFO - Step 2 executed successfully on attempt 2
```

### 4. Check API Response

The response now includes:
```json
{
  "type": "answer",
  "message": "We have 1,500 active customers in the database...",
  "metadata": {
    "plan": {...},
    "execution_results": [...],
    "summary": {
      "answer": "...",
      "confidence": "high",
      "data_sources_used": ["customer_db"]
    },
    "debug_info": [...]
  }
}
```

## Configuration

### Environment Variables

Required:
- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `ANTHROPIC_DEVELOPER_MODEL`: Model for SQL generation (default: claude-sonnet-4-5-20250929)

Optional:
- `LLM_DEBUG=true`: Enable detailed execution logging
- PostgreSQL connection details (if connecting to real database)

### Retry Configuration

In `app/llm/executor.py`:
```python
MAX_RETRY_ATTEMPTS = 5  # Maximum SQL generation attempts per step
```

## Language Support

The system maintains language consistency:
- Prompts detect user's language from question
- All responses (SQL reasoning, error messages, summary) use same language
- Supports: English, Hungarian, German, and others

## Performance Considerations

1. **Schema Loading**: Database schemas are loaded once at executor initialization
2. **Token Usage**:
   - Simple queries: ~3,000-5,000 tokens
   - Complex multi-step: ~10,000-20,000 tokens
   - With retries: +2,000-3,000 tokens per retry
3. **Execution Time**:
   - Validation + Decision: ~500-1000ms
   - Planning: ~1000-2000ms
   - Per step execution: ~1000-3000ms
   - Summary: ~1000-2000ms

## Future Enhancements

Potential improvements:
1. **Parallel execution**: Execute independent steps in parallel
2. **Result caching**: Cache frequently used query results
3. **Query optimization**: Analyze and optimize generated SQL
4. **Custom retry strategies**: Different retry limits per error type
5. **Incremental results**: Stream results as steps complete
6. **SQL validation**: Pre-validate SQL syntax before execution

## Troubleshooting

### Issue: All steps fail with "connection" error
**Solution**: Check datasource configuration in `knowledge/datasources.yaml` and `.env`

### Issue: SQL generation produces wrong syntax
**Solution**: Verify database schemas in `knowledge/data_schemas/*.yaml` are accurate

### Issue: Token limits exceeded
**Solution**: Increase `ANTHROPIC_MAX_TOKENS` or simplify question

### Issue: Steps succeed but summary is generic
**Solution**: Check if result data is properly formatted in execution results

## Code References

Key implementation files:
- `backend/app/llm/executor.py` - Main execution logic
- `backend/app/llm/orchestrator.py:167-221` - Integration point
- `backend/app/llm/schemas.py:61-107` - New schemas
- `backend/knowledge/prompts/generate_sql.yaml` - SQL generation
- `backend/knowledge/prompts/analyze_error.yaml` - Error recovery
- `backend/knowledge/prompts/write_summary.yaml` - Answer generation
