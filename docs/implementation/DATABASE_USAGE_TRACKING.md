# Database Usage Tracking & UI Highlighting

## Summary

Implemented thread-level database usage tracking to highlight only the databases that have been actively used in each conversation thread.

---

## Problem

The UI showed all available databases highlighted at the top of every thread, even if they hadn't been used. This created visual clutter and didn't provide useful context about which databases were actually queried.

---

## Solution

Track which databases are used in each thread and only highlight those databases in the UI.

### Backend Changes

#### 1. Storage Layer (`app/storage.py`)

**Added to Interface:**
```python
@abstractmethod
def add_used_databases(self, thread_id: str, databases: List[str]) -> None:
    """Add databases that were used in this thread"""
    pass

@abstractmethod
def get_used_databases(self, thread_id: str) -> List[str]:
    """Get all databases that have been used in this thread"""
    pass
```

**Implementation in InMemoryStorage:**
```python
def __init__(self):
    # ...
    self.used_databases: Dict[str, set] = {}  # thread_id -> set of database IDs

def create_thread(self, name: str) -> Dict:
    # ...
    self.used_databases[thread_id] = set()  # Initialize empty set
    return thread

def add_used_databases(self, thread_id: str, databases: List[str]) -> None:
    """Add databases that were used in this thread"""
    if thread_id not in self.threads:
        raise ValueError(f"Thread {thread_id} not found")

    if thread_id not in self.used_databases:
        self.used_databases[thread_id] = set()

    # Add databases to the set (automatically handles duplicates)
    for db in databases:
        self.used_databases[thread_id].add(db)

def get_used_databases(self, thread_id: str) -> List[str]:
    """Get all databases that have been used in this thread"""
    return sorted(list(self.used_databases.get(thread_id, set())))
```

**Key Features:**
- Uses a `set` to automatically handle duplicates
- Accumulates databases across all messages in the thread
- Returns sorted list for consistent UI display

#### 2. Orchestrator (`app/llm/orchestrator.py`)

**Tracks databases after validation:**
```python
# Stage 1: Validate question
validation_result = self._validate_question(question, conversation_history)

# Track databases used in this thread (if relevant)
if validation_result.is_relevant and validation_result.relevant_databases and self.thread_id:
    try:
        storage.add_used_databases(self.thread_id, validation_result.relevant_databases)
    except Exception as e:
        # Don't fail the request if tracking fails
        logging.warning(f"Failed to track used databases: {e}")
```

**When tracking happens:**
- After validation stage identifies relevant databases
- Before any other processing (decision, planning, execution)
- Only if question is relevant and has identified databases
- Fails gracefully if storage error occurs

#### 3. API Endpoint (`app/routes.py`)

**New endpoint:**
```python
@api_bp.route("/threads/<thread_id>/databases", methods=["GET"])
def get_thread_databases(thread_id):
    """Get databases that have been used in this thread"""
    thread = storage.get_thread(thread_id)
    if not thread:
        return jsonify({"error": "Thread not found"}), 404

    databases = storage.get_used_databases(thread_id)
    return jsonify({"databases": databases})
```

**Response format:**
```json
{
  "databases": ["customer_db", "accounts_db"]
}
```

---

## Frontend Integration

### API Endpoint

```
GET /api/threads/{thread_id}/databases
```

**Response:**
```json
{
  "databases": ["customer_db", "accounts_db", "loans_db"]
}
```

### Implementation Steps

1. **Fetch used databases when thread loads:**
```typescript
// In your ChatInterface or similar component
const [usedDatabases, setUsedDatabases] = useState<string[]>([]);

useEffect(() => {
  if (threadId) {
    fetch(`/api/threads/${threadId}/databases`)
      .then(res => res.json())
      .then(data => setUsedDatabases(data.databases || []))
      .catch(err => console.error('Failed to fetch used databases:', err));
  }
}, [threadId]);
```

2. **Refresh after each message:**
```typescript
// After sending a message and getting a response
const sendMessage = async (content: string) => {
  // ... send message logic ...

  // Refresh used databases
  const dbResponse = await fetch(`/api/threads/${threadId}/databases`);
  const dbData = await dbResponse.json();
  setUsedDatabases(dbData.databases || []);
};
```

3. **Highlight only used databases:**
```typescript
// In your DataSourceBadges component
<div className="database-badges">
  {allDataSources.map(source => (
    <Badge
      key={source.id}
      className={usedDatabases.includes(source.id) ? 'highlighted' : 'dimmed'}
    >
      {source.name}
    </Badge>
  ))}
</div>
```

**CSS for highlighting:**
```css
.database-badges .highlighted {
  opacity: 1;
  background-color: #3b82f6; /* Blue highlight */
  border: 2px solid #2563eb;
}

.database-badges .dimmed {
  opacity: 0.3;
  background-color: #e5e7eb; /* Gray */
  border: 1px solid #d1d5db;
}
```

---

## Behavior Examples

### Example 1: Fresh Thread

**Initial state:**
```
User opens new thread
→ GET /api/threads/{thread_id}/databases
→ Response: {"databases": []}
→ UI: All badges dimmed (no databases used yet)
```

### Example 2: First Question

**User asks:** "How many customers do we have?"

```
1. Backend validates question
2. Identifies relevant_databases: ["customer_db"]
3. Calls storage.add_used_databases(thread_id, ["customer_db"])
4. Returns answer to user

Frontend refreshes:
→ GET /api/threads/{thread_id}/databases
→ Response: {"databases": ["customer_db"]}
→ UI: Only "Customer DB" badge is highlighted
```

