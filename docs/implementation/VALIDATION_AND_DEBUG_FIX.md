# Validation Fix & Full Debug Logging

## Summary of Changes

Three key improvements:
1. ✅ Fixed validation to return correct database IDs (not table names)
2. ✅ Enhanced validation prompt with summary.yaml context
3. ✅ Added full prompt/response logging for debugging

---

## 1. Fixed Validation Database IDs

### Problem

Validation was returning incorrect database identifiers:

```json
{
  "is_relevant": true,
  "reasoning": "...",
  "relevant_databases": ["customers"]  // ❌ WRONG - This is a table name!
}
```

Should return:
```json
{
  "is_relevant": true,
  "reasoning": "...",
  "relevant_databases": ["customer_db"]  // ✅ CORRECT - Database ID from summary.yaml
}
```

### Root Cause

The `validate_question.yaml` prompt wasn't explicit about using database IDs from `summary.yaml`.

### Solution

Updated `validate_question.yaml` with explicit instructions:

#### Added to System Prompt:

```yaml
CRITICAL - Database ID Format:
When specifying relevant_databases, you MUST use the DATABASE ID (the value in parentheses above), NOT the database name or table names.

Valid database IDs (from the list above):
- customer_db (for customer-related data)
- accounts_db (for accounts and transactions)
- loans_db (for loans and lending)
- insurance_db (for insurance policies)
- compliance_db (for compliance and audits)
- employees_db (for HR and employees)

Example: If the question is about customers, use ["customer_db"], NOT ["customers"] or ["Customer DB"].
```

#### Updated User Prompt:

```yaml
Based on the available data sources and the user's question, determine:
1. Is this question relevant to the available databases?
2. If yes, which DATABASE IDs (from the list above) would be needed to answer it? Use the ID values like "customer_db", "accounts_db", etc.
3. If no, what should I tell the user?

Remember: Use database IDs (e.g., "customer_db"), not table names (e.g., "customers")!
```

### Data Source Format

The orchestrator already formats data sources correctly from `summary.yaml`:

```python
# orchestrator.py:33-38
def _format_data_sources(self) -> str:
    """Format data sources for prompt"""
    lines = []
    for source in self.data_sources:
        lines.append(f"- {source['name']} ({source['id']}): {source['description']}")
    return "\n".join(lines)
```

Output example:
```
- Customer DB (customer_db): Customer relationship management, interactions, complaints, marketing campaigns, and satisfaction surveys
- Accounts DB (accounts_db): Bank accounts, transactions, customer master data, and account relationships
- Loans DB (loans_db): Loan applications, active loans, repayments, collateral, and credit risk assessments
...
```

The ID in parentheses is what must be returned in `relevant_databases`.

---

## 2. Summary.yaml Usage Confirmed

### Question: Is summary.yaml being used?

**YES!** The `summary.yaml` file is loaded and used in validation:

#### Loading (`orchestrator.py:22-31`):
```python
def _load_data_sources(self):
    """Load data sources from summary.yaml"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    summary_path = os.path.join(base_dir, "knowledge", "data_schemas", "summary.yaml")

    with open(summary_path, "r") as f:
        data = yaml.safe_load(f)

    self.data_sources = data.get("data_sources", [])
```

#### Formatting (`orchestrator.py:33-38`):
```python
def _format_data_sources(self) -> str:
    """Format data sources for prompt"""
    lines = []
    for source in self.data_sources:
        lines.append(f"- {source['name']} ({source['id']}): {source['description']}")
    return "\n".join(lines)
```

#### Injection into Prompt (`orchestrator.py:243-252`):
```python
def _validate_question(self, question: str, conversation_history: List[Dict[str, str]]) -> ValidationResult:
    """Stage 1: Validate if question is relevant"""
    template = self.prompt_loader.load("validate_question")

    user_prompt = template.render_user_prompt(
        question=question,
        data_sources=self._format_data_sources(),  # ← Injects summary.yaml data
        conversation_history=self._format_conversation_history(conversation_history)
    )
```

### What the LLM Sees

