"""Structured output schemas for LLM responses"""
from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    """Result of question validation against data sources"""
    is_relevant: bool = Field(description="Whether the question is relevant to available data sources")
    reasoning: str = Field(description="Explanation of why the question is or isn't relevant")
    suggested_response: Optional[str] = Field(
        default=None,
        description="Suggested response if question is not relevant"
    )
    relevant_databases: List[str] = Field(
        default_factory=list,
        description="List of database IDs that are relevant to answer the question"
    )


class ClarificationQuestion(BaseModel):
    """A clarification question to ask the user"""
    question: str = Field(description="The clarification question to ask")
    reason: str = Field(description="Why this clarification is needed")


class QueryPlanStep(BaseModel):
    """A single step in the query execution plan"""
    step_number: int = Field(description="Sequential step number starting from 1")
    description: str = Field(description="Clear description of what this step does")
    databases: List[str] = Field(description="List of database names involved (e.g., ['customer_db', 'accounts_db'])")
    tables: List[str] = Field(description="List of table names involved (e.g., ['customers', 'accounts'])")
    operation: Literal["single_query", "join_query", "aggregation", "calculation"] = Field(
        description="REQUIRED: Type of operation. Must be one of: 'single_query' (query one table), 'join_query' (join multiple tables), 'aggregation' (GROUP BY, COUNT, SUM, etc.), 'calculation' (computed fields, formulas)"
    )


class QueryPlan(BaseModel):
    """Complete plan to answer user's question"""
    summary: str = Field(description="High-level summary of how to answer the question")
    steps: List[QueryPlanStep] = Field(description="Ordered list of steps to execute")
    expected_output: str = Field(description="Description of what the final result will contain")
    needs_clarification: bool = Field(default=False, description="Whether clarification is needed")
    clarification_questions: List[ClarificationQuestion] = Field(
        default_factory=list,
        description="Questions to ask user if clarification needed"
    )


class DecisionResult(BaseModel):
    """Decision on what action to take next"""
    action: Literal["ask_clarification", "create_plan", "answer_directly", "reject"] = Field(
        description="The action to take"
    )
    reasoning: str = Field(description="Why this action was chosen")
    message: Optional[str] = Field(
        default=None,
        description="Message to send to user (for ask_clarification, answer_directly, or reject)"
    )


class SQLGenerationResult(BaseModel):
    """Result of SQL generation for a plan step"""
    sql: str = Field(description="The generated SQL query")
    reasoning: str = Field(description="Explanation of what the SQL does and why it was written this way")
    database: str = Field(description="The logical database name to execute this query against")


class ErrorAnalysisResult(BaseModel):
    """Analysis of a SQL execution error"""
    is_recoverable: bool = Field(description="Whether the error can be fixed by modifying the SQL")
    reasoning: str = Field(description="Explanation of the error and why it is or isn't recoverable")
    suggested_sql: Optional[str] = Field(
        default=None,
        description="Corrected SQL query if error is recoverable, None otherwise"
    )
    error_type: Literal["syntax", "schema", "permission", "connection", "data", "other"] = Field(
        description="Category of error: syntax (SQL syntax error), schema (table/column not found), permission (access denied), connection (database unavailable), data (constraint violation, type mismatch), other"
    )


class StepExecutionResult(BaseModel):
    """Result of executing a single plan step"""
    step_number: int = Field(description="The step number that was executed")
    success: bool = Field(description="Whether the step executed successfully")
    sql: Optional[str] = Field(default=None, description="The final SQL that was executed (after any corrections)")
    result_data: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="The query results as a list of dictionaries (for CSV-like output)"
    )
    result_value: Optional[str] = Field(
        default=None,
        description="Single result value (for direct answers like counts, sums)"
    )
    error: Optional[str] = Field(default=None, description="Error message if execution failed")
    attempts: int = Field(default=1, description="Number of SQL generation attempts made")


class SummaryResult(BaseModel):
    """Final summary that answers the user's question"""
    answer: str = Field(description="The complete answer to the user's question in their language")
    is_answerable: bool = Field(description="Whether the question could be answered with the available data")
    confidence: Literal["high", "medium", "low"] = Field(
        description="Confidence level in the answer based on data quality and completeness"
    )
    data_sources_used: List[str] = Field(
        description="List of databases that were queried to answer the question"
    )
