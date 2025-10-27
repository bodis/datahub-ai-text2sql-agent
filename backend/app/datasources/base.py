"""Base classes for data source abstraction"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class QueryResult:
    """Result of a SQL query execution"""
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    columns: Optional[List[str]] = None
    row_count: int = 0
    error: Optional[str] = None
    execution_time_ms: Optional[int] = None


class DataSourceBase(ABC):
    """Abstract base class for data sources"""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.enabled = config.get("enabled", True)
        self.description = config.get("description", "")
        self.databases = config.get("databases", [])

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the data source"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to the data source"""
        pass

    @abstractmethod
    def execute_query(self, sql: str, database: str, params: Optional[Dict] = None) -> QueryResult:
        """
        Execute a SQL query

        Args:
            sql: The SQL query to execute
            database: Logical database name (e.g., 'customer_db')
            params: Optional query parameters

        Returns:
            QueryResult with data or error
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test if connection is alive"""
        pass

    @abstractmethod
    def get_schema_info(self, database: str) -> Dict[str, Any]:
        """
        Get schema information for a database

        Args:
            database: Logical database name

        Returns:
            Dictionary with table and column information
        """
        pass

    def supports_database(self, database: str) -> bool:
        """Check if this datasource supports a given database"""
        return database in self.databases

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}' databases={self.databases}>"