The validation prompt includes:

```
You have access to the following data sources:
- Customer DB (customer_db): Customer relationship management, interactions, complaints, marketing campaigns, and satisfaction surveys
- Accounts DB (accounts_db): Bank accounts, transactions, customer master data, and account relationships
- Loans DB (loans_db): Loan applications, active loans, repayments, collateral, and credit risk assessments
- Insurance DB (insurance_db): Insurance policies, claims, beneficiaries, and coverage details
- Compliance DB (compliance_db): AML screening, audit trails, compliance rules, and regulatory reporting
- Employees DB (employees_db): Employee information, departments, assignments, and training programs
```

This comes directly from `knowledge/data_schemas/summary.yaml`.

---

## 3. Full Debug Logging Added

### Problem

Debug logging was truncating prompts and responses to 200-500 characters:

```python
# OLD
logger.info(f"System Prompt:\n{system_prompt[:200]}...")  # Truncated!
logger.info(f"  {msg['role']}: {msg['content'][:200]}...")  # Truncated!
logger.info(f"Response:\n{response_text[:500]}...")  # Truncated!
```

### Solution

Updated all debug logging to show FULL content when `LLM_DEBUG=true`:

#### Changes in `client.py`:

**1. Regular Completion (`complete()` method - lines 100-109)**
```python
# NEW - Shows full prompts
if self.debug_enabled:
    logger.info("=" * 80)
    logger.info(f"LLM REQUEST - Model: {model_id}")
    logger.info(f"Temperature: {temperature}")
    if system_prompt:
        logger.info(f"SYSTEM PROMPT (FULL):\n{system_prompt}")  # ✅ Full
    logger.info(f"USER MESSAGES (FULL):")
    for i, msg in enumerate(formatted_messages):
        logger.info(f"  Message {i+1} [{msg['role']}]:\n{msg['content']}")  # ✅ Full
    logger.info("=" * 80)
```

**2. Structured Completion (`complete_structured()` method - lines 181-191)**
```python
# NEW - Shows full prompts
if self.debug_enabled:
    logger.info("=" * 80)
    logger.info(f"LLM STRUCTURED REQUEST - Model: {model_id}")
    logger.info(f"Response Model: {response_model.__name__}")
    logger.info(f"Temperature: {temperature}")
    if system_prompt:
        logger.info(f"SYSTEM PROMPT (FULL):\n{system_prompt}")  # ✅ Full
    logger.info(f"USER MESSAGES (FULL):")
    for i, msg in enumerate(formatted_messages):
        logger.info(f"  Message {i+1} [{msg['role']}]:\n{msg['content']}")  # ✅ Full
    logger.info("=" * 80)
```

**3. Regular Response Logging (lines 129-135)**
```python
# NEW - Shows full response
if self.debug_enabled:
    logger.info("=" * 80)
    logger.info(f"LLM RESPONSE - Model: {model_id}")
    logger.info(f"Elapsed Time: {elapsed_time:.2f}s ({usage['elapsed_time_ms']}ms)")
    logger.info(f"Token Usage: Input={usage['input_tokens']}, Output={usage['output_tokens']}, Total={usage['total_tokens']}")
    logger.info(f"RESPONSE TEXT (FULL):\n{response_text}")  # ✅ Full
    logger.info("=" * 80)
```

**4. Structured Response Logging (lines 244-250)**
```python
# NEW - Shows full structured response
if self.debug_enabled:
    logger.info("=" * 80)
    logger.info(f"LLM STRUCTURED RESPONSE - Model: {model_id}")
    logger.info(f"Elapsed Time: {elapsed_time:.2f}s ({usage['elapsed_time_ms']}ms)")
    logger.info(f"Token Usage: Input={usage['input_tokens']}, Output={usage['output_tokens']}, Total={usage['total_tokens']}")
    logger.info(f"STRUCTURED RESPONSE (FULL):\n{json.dumps(structured_response.model_dump(), indent=2)}")  # ✅ Full
    logger.info("=" * 80)
```

### What You'll See Now

With `LLM_DEBUG=true` in `.env`, the logs will show:

