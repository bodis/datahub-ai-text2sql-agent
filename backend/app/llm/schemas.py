"""Structured output schemas for LLM responses"""
from typing import Literal, Optional, List
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
