# Datasource Architecture Change

## Summary

Changed from **one datasource for all databases** to **one datasource per database** to properly support PostgreSQL's database isolation model.

---

## Problem

PostgreSQL cannot run queries across different physical databases. The old architecture tried to use one datasource (`demo_bank`) to manage multiple logical databases as schemas, but this doesn't work for true cross-database scenarios.

### Old Architecture (Single Datasource)

```yaml
datasources:
  demo_bank:
    type: postgresql
    connection:
      database: "${POSTGRES_DB:accounts_db}"  # One physical database
    databases:
      - customer_db    # Treated as schema
      - accounts_db    # Treated as schema
      - loans_db       # etc.
      ...
```

**Problem**: Cannot query across different PostgreSQL databases.

---

## New Architecture (One Datasource Per Database)

Each logical database now has its own physical PostgreSQL database and datasource.

### datasources.yaml

```yaml
datasources:
  customer_db_source:
    type: postgresql
    description: Customer DB PostgreSQL database
    enabled: true
    connection:
      host: "${POSTGRES_HOST:localhost}"
      port: "${POSTGRES_PORT:5432}"
      database: "${POSTGRES_CUSTOMER_DB:customer_db}"
      user: "${POSTGRES_USER:postgres}"
      password: "${POSTGRES_PASSWORD:postgres}"
      min_pool_size: 2
      max_pool_size: 10
      connect_timeout: 10
    databases:
      - customer_db

  accounts_db_source:
    type: postgresql
    description: Accounts DB PostgreSQL database
    enabled: true
    connection:
      host: "${POSTGRES_HOST:localhost}"
      port: "${POSTGRES_PORT:5432}"
      database: "${POSTGRES_ACCOUNTS_DB:accounts_db}"
      user: "${POSTGRES_USER:postgres}"
      password: "${POSTGRES_PASSWORD:postgres}"
      min_pool_size: 2
      max_pool_size: 10
      connect_timeout: 10
    databases:
      - accounts_db

  # ... and 4 more (loans_db_source, insurance_db_source, compliance_db_source, employees_db_source)
```

### summary.yaml

```yaml
data_sources:
  - id: customer_db
    name: Customer DB
    datasource: customer_db_source  # ← Changed from demo_bank

  - id: accounts_db
    name: Accounts DB
    datasource: accounts_db_source  # ← Changed from demo_bank

  - id: loans_db
    name: Loans DB
    datasource: loans_db_source  # ← Changed from demo_bank

  - id: insurance_db
    name: Insurance DB
    datasource: insurance_db_source  # ← Changed from demo_bank

  - id: compliance_db
    name: Compliance DB
    datasource: compliance_db_source  # ← Changed from demo_bank

  - id: employees_db
    name: Employees DB
    datasource: employees_db_source  # ← Changed from demo_bank
```

---

## Configuration Changes

### .env.example

**Before:**
```bash
POSTGRES_DB=accounts_db  # Single database
```

**After:**
```bash
# Connection settings (shared)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Individual database names
POSTGRES_CUSTOMER_DB=customer_db
POSTGRES_ACCOUNTS_DB=accounts_db
POSTGRES_LOANS_DB=loans_db
POSTGRES_INSURANCE_DB=insurance_db
POSTGRES_COMPLIANCE_DB=compliance_db
POSTGRES_EMPLOYEES_DB=employees_db
```

### Your .env File

Update your `.env` to match `.env.example`:

```bash
# Shared connection
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Individual databases (update these to match your PostgreSQL setup)
POSTGRES_CUSTOMER_DB=customer_db
POSTGRES_ACCOUNTS_DB=accounts_db
POSTGRES_LOANS_DB=loans_db
POSTGRES_INSURANCE_DB=insurance_db
POSTGRES_COMPLIANCE_DB=compliance_db
POSTGRES_EMPLOYEES_DB=employees_db
```

---

## Benefits

### ✅ Proper PostgreSQL Isolation

Each database is truly isolated:
- Separate physical PostgreSQL databases
- Independent connection pools
- No cross-database query confusion

### ✅ Clear Datasource Mapping

```
customer_db → customer_db_source → PostgreSQL: customer_db
accounts_db → accounts_db_source → PostgreSQL: accounts_db
loans_db → loans_db_source → PostgreSQL: loans_db
...
```

### ✅ Validation Works Correctly

The existing validation logic (`manager.py:100-160`) already handles this:
- Checks if databases span multiple datasources
- Since each database has its own datasource, cross-database queries are automatically rejected
- Ensures SQL execution only targets one database

### ✅ Flexible Configuration

