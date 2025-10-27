"""Data source manager for loading and managing multiple datasources"""
import os
import yaml
import logging
from typing import Dict, List, Optional, Set
from app.datasources.base import DataSourceBase, QueryResult
from app.datasources.postgresql import PostgreSQLDataSource

logger = logging.getLogger(__name__)


class DataSourceManager:
    """Manages multiple data sources and query routing"""

    def __init__(self):
        self.datasources: Dict[str, DataSourceBase] = {}
        self.database_to_datasource: Dict[str, str] = {}  # Maps logical DB to datasource name
        self._load_configurations()

    def _load_configurations(self):
        """Load datasource configurations from YAML and summary.yaml"""
        # Load datasources.yaml
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        datasources_path = os.path.join(base_dir, "knowledge", "datasources.yaml")
        summary_path = os.path.join(base_dir, "knowledge", "data_schemas", "summary.yaml")

        try:
            # Load datasource definitions
            with open(datasources_path, "r") as f:
                datasources_config = yaml.safe_load(f)

            # Create datasource instances
            for name, config in datasources_config.get("datasources", {}).items():
                if not config.get("enabled", True):
                    logger.info(f"Skipping disabled datasource: {name}")
                    continue

                datasource_type = config.get("type", "").lower()

                if datasource_type == "postgresql":
                    datasource = PostgreSQLDataSource(name, config)
                    self.datasources[name] = datasource
                    logger.info(f"Registered PostgreSQL datasource: {name}")
                else:
                    logger.warning(f"Unknown datasource type '{datasource_type}' for: {name}")

            # Load database-to-datasource mappings from summary.yaml
            with open(summary_path, "r") as f:
                summary_config = yaml.safe_load(f)

            for db_config in summary_config.get("data_sources", []):
                db_id = db_config.get("id")
                datasource_name = db_config.get("datasource")

                if db_id and datasource_name:
                    self.database_to_datasource[db_id] = datasource_name

            logger.info(f"Loaded {len(self.datasources)} datasources and {len(self.database_to_datasource)} database mappings")

        except Exception as e:
            logger.error(f"Failed to load datasource configurations: {e}")
            raise

    def connect_all(self) -> Dict[str, bool]:
        """Connect to all enabled datasources"""
        results = {}
        for name, datasource in self.datasources.items():
            try:
                success = datasource.connect()
                results[name] = success
                if success:
                    logger.info(f"Successfully connected to: {name}")
                else:
                    logger.error(f"Failed to connect to: {name}")
            except Exception as e:
                logger.error(f"Error connecting to {name}: {e}")
                results[name] = False

        return results

    def disconnect_all(self):
        """Disconnect from all datasources"""
        for name, datasource in self.datasources.items():
            try:
                datasource.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting from {name}: {e}")

    def get_datasource(self, name: str) -> Optional[DataSourceBase]:
        """Get a datasource by name"""
        return self.datasources.get(name)

    def get_datasource_for_database(self, database: str) -> Optional[DataSourceBase]:
        """Get the datasource that contains a specific database"""
        datasource_name = self.database_to_datasource.get(database)
        if datasource_name:
            return self.datasources.get(datasource_name)
        return None

    def validate_databases(self, databases: List[str]) -> Dict[str, any]:
        """
        Validate that a list of databases can be queried together

        Args:
            databases: List of logical database names

        Returns:
            Dictionary with validation result:
            - valid: bool
            - datasource: str (if valid, the datasource name)
            - error: str (if invalid, the error message)
            - database_sources: dict mapping each DB to its datasource
        """
        if not databases:
            return {
                "valid": False,
                "error": "No databases specified"
            }

        # Map each database to its datasource
        database_sources = {}
        unique_datasources = set()

        for db in databases:
            datasource_name = self.database_to_datasource.get(db)

            if not datasource_name:
                return {
                    "valid": False,
                    "error": f"Database '{db}' not found in any datasource",
                    "database_sources": database_sources
                }

            datasource = self.datasources.get(datasource_name)

            if not datasource:
                return {
                    "valid": False,
                    "error": f"Datasource '{datasource_name}' for database '{db}' is not available",
                    "database_sources": database_sources
                }

            database_sources[db] = datasource_name
            unique_datasources.add(datasource_name)

        # Check if all databases are in the same datasource
        if len(unique_datasources) > 1:
            return {
                "valid": False,
                "error": f"Cannot query across different datasources. Databases span: {', '.join(unique_datasources)}",
                "database_sources": database_sources
            }

        datasource_name = list(unique_datasources)[0]

        return {
            "valid": True,
            "datasource": datasource_name,
            "database_sources": database_sources
        }

    def execute_query(self, sql: str, database: str, params: Optional[Dict] = None) -> QueryResult:
        """
        Execute a SQL query on the appropriate datasource

        Args:
            sql: SQL query
            database: Logical database name
            params: Optional query parameters

        Returns:
            QueryResult
        """
        datasource = self.get_datasource_for_database(database)

        if not datasource:
            return QueryResult(
                success=False,
                error=f"No datasource found for database '{database}'"
            )

        return datasource.execute_query(sql, database, params)


# Global manager instance
_manager: Optional[DataSourceManager] = None


def get_manager() -> DataSourceManager:
    """Get or create the global datasource manager"""
    global _manager
    if _manager is None:
        _manager = DataSourceManager()
        # Auto-connect on first access
        _manager.connect_all()
    return _manager
