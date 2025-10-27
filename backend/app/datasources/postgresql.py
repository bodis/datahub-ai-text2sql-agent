"""PostgreSQL data source implementation using psycopg3"""
import os
import time
import logging
from typing import List, Dict, Any, Optional
import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from app.datasources.base import DataSourceBase, QueryResult

logger = logging.getLogger(__name__)


class PostgreSQLDataSource(DataSourceBase):
    """PostgreSQL data source using psycopg3 with connection pooling"""

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.connection_config = config.get("connection", {})
        self.pool: Optional[ConnectionPool] = None

        # Resolve environment variables in connection config
        self._resolve_env_vars()

    def _resolve_env_vars(self):
        """Resolve ${ENV_VAR:default} placeholders in connection config"""
        for key, value in self.connection_config.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                # Parse ${ENV_VAR:default}
                var_spec = value[2:-1]  # Remove ${ and }
                if ":" in var_spec:
                    env_var, default = var_spec.split(":", 1)
                    self.connection_config[key] = os.getenv(env_var, default)
                else:
                    self.connection_config[key] = os.getenv(var_spec, "")

    def _get_connection_string(self) -> str:
        """Build PostgreSQL connection string"""
        host = self.connection_config.get("host", "localhost")
        port = self.connection_config.get("port", 5432)
        database = self.connection_config.get("database", "postgres")
        user = self.connection_config.get("user", "postgres")
        password = self.connection_config.get("password", "")

        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    def connect(self) -> bool:
        """Establish connection pool to PostgreSQL"""
        try:
            conninfo = self._get_connection_string()
            min_size = self.connection_config.get("min_pool_size", 2)
            max_size = self.connection_config.get("max_pool_size", 10)
            timeout = self.connection_config.get("connect_timeout", 10)

            self.pool = ConnectionPool(
                conninfo=conninfo,
                min_size=min_size,
                max_size=max_size,
                timeout=timeout,
                kwargs={"row_factory": dict_row}
            )

            logger.info(f"Connected to PostgreSQL datasource '{self.name}' (pool: {min_size}-{max_size})")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL datasource '{self.name}': {e}")
            return False

    def disconnect(self) -> None:
        """Close connection pool"""
        if self.pool:
            self.pool.close()
            logger.info(f"Disconnected from PostgreSQL datasource '{self.name}'")
            self.pool = None

    def test_connection(self) -> bool:
        """Test if connection is alive"""
        if not self.pool:
            return False

        try:
            with self.pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    result = cur.fetchone()
                    return result is not None
        except Exception as e:
            logger.error(f"Connection test failed for '{self.name}': {e}")
            return False

    def execute_query(self, sql: str, database: str, params: Optional[Dict] = None) -> QueryResult:
        """
        Execute a SQL query

        Args:
            sql: The SQL query to execute
            database: Logical database name (e.g., 'customer_db') - used as schema in PostgreSQL
            params: Optional query parameters

        Returns:
            QueryResult with data or error
        """
        if not self.pool:
            return QueryResult(
                success=False,
                error="Data source not connected. Call connect() first."
            )

        if not self.supports_database(database):
            return QueryResult(
                success=False,
                error=f"Database '{database}' not supported by datasource '{self.name}'"
            )

        start_time = time.time()

        try:
            with self.pool.connection() as conn:
                # Set search_path to the logical database (schema)
                with conn.cursor() as cur:
                    # Set schema search path
                    cur.execute(f"SET search_path TO {database}, public")

                    # Execute the actual query
                    if params:
                        cur.execute(sql, params)
                    else:
                        cur.execute(sql)

                    # Fetch results if it's a SELECT query
                    if cur.description:
                        columns = [desc[0] for desc in cur.description]
                        rows = cur.fetchall()
                        row_count = len(rows)

                        execution_time = int((time.time() - start_time) * 1000)

                        return QueryResult(
                            success=True,
                            data=rows,
                            columns=columns,
                            row_count=row_count,
                            execution_time_ms=execution_time
                        )
                    else:
                        # Non-SELECT query (INSERT, UPDATE, DELETE)
                        row_count = cur.rowcount if cur.rowcount >= 0 else 0
                        conn.commit()

                        execution_time = int((time.time() - start_time) * 1000)

                        return QueryResult(
                            success=True,
                            row_count=row_count,
                            execution_time_ms=execution_time
                        )

        except psycopg.Error as e:
            execution_time = int((time.time() - start_time) * 1000)
            error_msg = f"PostgreSQL error: {str(e)}"
            logger.error(f"Query execution failed in '{self.name}': {error_msg}")

            return QueryResult(
                success=False,
                error=error_msg,
                execution_time_ms=execution_time
            )

        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Query execution failed in '{self.name}': {error_msg}")

            return QueryResult(
                success=False,
                error=error_msg,
                execution_time_ms=execution_time
            )

    def get_schema_info(self, database: str) -> Dict[str, Any]:
        """
        Get schema information for a database (schema in PostgreSQL)

        Args:
            database: Logical database name (schema name)

        Returns:
            Dictionary with table and column information
        """
        if not self.supports_database(database):
            return {"error": f"Database '{database}' not supported"}

        query = """
            SELECT
                table_name,
                column_name,
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = %s
            ORDER BY table_name, ordinal_position
        """

        result = self.execute_query(query, database, {"schema": database})

        if not result.success:
            return {"error": result.error}

        # Group by table
        tables = {}
        for row in result.data or []:
            table_name = row["table_name"]
            if table_name not in tables:
                tables[table_name] = {"columns": []}

            tables[table_name]["columns"].append({
                "name": row["column_name"],
                "type": row["data_type"],
                "nullable": row["is_nullable"] == "YES"
            })

        return {"schema": database, "tables": tables}