Each datasource can have:
- Different hosts
- Different ports
- Different credentials
- Independent connection pool settings

---

## Limitations

### ❌ No Cross-Database Queries

**Before (incorrectly assumed possible):**
```sql
-- This will NOT work
SELECT c.name, a.balance
FROM customer_db.public.customers c
JOIN accounts_db.public.accounts a ON c.customer_id = a.customer_id
```

**After (correctly enforced):**
The system will reject queries that try to use multiple databases in a single step.

### ✅ Multi-Step Solution

If a query needs data from multiple databases:

**Step 1:** Query customer_db
```sql
SELECT customer_id, name FROM customers WHERE ...
```

**Step 2:** Use results from Step 1 to query accounts_db
```sql
SELECT balance FROM accounts WHERE customer_id IN (...)
```

**Step 3:** Combine results in summary

This is already how the agentic executor works! Each step targets one database.

---

## Database Setup

You'll need to create 6 separate PostgreSQL databases:

```sql
-- Create all databases
CREATE DATABASE customer_db;
CREATE DATABASE accounts_db;
CREATE DATABASE loans_db;
CREATE DATABASE insurance_db;
CREATE DATABASE compliance_db;
CREATE DATABASE employees_db;
```

Or if you want all databases in one physical database but as separate schemas, update your datasources.yaml to use the same `database` value but different schema qualifiers in your SQL.

---

## Files Modified

1. **`backend/knowledge/datasources.yaml`**
   - Changed from 1 datasource to 6 datasources
   - Each with identical config except database name

2. **`backend/knowledge/data_schemas/summary.yaml`**
   - Updated datasource mappings
   - `customer_db → customer_db_source` (was `demo_bank`)
   - Same for all 6 databases

3. **`backend/.env.example`**
   - Added 6 database environment variables
   - Removed old `POSTGRES_DB` single variable

---

## Migration Steps

If you're migrating from the old setup:

1. **Update `.env`**: Add all 6 database variables
2. **Create databases**: Run SQL to create 6 databases (or use schemas)
3. **Load data**: Populate each database with appropriate tables
4. **Restart backend**: Let it reload new datasources.yaml
5. **Test**: Ask questions that use each database

---

## Verification

Check that datasources loaded correctly:

```bash
# Start backend with debug
cd backend
uv run uvicorn main:app --host 0.0.0.0 --port 5001 --reload
```

Look for logs:
```
INFO - Registered PostgreSQL datasource: customer_db_source
INFO - Registered PostgreSQL datasource: accounts_db_source
INFO - Registered PostgreSQL datasource: loans_db_source
INFO - Registered PostgreSQL datasource: insurance_db_source
INFO - Registered PostgreSQL datasource: compliance_db_source
INFO - Registered PostgreSQL datasource: employees_db_source
INFO - Loaded 6 datasources and 6 database mappings
```

Test query:
```
"How many customers do we have?"
```

Expected:
- Validation: `["customer_db"]`
- Execution: Uses `customer_db_source` → connects to PostgreSQL `customer_db`

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                       │
│                   (Orchestrator + Executor)                 │
└────────────┬────────────────────────────────┬───────────────┘
             │                                │
             │ "customer_db"                  │ "accounts_db"
             │                                │
             ▼                                ▼
┌────────────────────────┐      ┌────────────────────────┐
│  customer_db_source    │      │  accounts_db_source    │
│  (DataSource Manager)  │      │  (DataSource Manager)  │
└────────────┬───────────┘      └────────────┬───────────┘
             │                                │
             │ PostgreSQL                     │ PostgreSQL
             │ Connection                     │ Connection
             │                                │
             ▼                                ▼
┌────────────────────────┐      ┌────────────────────────┐
│  PostgreSQL Database   │      │  PostgreSQL Database   │
│  Name: customer_db     │      │  Name: accounts_db     │
│                        │      │                        │
│  - public schema       │      │  - public schema       │
│    - customers table   │      │    - accounts table    │
│    - campaigns table   │      │    - transactions      │
│    - complaints table  │      │    - customer_master   │
└────────────────────────┘      └────────────────────────┘

    (Same pattern for loans_db, insurance_db, compliance_db, employees_db)
```

---

## Summary

✅ **One datasource per database** - Clean 1:1 mapping
✅ **PostgreSQL isolation** - True database separation
✅ **No code changes needed** - Manager already handles validation
✅ **Multi-step queries work** - Executor handles cross-database needs
✅ **Flexible configuration** - Each database can have different settings
✅ **Automatic validation** - Cross-database queries are rejected

The system now properly reflects PostgreSQL's database isolation model!
