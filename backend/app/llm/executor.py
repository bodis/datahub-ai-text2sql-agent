"""Agentic executor for SQL generation and execution"""
import os
import yaml
import logging
from typing import List, Dict, Any, Optional
from app.llm.client import get_client, ConversationMessage
from app.llm.prompts import get_prompt_loader
from app.llm.schemas import (
    QueryPlan,
    QueryPlanStep,
    SQLGenerationResult,
    ErrorAnalysisResult,
    StepExecutionResult,
    SummaryResult
)
from app.datasources.manager import get_manager
from app.datasources.base import QueryResult

logger = logging.getLogger(__name__)


class StepExecutor:
    """Executes query plan steps with agentic SQL generation and error recovery"""

    MAX_RETRY_ATTEMPTS = 5

    def __init__(self, thread_id: Optional[str] = None):
        self.client = get_client()
        self.prompt_loader = get_prompt_loader()
        self.datasource_manager = get_manager()
        self.thread_id = thread_id
        self.token_usage_callback = None
        self.debug_info = []
        self._load_schemas()

    def _load_schemas(self):
        """Load all database schemas from YAML files"""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        schemas_dir = os.path.join(base_dir, "knowledge", "data_schemas")

        self.schemas = {}

        # Load all database schema files
        schema_files = [
            "customer_db.yaml",
            "accounts_db.yaml",
            "loans_db.yaml",
            "insurance_db.yaml",
            "compliance_db.yaml",
            "employees_db.yaml"
        ]

        for filename in schema_files:
            filepath = os.path.join(schemas_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, "r") as f:
                        schema_data = yaml.safe_load(f)
                        # Extract database name from the schema
                        for db_name, db_info in schema_data.get("databases", {}).items():
                            self.schemas[db_name] = db_info
                    logger.info(f"Loaded schema from {filename}")
                except Exception as e:
                    logger.error(f"Failed to load schema from {filename}: {e}")

    def _format_schema_for_databases(self, databases: List[str]) -> str:
        """Format schema information for the specified databases"""
        lines = []

        for db_name in databases:
            if db_name not in self.schemas:
                lines.append(f"### {db_name}\n(Schema information not available)\n")
                continue

            db_info = self.schemas[db_name]
            lines.append(f"### {db_name}\n")

            # Format schemas and tables
            for schema_name, schema_info in db_info.get("schemas", {}).items():
                for table_name, table_info in schema_info.get("tables", {}).items():
                    full_table = f"{db_name}.{schema_name}.{table_name}"
                    lines.append(f"\n**Table: {full_table}**")
                    lines.append(f"Description: {table_info.get('description', 'N/A')}")
                    lines.append("Columns:")

                    for col in table_info.get("columns", []):
                        col_name = col.get("name")
                        col_type = col.get("type")
                        col_desc = col.get("description", "")
                        nullable = "NULL" if col.get("nullable", True) else "NOT NULL"
                        lines.append(f"  - {col_name} ({col_type}, {nullable}): {col_desc}")

                        # Add foreign key info if present
                        if "foreign_key" in col:
                            fk = col["foreign_key"]
                            lines.append(f"    FK -> {fk['table']}.{fk['column']}")

        return "\n".join(lines)

    def _format_previous_results(self, previous_results: List[StepExecutionResult]) -> str:
        """Format previous step results for context"""
        if not previous_results:
            return "No previous results available."

        lines = ["Previous step results:"]
        for result in previous_results:
            lines.append(f"\nStep {result.step_number}:")
            lines.append(f"Success: {result.success}")

            if result.success:
                if result.result_value:
                    lines.append(f"Result: {result.result_value}")
                elif result.result_data:
                    lines.append(f"Rows returned: {len(result.result_data)}")
                    # Show first few rows as sample
                    if len(result.result_data) > 0:
                        lines.append("Sample data:")
                        for i, row in enumerate(result.result_data[:3]):
                            lines.append(f"  Row {i+1}: {row}")
                        if len(result.result_data) > 3:
                            lines.append(f"  ... and {len(result.result_data) - 3} more rows")
            else:
                lines.append(f"Error: {result.error}")

        return "\n".join(lines)

    def _format_last_attempt(self, last_attempt: Dict[str, Any]) -> str:
        """Format the last SQL attempt for error analysis context"""
        if not last_attempt:
            return "This is the first attempt."

        return f"Previous SQL:\n{last_attempt['sql']}\n\nPrevious Error:\n{last_attempt['error']}"

    def _generate_sql(
        self,
        original_question: str,
        step: QueryPlanStep,
        previous_results: List[StepExecutionResult]
    ) -> SQLGenerationResult:
        """Generate SQL for a plan step using LLM"""
        template = self.prompt_loader.load("generate_sql")

        # Get relevant schemas
        database_schemas = self._format_schema_for_databases(step.databases)
        previous_results_text = self._format_previous_results(previous_results)

        user_prompt = template.render_user_prompt(
            original_question=original_question,
            step_number=step.step_number,
            step_description=step.description,
            step_databases=", ".join(step.databases),
            step_tables=", ".join(step.tables),
            step_operation=step.operation,
            previous_results=previous_results_text,
            database_schemas=database_schemas
        )

        # Replace ${database_schemas} in system prompt
        system_prompt = template.system_prompt.replace("${database_schemas}", database_schemas)

        messages = [ConversationMessage(role="user", content=user_prompt)]

        result, usage = self.client.complete_structured(
            messages=messages,
            response_model=SQLGenerationResult,
            system_prompt=system_prompt,
            temperature=template.temperature,
            model=template.model
        )

        # Track debug info
        self.debug_info.append({
            "stage": "sql_generation",
            "step": step.step_number,
            "model": template.model,
            "elapsed_ms": usage.get("elapsed_time_ms", 0),
            "tokens": usage
        })

        # Track token usage
        if self.token_usage_callback:
            self.token_usage_callback(usage)

        return result

    def _analyze_error(
        self,
        original_question: str,
        step: QueryPlanStep,
        failed_sql: str,
        error_message: str,
        attempt_number: int,
        last_attempt: Optional[Dict[str, Any]] = None
    ) -> ErrorAnalysisResult:
        """Analyze SQL error and suggest fix using LLM"""
        template = self.prompt_loader.load("analyze_error")

        # Get relevant schemas
        database_schemas = self._format_schema_for_databases(step.databases)

        # Only include the immediate previous attempt (if any), not full history
        previous_attempt_text = self._format_last_attempt(last_attempt) if last_attempt else "This is the first attempt."

        user_prompt = template.render_user_prompt(
            original_question=original_question,
            step_number=step.step_number,
            step_description=step.description,
            failed_sql=failed_sql,
            error_message=error_message,
            attempt_number=attempt_number,
            previous_attempts=previous_attempt_text
        )

        # Replace ${database_schemas} in system prompt
        system_prompt = template.system_prompt.replace("${database_schemas}", database_schemas)

        messages = [ConversationMessage(role="user", content=user_prompt)]

        result, usage = self.client.complete_structured(
            messages=messages,
            response_model=ErrorAnalysisResult,
            system_prompt=system_prompt,
            temperature=template.temperature,
            model=template.model
        )

        # Track debug info
        self.debug_info.append({
            "stage": "error_analysis",
            "step": step.step_number,
            "attempt": attempt_number,
            "model": template.model,
            "elapsed_ms": usage.get("elapsed_time_ms", 0),
            "tokens": usage
        })

        # Track token usage
        if self.token_usage_callback:
            self.token_usage_callback(usage)

        return result

    def _execute_sql(self, sql: str, database: str) -> QueryResult:
        """Execute SQL via datasource manager"""
        try:
            return self.datasource_manager.execute_query(sql, database)
        except Exception as e:
            logger.error(f"Error executing SQL: {e}", exc_info=True)
            return QueryResult(
                success=False,
                error=f"Execution error: {str(e)}"
            )

    def _execute_step_with_retry(
        self,
        original_question: str,
        step: QueryPlanStep,
        previous_results: List[StepExecutionResult]
    ) -> StepExecutionResult:
        """Execute a single step with retry logic (agentic loop)"""
        attempts = []
        current_sql = None

        for attempt_num in range(1, self.MAX_RETRY_ATTEMPTS + 1):
            try:
                # Generate SQL (first time) or get corrected SQL (retry)
                if attempt_num == 1:
                    logger.info(f"Generating SQL for step {step.step_number}")
                    sql_result = self._generate_sql(original_question, step, previous_results)
                    current_sql = sql_result.sql
                    database = sql_result.database
                    logger.debug(f"Generated SQL: {current_sql}")
                else:
                    # We already have the corrected SQL from error analysis
                    logger.info(f"Retrying step {step.step_number} with corrected SQL (attempt {attempt_num})")
                    logger.debug(f"Corrected SQL: {current_sql}")

                # Execute SQL
                query_result = self._execute_sql(current_sql, database)

                if query_result.success:
                    # Success! Format and return result
                    logger.info(f"Step {step.step_number} executed successfully on attempt {attempt_num}")

                    # Determine if result is a single value or dataset
                    result_value = None
                    result_data = None

                    if query_result.data and len(query_result.data) > 0:
                        # Check if it's a single value result
                        if len(query_result.data) == 1 and len(query_result.data[0]) == 1:
                            # Single value
                            result_value = str(list(query_result.data[0].values())[0])
                        else:
                            # Multiple rows/columns - dataset
                            result_data = query_result.data

                    return StepExecutionResult(
                        step_number=step.step_number,
                        success=True,
                        sql=current_sql,
                        result_data=result_data,
                        result_value=result_value,
                        attempts=attempt_num
                    )
                else:
                    # Query failed - analyze error
                    logger.warning(f"Step {step.step_number} failed on attempt {attempt_num}: {query_result.error}")

                    # Record this attempt
                    attempts.append({
                        "sql": current_sql,
                        "error": query_result.error
                    })

                    # If this was the last attempt, give up
                    if attempt_num == self.MAX_RETRY_ATTEMPTS:
                        logger.error(f"Step {step.step_number} failed after {self.MAX_RETRY_ATTEMPTS} attempts")
                        return StepExecutionResult(
                            step_number=step.step_number,
                            success=False,
                            sql=current_sql,
                            error=f"Failed after {self.MAX_RETRY_ATTEMPTS} attempts. Last error: {query_result.error}",
                            attempts=attempt_num
                        )

                    # Analyze error and get correction
                    # Only pass the immediate previous attempt (if any), not full history
                    last_attempt = attempts[-2] if len(attempts) >= 2 else None
                    error_analysis = self._analyze_error(
                        original_question=original_question,
                        step=step,
                        failed_sql=current_sql,
                        error_message=query_result.error,
                        attempt_number=attempt_num,
                        last_attempt=last_attempt
                    )

                    if not error_analysis.is_recoverable:
                        # Error is not recoverable - stop trying
                        logger.error(f"Step {step.step_number} has non-recoverable error: {error_analysis.reasoning}")
                        return StepExecutionResult(
                            step_number=step.step_number,
                            success=False,
                            sql=current_sql,
                            error=f"Non-recoverable error ({error_analysis.error_type}): {error_analysis.reasoning}",
                            attempts=attempt_num
                        )

                    # Error is recoverable - try corrected SQL
                    if error_analysis.suggested_sql:
                        current_sql = error_analysis.suggested_sql
                        database = database  # Keep same database
                    else:
                        # No suggested SQL even though recoverable? This shouldn't happen but handle it
                        logger.error(f"Error marked as recoverable but no suggested SQL provided")
                        return StepExecutionResult(
                            step_number=step.step_number,
                            success=False,
                            sql=current_sql,
                            error=f"Error analysis failed to provide corrected SQL: {error_analysis.reasoning}",
                            attempts=attempt_num
                        )

            except Exception as e:
                logger.error(f"Unexpected error in step {step.step_number} attempt {attempt_num}: {e}", exc_info=True)
                return StepExecutionResult(
                    step_number=step.step_number,
                    success=False,
                    sql=current_sql,
                    error=f"Unexpected error: {str(e)}",
                    attempts=attempt_num
                )

        # Should not reach here, but just in case
        return StepExecutionResult(
            step_number=step.step_number,
            success=False,
            error="Maximum retry attempts exceeded",
            attempts=self.MAX_RETRY_ATTEMPTS
        )

    def execute_plan(
        self,
        original_question: str,
        plan: QueryPlan
    ) -> List[StepExecutionResult]:
        """
        Execute all steps in the query plan with agentic SQL generation

        Args:
            original_question: The original user question
            plan: The query plan to execute

        Returns:
            List of step execution results
        """
        results = []

        for step in plan.steps:
            logger.info(f"Executing step {step.step_number}/{len(plan.steps)}")

            # Execute this step with retry logic
            step_result = self._execute_step_with_retry(
                original_question=original_question,
                step=step,
                previous_results=results
            )

            results.append(step_result)

            # If step failed, stop execution
            if not step_result.success:
                logger.error(f"Step {step.step_number} failed, stopping execution")
                break

        return results

    def generate_summary(
        self,
        original_question: str,
        plan: QueryPlan,
        execution_results: List[StepExecutionResult]
    ) -> SummaryResult:
        """
        Generate final summary from execution results

        Args:
            original_question: The original user question
            plan: The query plan that was executed
            execution_results: Results from all executed steps

        Returns:
            Summary result with final answer
        """
        template = self.prompt_loader.load("write_summary")

        # Format plan summary
        plan_summary = plan.summary

        # Format execution results
        results_lines = []
        data_sources_used = set()

        for result in execution_results:
            # Find the corresponding step in plan
            step = next((s for s in plan.steps if s.step_number == result.step_number), None)

            results_lines.append(f"\n**Step {result.step_number}**")
            if step:
                results_lines.append(f"Description: {step.description}")
                data_sources_used.update(step.databases)

            results_lines.append(f"Status: {'✓ Success' if result.success else '✗ Failed'}")

            if result.success:
                if result.result_value:
                    results_lines.append(f"Result: {result.result_value}")
                elif result.result_data:
                    results_lines.append(f"Rows returned: {len(result.result_data)}")
                    results_lines.append("Data:")
                    # Format as markdown table if possible
                    if len(result.result_data) > 0:
                        cols = list(result.result_data[0].keys())
                        results_lines.append("| " + " | ".join(cols) + " |")
                        results_lines.append("|" + "|".join(["---"] * len(cols)) + "|")
                        for row in result.result_data[:10]:  # Limit to 10 rows
                            results_lines.append("| " + " | ".join(str(row.get(c, "")) for c in cols) + " |")
                        if len(result.result_data) > 10:
                            results_lines.append(f"... and {len(result.result_data) - 10} more rows")
                results_lines.append(f"SQL executed: ```sql\n{result.sql}\n```")
            else:
                results_lines.append(f"Error: {result.error}")

        execution_results_text = "\n".join(results_lines)

        user_prompt = template.render_user_prompt(
            original_question=original_question,
            plan_summary=plan_summary,
            execution_results=execution_results_text
        )

        messages = [ConversationMessage(role="user", content=user_prompt)]

        result, usage = self.client.complete_structured(
            messages=messages,
            response_model=SummaryResult,
            system_prompt=template.system_prompt,
            temperature=template.temperature,
            model=template.model
        )

        # Track debug info
        self.debug_info.append({
            "stage": "summary",
            "model": template.model,
            "elapsed_ms": usage.get("elapsed_time_ms", 0),
            "tokens": usage
        })

        # Track token usage
        if self.token_usage_callback:
            self.token_usage_callback(usage)

        return result


def get_executor(thread_id: Optional[str] = None) -> StepExecutor:
    """Create a new executor instance"""
    return StepExecutor(thread_id=thread_id)