### Example 3: Multi-Database Question

**User asks:** "Show customers with their account balances"

```
1. Backend validates question
2. Identifies relevant_databases: ["customer_db", "accounts_db"]
3. Calls storage.add_used_databases(thread_id, ["customer_db", "accounts_db"])
4. Returns answer to user

Frontend refreshes:
→ GET /api/threads/{thread_id}/databases
→ Response: {"databases": ["accounts_db", "customer_db"]}
→ UI: "Customer DB" and "Accounts DB" badges are highlighted
```

### Example 4: Accumulation Across Messages

**Message 1:** "How many customers?" → Uses `customer_db`
**Message 2:** "Show loan amounts" → Uses `loans_db`
**Message 3:** "List insurance policies" → Uses `insurance_db`

```
After all messages:
→ GET /api/threads/{thread_id}/databases
→ Response: {"databases": ["customer_db", "insurance_db", "loans_db"]}
→ UI: Three badges highlighted (sorted alphabetically)
```

---

## Data Flow

```
User sends message
    ↓
Backend validates question
    ↓
Identifies relevant databases: ["customer_db", "accounts_db"]
    ↓
storage.add_used_databases(thread_id, ["customer_db", "accounts_db"])
    ↓
Thread's used_databases set: {"customer_db", "accounts_db"}
    ↓
Returns answer to user
    ↓
Frontend requests: GET /api/threads/{thread_id}/databases
    ↓
Backend returns: {"databases": ["accounts_db", "customer_db"]}
    ↓
Frontend highlights only these badges
```

---

## Benefits

✅ **Clearer Context**: Users see which databases are actually being used
✅ **Visual Feedback**: Immediate indication of what data sources are involved
✅ **Persistent State**: Database usage persists across the entire thread
✅ **No Clutter**: Unused databases remain dimmed
✅ **Automatic Updates**: Tracking happens automatically on every question
✅ **Thread-Specific**: Each thread tracks its own database usage independently

---

## Testing

### Backend Test

```bash
# Start backend
cd backend
uv run uvicorn main:app --host 0.0.0.0 --port 5001 --reload

# Create thread
curl -X POST http://localhost:5001/api/threads \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Thread"}'
# Response: {"id": "abc-123", ...}

# Check initial databases (should be empty)
curl http://localhost:5001/api/threads/abc-123/databases
# Response: {"databases": []}

# Send a message
curl -X POST http://localhost:5001/api/threads/abc-123/messages \
  -H "Content-Type: application/json" \
  -d '{"content":"How many customers do we have?"}'

# Check databases again
curl http://localhost:5001/api/threads/abc-123/databases
# Response: {"databases": ["customer_db"]}

# Send another message
curl -X POST http://localhost:5001/api/threads/abc-123/messages \
  -H "Content-Type: application/json" \
  -d '{"content":"Show loan amounts"}'

# Check databases again
curl http://localhost:5001/api/threads/abc-123/databases
# Response: {"databases": ["customer_db", "loans_db"]}
```

### Frontend Test

1. Open a new thread
2. Verify all database badges are dimmed
3. Ask: "How many customers do we have?"
4. Verify only "Customer DB" badge is highlighted
5. Ask: "Show account balances"
6. Verify "Customer DB" and "Accounts DB" are highlighted
7. Ask: "List loan applications"
8. Verify "Customer DB", "Accounts DB", and "Loans DB" are highlighted

---

## Files Modified

1. **`backend/app/storage.py`**
   - Added `used_databases` dict to track databases per thread
   - Added `add_used_databases()` method
   - Added `get_used_databases()` method
   - Updated `create_thread()` to initialize empty set

2. **`backend/app/llm/orchestrator.py`**
   - Imported storage module
   - Added database tracking after validation
   - Graceful error handling for tracking failures

3. **`backend/app/routes.py`**
   - Added `GET /api/threads/<thread_id>/databases` endpoint
   - Returns list of database IDs used in the thread

---

## Frontend Requirements

To implement this feature, the frontend needs to:

1. **Call the new endpoint** when a thread is loaded
2. **Refresh database list** after each message
3. **Apply highlighting styles** based on the returned database list
4. **Dim non-used badges** for visual distinction

**Example component structure:**
```typescript
interface DataSourceBadgesProps {
  allDataSources: DataSource[];
  usedDatabases: string[];
}

const DataSourceBadges: React.FC<DataSourceBadgesProps> = ({
  allDataSources,
  usedDatabases
}) => {
  return (
    <div className="flex gap-2">
      {allDataSources.map(source => (
        <Badge
          key={source.id}
          variant={usedDatabases.includes(source.id) ? 'default' : 'outline'}
          className={
            usedDatabases.includes(source.id)
              ? 'opacity-100 bg-blue-500'
              : 'opacity-30 bg-gray-200'
          }
        >
          <Icon name={source.icon} />
          {source.name}
        </Badge>
      ))}
    </div>
  );
};
```

---

## Summary

✅ **Backend tracking implemented** - Databases tracked per thread automatically
✅ **API endpoint added** - `GET /api/threads/{thread_id}/databases`
✅ **Persistent across messages** - Accumulates all databases used in thread
✅ **Automatic deduplication** - Uses sets to handle duplicates
✅ **Ready for frontend integration** - Simple REST API call

The backend is ready! The frontend just needs to:
1. Fetch the used databases from the new endpoint
2. Highlight badges that match the returned database IDs
3. Dim the rest

This provides clear visual feedback about which data sources are actually involved in each conversation! 🎨
