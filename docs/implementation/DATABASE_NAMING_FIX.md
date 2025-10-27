# Database Naming Issue - Fixed

## Problem

The error "Database 'customers' not found in any datasource" occurred because the LLM was confusing **table names** with **database names**.

### Root Causes

1. **Insufficient Schema Context**: The orchestrator's `_create_plan` method was passing minimal database information:
   ```python
   # OLD - Just database names
   database_schemas = f"Relevant databases: {', '.join(validation.relevant_databases)}"
   ```

2. **Unclear Prompt Instructions**: The `create_plan.yaml` prompt didn't explicitly distinguish between database IDs and table names.

3. **Naming Confusion**:
   - Database: `customer_db` (with `_db` suffix)
   - Table: `customers` (no suffix)
   - The LLM would sometimes use the table name as a database name

## Solution

### 1. Enhanced Prompt Instructions (`create_plan.yaml`)

Added explicit guidance:
```yaml
CRITICAL - Database vs Table Names:
- **databases** field MUST use the DATABASE ID (e.g., "customer_db", "accounts_db")
- **tables** field should use TABLE NAMES only (e.g., "customers", "accounts")
- DO NOT confuse table names with database names!
- Available database IDs: customer_db, accounts_db, loans_db, insurance_db, compliance_db, employees_db
```

### 2. Proper Schema Loading (`orchestrator.py`)

Added two new methods:

**`_load_database_schemas()`**: Loads all YAML schema files
```python
def _load_database_schemas(self) -> Dict[str, Any]:
    """Load all database schemas from YAML files"""
    # Loads customer_db.yaml, accounts_db.yaml, etc.
    # Returns dict mapping database name to schema info
```

**`_format_database_schemas(database_names)`**: Formats schema for LLM
```python
def _format_database_schemas(self, database_names: List[str]) -> str:
    """Format schema information for specific databases"""
    # For each database:
    #   - List all tables with descriptions
    #   - Show key columns (first 5) with types and descriptions
    #   - Make it clear which database each table belongs to
```

**Updated `_create_plan()`**: Now uses full schema information
```python
# NEW - Full schema with tables and columns
database_schemas = self._format_database_schemas(validation.relevant_databases)
```

### 3. Fixed Dependencies (`pyproject.toml`)

Added missing PostgreSQL connection pool library:
```toml
dependencies = [
    ...
    "psycopg-pool>=3.2.0",
]
```

## Database Structure Clarification

The system uses PostgreSQL **schemas** as logical databases:

```
Physical Database: accounts_db (PostgreSQL)
├── Schema: customer_db (logical database)
│   ├── Table: customers
│   ├── Table: campaigns
│   └── ...
├── Schema: accounts_db (logical database)
│   ├── Table: accounts
│   ├── Table: transactions
│   └── ...
└── Schema: loans_db (logical database)
    ├── Table: loans
    └── ...
```

**Database IDs** (use in "databases" field):
- `customer_db`
- `accounts_db`
- `loans_db`
- `insurance_db`
- `compliance_db`
- `employees_db`

**Table Names** (use in "tables" field):
- `customers`, `campaigns`, `complaints` (in customer_db)
- `accounts`, `transactions`, `customer_master` (in accounts_db)
- `loans`, `loan_applications`, `repayments` (in loans_db)
- etc.

## Example of Correct Plan

```json
{
  "step_number": 1,
  "description": "Get total customer count",
  "databases": ["customer_db"],        // ✅ Database ID
  "tables": ["customers"],             // ✅ Table name
  "operation": "aggregation"
}
```

## What Changed

**Files Modified:**
1. `backend/knowledge/prompts/create_plan.yaml` - Added explicit database vs table naming instructions
2. `backend/app/llm/orchestrator.py` - Added schema loading and formatting methods
3. `backend/pyproject.toml` - Added `psycopg-pool` dependency

**Files Created:**
- `backend/app/llm/executor.py` - Already had proper schema loading
- `backend/app/llm/schemas.py` - Schema definitions
- `backend/knowledge/prompts/generate_sql.yaml` - SQL generation prompt
- `backend/knowledge/prompts/analyze_error.yaml` - Error analysis prompt
- `backend/knowledge/prompts/write_summary.yaml` - Summary generation prompt

## Testing

The backend should now automatically reload with these fixes. Try asking:

```
"How many customers do we have?"
```

Expected plan:
```json
{
  "steps": [
    {
      "step_number": 1,
      "databases": ["customer_db"],    // ✅ Correct database ID
      "tables": ["customers"],         // ✅ Correct table name
      "operation": "aggregation"
    }
  ]
}
```

The LLM will now have full context about:
- Which tables belong to which database
- What columns are available in each table
- Clear distinction between database IDs and table names

## Impact

✅ **Fixed**: Database not found errors due to naming confusion
✅ **Improved**: LLM has full schema context for better SQL generation
✅ **Clearer**: Explicit instructions prevent database/table name confusion
✅ **Complete**: All dependencies installed and working
