"""Main orchestrator for multi-stage LLM query planning"""
import os
import yaml
from typing import List, Dict, Any, Optional
from app.llm.client import get_client, ConversationMessage
from app.llm.prompts import get_prompt_loader
from app.llm.schemas import ValidationResult, DecisionResult, QueryPlan
from app.datasources.manager import get_manager
from app.llm.executor import get_executor
from app.storage import storage


class QueryOrchestrator:
    """Orchestrates the multi-stage query planning process"""

    def __init__(self, thread_id: Optional[str] = None):
        self.client = get_client()
        self.prompt_loader = get_prompt_loader()
        self.thread_id = thread_id
        self.token_usage_callback = None  # Will be set by caller
        self.debug_info = []  # Track LLM interactions for debugging
        self._load_data_sources()

    def _load_data_sources(self):
        """Load data sources from summary.yaml"""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        summary_path = os.path.join(base_dir, "knowledge", "data_schemas", "summary.yaml")

        with open(summary_path, "r") as f:
            data = yaml.safe_load(f)

        self.data_sources = data.get("data_sources", [])

    def _format_data_sources(self) -> str:
        """Format data sources for prompt"""
        lines = []
        for source in self.data_sources:
            lines.append(f"- {source['name']} ({source['id']}): {source['description']}")
        return "\n".join(lines)

    def _format_conversation_history(self, conversation: List[Dict[str, str]]) -> str:
        """Format conversation history for prompt"""
        if not conversation:
            return "No previous conversation."

        lines = []
        for msg in conversation[-5:]:  # Last 5 messages for context
            role = msg.get("sender", "unknown")
            content = msg.get("content", "")
            lines.append(f"{role.upper()}: {content}")

        return "\n".join(lines)

    def _load_database_schemas(self) -> Dict[str, Any]:
        """Load all database schemas from YAML files"""
        schemas = {}
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        schemas_dir = os.path.join(base_dir, "knowledge", "data_schemas")

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
                        for db_name, db_info in schema_data.get("databases", {}).items():
                            schemas[db_name] = db_info
                except Exception as e:
                    import logging
                    logging.error(f"Failed to load schema from {filename}: {e}")

        return schemas

    def _format_database_schemas(self, database_names: List[str]) -> str:
        """Format schema information for specific databases"""
        schemas = self._load_database_schemas()
        lines = []

        for db_name in database_names:
            if db_name not in schemas:
                lines.append(f"### {db_name}\n(Schema not available)\n")
                continue

            db_info = schemas[db_name]
            lines.append(f"### Database: {db_name}\n")

            # Format tables with their descriptions
            for schema_name, schema_info in db_info.get("schemas", {}).items():
                for table_name, table_info in schema_info.get("tables", {}).items():
                    lines.append(f"\n**Table: {table_name}** (in {db_name}.{schema_name})")
                    lines.append(f"Description: {table_info.get('description', 'N/A')}")

                    # List key columns
                    columns = table_info.get("columns", [])[:5]  # First 5 columns for planning
                    if columns:
                        lines.append("Key columns:")
                        for col in columns:
                            col_name = col.get("name")
                            col_type = col.get("type")
                            col_desc = col.get("description", "")
                            lines.append(f"  - {col_name} ({col_type}): {col_desc}")

        return "\n".join(lines)

    def process_question(
        self,
        question: str,
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Process a user question through the multi-stage pipeline

        Args:
            question: The user's question
            conversation_history: Previous messages in the conversation

        Returns:
            Dictionary with response and metadata
        """
        import time
        pipeline_start = time.time()

        # Stage 1: Validate question
        validation_result = self._validate_question(question, conversation_history)

        # Track databases used in this thread (if relevant)
        if validation_result.is_relevant and validation_result.relevant_databases and self.thread_id:
            try:
                storage.add_used_databases(self.thread_id, validation_result.relevant_databases)
            except Exception as e:
                # Don't fail the request if tracking fails
                import logging
                logging.warning(f"Failed to track used databases: {e}")

        if not validation_result.is_relevant:
            pipeline_time = time.time() - pipeline_start
            # Update all debug info with pipeline time
            for info in self.debug_info:
                info["pipeline_time_ms"] = int(pipeline_time * 1000)
            return {
                "type": "rejection",
                "message": validation_result.suggested_response or
                          "I can only help with queries about financial and banking data. Your question appears to be outside this scope.",
                "metadata": {
                    "validation": validation_result.model_dump(),
                    "pipeline_time_ms": int(pipeline_time * 1000),
                    "debug_info": self.debug_info
                }
            }

        # Stage 2: Decide action
        decision = self._decide_action(question, validation_result, conversation_history)

        if decision.action == "answer_directly":
            pipeline_time = time.time() - pipeline_start
            # Update all debug info with pipeline time
            for info in self.debug_info:
                info["pipeline_time_ms"] = int(pipeline_time * 1000)
            return {
                "type": "direct_answer",
                "message": decision.message,
                "metadata": {
                    "validation": validation_result.model_dump(),
                    "decision": decision.model_dump(),
                    "pipeline_time_ms": int(pipeline_time * 1000),
                    "debug_info": self.debug_info
                }
            }

        if decision.action == "ask_clarification":
            pipeline_time = time.time() - pipeline_start
            # Update all debug info with pipeline time
            for info in self.debug_info:
                info["pipeline_time_ms"] = int(pipeline_time * 1000)
            return {
                "type": "clarification",
                "message": decision.message,
                "metadata": {
                    "validation": validation_result.model_dump(),
                    "decision": decision.model_dump(),
                    "pipeline_time_ms": int(pipeline_time * 1000),
                    "debug_info": self.debug_info
                }
            }

        if decision.action == "create_plan":
            # Check datasource compatibility before creating plan
            datasource_check = self._validate_datasources(validation_result.relevant_databases)

            if not datasource_check["valid"]:
                pipeline_time = time.time() - pipeline_start
                # Update all debug info with pipeline time
                for info in self.debug_info:
                    info["pipeline_time_ms"] = int(pipeline_time * 1000)
                return {
                    "type": "datasource_error",
                    "message": datasource_check["error"],
                    "metadata": {
                        "validation": validation_result.model_dump(),
                        "decision": decision.model_dump(),
                        "datasource_check": datasource_check,
                        "pipeline_time_ms": int(pipeline_time * 1000),
                        "debug_info": self.debug_info
                    }
                }

            # Stage 3: Create query plan
            plan = self._create_plan(question, validation_result, conversation_history)

            if plan.needs_clarification:
                clarification_msg = self._format_clarification_questions(plan.clarification_questions)
                pipeline_time = time.time() - pipeline_start
                # Update all debug info with pipeline time
                for info in self.debug_info:
                    info["pipeline_time_ms"] = int(pipeline_time * 1000)
                return {
                    "type": "clarification",
                    "message": clarification_msg,
                    "metadata": {
                        "validation": validation_result.model_dump(),
                        "decision": decision.model_dump(),
                        "plan": plan.model_dump(),
                        "pipeline_time_ms": int(pipeline_time * 1000),
                        "debug_info": self.debug_info
                    }
                }

            # Stage 4: Execute plan with agentic SQL generation
            executor = get_executor(self.thread_id)
            executor.token_usage_callback = self.token_usage_callback  # Share token tracking

            execution_results = executor.execute_plan(question, plan)

            # Merge executor debug info
            self.debug_info.extend(executor.debug_info)

            # Check if execution failed
            if not all(result.success for result in execution_results):
                # Find first failed step
                failed_step = next(r for r in execution_results if not r.success)
                pipeline_time = time.time() - pipeline_start
                # Update all debug info with pipeline time
                for info in self.debug_info:
                    info["pipeline_time_ms"] = int(pipeline_time * 1000)

                return {
                    "type": "execution_error",
                    "message": f"Failed to execute step {failed_step.step_number}: {failed_step.error}",
                    "metadata": {
                        "validation": validation_result.model_dump(),
                        "decision": decision.model_dump(),
                        "plan": plan.model_dump(),
                        "execution_results": [r.model_dump() for r in execution_results],
                        "pipeline_time_ms": int(pipeline_time * 1000),
                        "debug_info": self.debug_info
                    }
                }

            # Stage 5: Generate summary from execution results
            summary = executor.generate_summary(question, plan, execution_results)

            # Merge final debug info
            self.debug_info.extend(executor.debug_info[len(execution_results):])  # Only new debug info

            pipeline_time = time.time() - pipeline_start
            # Update all debug info with pipeline time
            for info in self.debug_info:
                info["pipeline_time_ms"] = int(pipeline_time * 1000)

            return {
                "type": "answer",
                "message": summary.answer,
                "metadata": {
                    "validation": validation_result.model_dump(),
                    "decision": decision.model_dump(),
                    "plan": plan.model_dump(),
                    "execution_results": [r.model_dump() for r in execution_results],
                    "summary": summary.model_dump(),
                    "pipeline_time_ms": int(pipeline_time * 1000),
                    "debug_info": self.debug_info
                }
            }

        # Fallback
        pipeline_time = time.time() - pipeline_start
        # Update all debug info with pipeline time
        for info in self.debug_info:
            info["pipeline_time_ms"] = int(pipeline_time * 1000)
        return {
            "type": "error",
            "message": "I encountered an issue processing your question. Please try again.",
            "metadata": {
                "pipeline_time_ms": int(pipeline_time * 1000),
                "debug_info": self.debug_info
            }
        }

    def _validate_question(
        self,
        question: str,
        conversation_history: List[Dict[str, str]]
    ) -> ValidationResult:
        """Stage 1: Validate if question is relevant"""
        template = self.prompt_loader.load("validate_question")

        user_prompt = template.render_user_prompt(
            question=question,
            data_sources=self._format_data_sources(),
            conversation_history=self._format_conversation_history(conversation_history)
        )

        # Use structured output
        messages = [ConversationMessage(role="user", content=user_prompt)]

        result, usage = self.client.complete_structured(
            messages=messages,
            response_model=ValidationResult,
            system_prompt=template.system_prompt,
            temperature=template.temperature,
            model=template.model
        )

        # Track debug info
        self.debug_info.append({
            "stage": "validation",
            "model": template.model,
            "elapsed_ms": usage.get("elapsed_time_ms", 0),
            "tokens": usage,
            "pipeline_time_ms": 0  # Will be updated at the end
        })

        # Track token usage
        if self.token_usage_callback:
            self.token_usage_callback(usage)

        return result

    def _decide_action(
        self,
        question: str,
        validation: ValidationResult,
        conversation_history: List[Dict[str, str]]
    ) -> DecisionResult:
        """Stage 2: Decide what action to take"""
        template = self.prompt_loader.load("decide_action")

        user_prompt = template.render_user_prompt(
            question=question,
            is_relevant=str(validation.is_relevant),
            relevant_databases=", ".join(validation.relevant_databases),
            validation_reasoning=validation.reasoning,
            data_sources=self._format_data_sources(),
            conversation_history=self._format_conversation_history(conversation_history)
        )

        messages = [ConversationMessage(role="user", content=user_prompt)]

        result, usage = self.client.complete_structured(
            messages=messages,
            response_model=DecisionResult,
            system_prompt=template.system_prompt,
            temperature=template.temperature,
            model=template.model
        )

        # Track debug info
        self.debug_info.append({
            "stage": "decision",
            "model": template.model,
            "elapsed_ms": usage.get("elapsed_time_ms", 0),
            "tokens": usage,
            "pipeline_time_ms": 0  # Will be updated at the end
        })

        # Track token usage
        if self.token_usage_callback:
            self.token_usage_callback(usage)

        return result

    def _create_plan(
        self,
        question: str,
        validation: ValidationResult,
        conversation_history: List[Dict[str, str]]
    ) -> QueryPlan:
        """Stage 3: Create query execution plan"""
        template = self.prompt_loader.load("create_plan")

        # Load relevant database schemas with full table and column information
        database_schemas = self._format_database_schemas(validation.relevant_databases)

        user_prompt = template.render_user_prompt(
            question=question,
            relevant_databases=", ".join(validation.relevant_databases),
            database_schemas=database_schemas,
            conversation_history=self._format_conversation_history(conversation_history)
        )

        messages = [ConversationMessage(role="user", content=user_prompt)]

        result, usage = self.client.complete_structured(
            messages=messages,
            response_model=QueryPlan,
            system_prompt=template.system_prompt,
            temperature=template.temperature,
            model=template.model
        )

        # Track debug info
        self.debug_info.append({
            "stage": "planning",
            "model": template.model,
            "elapsed_ms": usage.get("elapsed_time_ms", 0),
            "tokens": usage,
            "pipeline_time_ms": 0  # Will be updated at the end
        })

        # Track token usage
        if self.token_usage_callback:
            self.token_usage_callback(usage)

        return result

    def _format_clarification_questions(self, questions) -> str:
        """Format clarification questions for user"""
        lines = ["I need some clarification to answer your question:\n"]
        for i, q in enumerate(questions, 1):
            lines.append(f"{i}. {q.question}")
        return "\n".join(lines)

    def _validate_datasources(self, databases: List[str]) -> Dict[str, Any]:
        """Validate that databases can be queried together"""
        try:
            manager = get_manager()
            return manager.validate_databases(databases)
        except Exception as e:
            return {
                "valid": False,
                "error": f"Datasource validation failed: {str(e)}"
            }

    def _format_plan_summary(self, plan: QueryPlan) -> str:
        """Format plan summary for user"""
        lines = [
            f"I understand. {plan.summary}\n",
            "Here's my plan:",
        ]

        for step in plan.steps:
            lines.append(f"\n{step.step_number}. {step.description}")
            lines.append(f"   - Databases: {', '.join(step.databases)}")
            lines.append(f"   - Tables: {', '.join(step.tables)}")
            lines.append(f"   - Operation: {step.operation}")

        lines.append(f"\n{plan.expected_output}")
        lines.append("\n(Note: SQL execution is not yet implemented)")

        return "\n".join(lines)


def get_orchestrator(thread_id: Optional[str] = None) -> QueryOrchestrator:
    """Create a new orchestrator instance for a thread"""
    return QueryOrchestrator(thread_id=thread_id)
