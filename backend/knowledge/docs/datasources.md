# Data Source Management

## Overview

The AI Data Agent uses a flexible datasource management system that allows connecting to multiple physical databases and mapping logical database names to them.

## Architecture

### Components

1. **DataSourceBase** (`app/datasources/base.py`)
   - Abstract base class for all datasource implementations
   - Defines interface for connection, query execution, and schema introspection

2. **PostgreSQLDataSource** (`app/datasources/postgresql.py`)
   - PostgreSQL implementation using psycopg3
   - Supports connection pooling
   - Maps logical database names to PostgreSQL schemas

3. **DataSourceManager** (`app/datasources/manager.py`)
   - Central manager for all datasources
   - Handles datasource registration and routing
   - Validates cross-datasource queries

## Configuration

### datasources.yaml

Defines physical datasource connections:

```yaml
datasources:
  demo_bank:
    type: postgresql
    description: Demo bank PostgreSQL database
    enabled: true
    connection:
      host: "${POSTGRES_HOST:localhost}"
      port: "${POSTGRES_PORT:5432}"
      database: "${POSTGRES_DB:demo_bank}"
      user: "${POSTGRES_USER:postgres}"
      password: "${POSTGRES_PASSWORD:postgres}"
      min_pool_size: 2
      max_pool_size: 10
      connect_timeout: 10
    databases:
      - customer_db
      - accounts_db
      - loans_db
      - insurance_db
      - compliance_db
      - employees_db
```

### summary.yaml

Maps logical databases to datasources:

```yaml
data_sources:
  - id: customer_db
    name: Customer DB
    datasource: demo_bank  # References datasources.yaml
```

## Environment Variables

Configure in `.env`:

```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=demo_bank
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

## PostgreSQL Schema Setup

The system expects each logical database (customer_db, accounts_db, etc.) to exist as a PostgreSQL schema:

```sql
-- Create schemas
CREATE SCHEMA IF NOT EXISTS customer_db;
CREATE SCHEMA IF NOT EXISTS accounts_db;
CREATE SCHEMA IF NOT EXISTS loans_db;
CREATE SCHEMA IF NOT EXISTS insurance_db;
CREATE SCHEMA IF NOT EXISTS compliance_db;
CREATE SCHEMA IF NOT EXISTS employees_db;

-- Example: Create tables in customer_db schema
CREATE TABLE customer_db.customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200),
    email VARCHAR(150)
);
```

## Query Execution

### Single Database Query

```python
from app.datasources.manager import get_manager

manager = get_manager()

# Execute query on customer_db (mapped to demo_bank datasource)
result = manager.execute_query(
    sql="SELECT * FROM customers LIMIT 10",
    database="customer_db"
)

if result.success:
    print(f"Found {result.row_count} rows")
    for row in result.data:
        print(row)
else:
    print(f"Error: {result.error}")
```

### Cross-Database Validation

The orchestrator automatically validates that all databases in a query belong to the same datasource:

```python
# Validate databases can be queried together
validation = manager.validate_databases(["customer_db", "accounts_db"])

if validation["valid"]:
    datasource = validation["datasource"]  # "demo_bank"
    # All databases are in the same datasource - can proceed
else:
    error = validation["error"]  # "Cannot query across different datasources..."
```

## Adding New Datasources

### 1. Implement DataSource Class

```python
from app.datasources.base import DataSourceBase, QueryResult

class MySQLDataSource(DataSourceBase):
    def connect(self) -> bool:
        # Implement MySQL connection
        pass

    def execute_query(self, sql: str, database: str, params=None) -> QueryResult:
        # Implement query execution
        pass

    # Implement other abstract methods...
```

### 2. Register in Manager

Update `app/datasources/manager.py`:

```python
elif datasource_type == "mysql":
    datasource = MySQLDataSource(name, config)
```

### 3. Add Configuration

Add to `datasources.yaml`:

```yaml
my_datasource:
  type: mysql
  enabled: true
  connection:
    host: localhost
    ...
  databases:
    - some_db
```

### 4. Update Summary

Add datasource reference to `summary.yaml`:

```yaml
- id: some_db
  datasource: my_datasource
```

## Connection Pooling

PostgreSQL datasource uses psycopg3 connection pooling:

- **min_pool_size**: Minimum connections to maintain
- **max_pool_size**: Maximum connections allowed
- **connect_timeout**: Connection timeout in seconds

## Error Handling

Query execution returns `QueryResult`:

```python
@dataclass
class QueryResult:
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    columns: Optional[List[str]] = None
    row_count: int = 0
    error: Optional[str] = None
    execution_time_ms: Optional[int] = None
```

## Future Enhancements

- [ ] Support for MySQL, SQLite, MongoDB
- [ ] Query result caching
- [ ] Read replicas and load balancing
- [ ] Query performance monitoring
- [ ] Connection health checks
- [ ] Automatic reconnection on failure