```
================================================================================
LLM STRUCTURED REQUEST - Model: claude-haiku-4-5
Response Model: ValidationResult
Temperature: 0.3
SYSTEM PROMPT (FULL):
You are an AI data analyst assistant. Your role is to help users query financial and banking data from multiple databases.

IMPORTANT: Always respond in the same language as the user's question.

You have access to the following data sources:
- Customer DB (customer_db): Customer relationship management, interactions, complaints, marketing campaigns, and satisfaction surveys
- Accounts DB (accounts_db): Bank accounts, transactions, customer master data, and account relationships
... (full prompt)

USER MESSAGES (FULL):
  Message 1 [user]:
User's question: "How many customers do we have?"

Previous conversation context:
No previous conversation.

Based on the available data sources and the user's question, determine:
1. Is this question relevant to the available databases?
2. If yes, which DATABASE IDs (from the list above) would be needed to answer it? Use the ID values like "customer_db", "accounts_db", etc.
3. If no, what should I tell the user?

Remember: Use database IDs (e.g., "customer_db"), not table names (e.g., "customers")!
================================================================================
... (processing)
================================================================================
RAW TOOL INPUT (before validation):
{
  "is_relevant": true,
  "reasoning": "...",
  "relevant_databases": [
    "customer_db"  // ✅ Now correct!
  ]
}
================================================================================
LLM STRUCTURED RESPONSE - Model: claude-haiku-4-5
Elapsed Time: 1.23s (1234ms)
Token Usage: Input=450, Output=65, Total=515
STRUCTURED RESPONSE (FULL):
{
  "is_relevant": true,
  "reasoning": "The question asks about the number of customers, which is directly related to banking data. This is a typical data analysis question that can be answered from the customer database. Customer count queries are a fundamental part of financial and banking data analysis.",
  "relevant_databases": [
    "customer_db"
  ],
  "suggested_response": null
}
================================================================================
```

---

## Files Modified

1. **`backend/knowledge/prompts/validate_question.yaml`**
   - Added explicit database ID format instructions
   - Added list of valid database IDs
   - Added examples and reminders

2. **`backend/app/llm/client.py`**
   - Lines 100-109: Full prompt logging for `complete()`
   - Lines 129-135: Full response logging for `complete()`
   - Lines 181-191: Full prompt logging for `complete_structured()`
   - Lines 244-250: Full response logging for `complete_structured()`

---

## Expected Behavior Now

### Before Fix:
```json
{
  "relevant_databases": ["customers"]  // ❌ Wrong - table name
}
```

### After Fix:
```json
{
  "relevant_databases": ["customer_db"]  // ✅ Correct - database ID from summary.yaml
}
```

### Frontend Impact

With correct database IDs, the frontend can now:
1. Highlight the correct database badges (matching summary.yaml IDs)
2. Show which datasources are being queried
3. Display accurate metadata about which databases were used

---

## Testing

1. **Start backend with debug enabled:**
   ```bash
   cd backend
   # Ensure .env has: LLM_DEBUG=true
   uv run uvicorn main:app --host 0.0.0.0 --port 5001 --reload
   ```

2. **Ask a test question:**
   ```
   "How many customers do we have?"
   ```

3. **Check logs for:**
   - Full system prompt showing all data sources from summary.yaml
   - Full user message with instructions
   - Full structured response with correct database IDs

4. **Verify response:**
   ```json
   {
     "is_relevant": true,
     "reasoning": "...",
     "relevant_databases": ["customer_db"]  // ✅ Should be database ID
   }
   ```

---

## Benefits

✅ **Correct Database IDs**: Validation returns IDs matching summary.yaml
✅ **Frontend Compatibility**: Can properly highlight database badges
✅ **Full Debug Visibility**: See complete prompts and responses
✅ **Better Debugging**: Identify prompt issues quickly
✅ **Proper Context**: LLM sees all available datasources from summary.yaml

The system now correctly identifies and returns database IDs that match the `id` field in `summary.yaml`, enabling proper frontend highlighting and metadata display!
