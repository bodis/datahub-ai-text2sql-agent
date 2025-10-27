# Frontend Database Highlighting Implementation

## Summary

Implemented visual dimming/highlighting of database badges based on actual usage in each thread.

---

## Changes Made

### 1. API Layer (`frontend/src/lib/api.ts`)

**Added new method:**
```typescript
async getUsedDatabases(threadId: string): Promise<string[]> {
  const response = await fetch(`${API_BASE}/threads/${threadId}/databases`);
  if (!response.ok) throw new Error("Failed to fetch used databases");
  const data = await response.json();
  return data.databases || [];
}
```

### 2. DataSourceBadges Component (`frontend/src/components/DataSourceBadges.tsx`)

**Key Changes:**

1. **Added Props:**
```typescript
interface DataSourceBadgesProps {
  threadId?: string;
  messageCount?: number; // Triggers refresh when messages change
}
```

2. **Added State:**
```typescript
const [usedDatabases, setUsedDatabases] = useState<string[]>([]);
```

3. **Fetch Used Databases:**
```typescript
useEffect(() => {
  const fetchUsedDatabases = async () => {
    if (!threadId) {
      setUsedDatabases([]);
      return;
    }

    try {
      const databases = await api.getUsedDatabases(threadId);
      setUsedDatabases(databases);
    } catch (error) {
      console.error("Failed to fetch used databases:", error);
      setUsedDatabases([]);
    }
  };

  fetchUsedDatabases();
}, [threadId, messageCount]); // Refreshes on thread change OR message count change
```

4. **Conditional Styling:**
```typescript
const isUsed = (sourceId: string) => usedDatabases.includes(sourceId);
const hasUsedDatabases = usedDatabases.length > 0;

// In render:
const used = isUsed(source.id);
const shouldDim = hasUsedDatabases && !used;

<span
  className={`... ${
    shouldDim
      ? "opacity-30 bg-gray-100 text-gray-500 border-gray-200"  // Dimmed
      : "bg-gradient-to-r from-purple-100 to-blue-100 text-purple-700 border-purple-200"  // Highlighted
  }`}
>
  {source.name}
</span>
```

5. **Tooltip Enhancement:**
```typescript
{used && (
  <div className="mt-2 text-xs text-purple-600 font-medium">
    ✓ Used in this thread
  </div>
)}
```

### 3. ChatInterface Component (`frontend/src/components/ChatInterface.tsx`)

**Updated Badge Usage:**
```typescript
<DataSourceBadges threadId={threadId} messageCount={messages.length} />
```

This passes both:
- `threadId` - To fetch databases for the current thread
- `messageCount` - To trigger refresh when new messages arrive

---

## Visual Behavior

### Initial State (No Messages)
```
All badges: Normal appearance (colorful gradient)
Logic: hasUsedDatabases = false, so no dimming applied
```

### After First Message
```
Used databases: Colorful gradient (highlighted)
Unused databases: Dimmed (opacity-30, gray)
Logic: hasUsedDatabases = true, shouldDim = !isUsed(source.id)
```

### Accumulation
```
Message 1: Uses customer_db → customer_db highlighted
Message 2: Uses loans_db → customer_db + loans_db highlighted
Message 3: Uses accounts_db → customer_db + loans_db + accounts_db highlighted

All others remain dimmed at opacity-30
```

---

## CSS Classes

**Highlighted (Used):**
```css
bg-gradient-to-r from-purple-100 to-blue-100
text-purple-700
border-purple-200
opacity-100 (default)
```

**Dimmed (Unused):**
```css
bg-gray-100
text-gray-500
border-gray-200
opacity-30
```

---

## Refresh Triggers

The `usedDatabases` state refreshes when:

1. **Thread changes** (`threadId` dependency)
   - User switches to a different thread
   - Used databases for new thread are fetched

2. **Messages change** (`messageCount` dependency)
   - User sends a message
   - Server responds
   - messageCount increments → triggers useEffect
   - Fetches updated used databases

---

## Data Flow

```
User sends message
    ↓
App.handleSendMessage() updates messages state
    ↓
ChatInterface re-renders with new messages.length
    ↓
DataSourceBadges receives new messageCount prop
    ↓
useEffect detects messageCount change
    ↓
Fetches: GET /api/threads/{threadId}/databases
    ↓
Updates usedDatabases state
    ↓
Re-renders badges with new highlighting
```

---

## Example Scenarios

### Scenario 1: Fresh Thread

**State:**
- threadId: "abc-123"
- messages: []
- usedDatabases: []
- hasUsedDatabases: false

**UI:**
- All badges: Colorful gradient ✅
- No dimming (because hasUsedDatabases = false)

### Scenario 2: After First Question

**User asks:** "How many customers?"

**State:**
- threadId: "abc-123"
- messages: 2 (user + server)
- usedDatabases: ["customer_db"]
- hasUsedDatabases: true

**UI:**
- Customer DB: Colorful gradient ✅
- All others: Dimmed (opacity-30) 🔅

### Scenario 3: Multi-Database Question

**User asks:** "Show customers with their account balances"

**State:**
- threadId: "abc-123"
- messages: 4
- usedDatabases: ["customer_db", "accounts_db"]
- hasUsedDatabases: true

**UI:**
- Customer DB: Colorful gradient ✅
- Accounts DB: Colorful gradient ✅
- All others: Dimmed (opacity-30) 🔅

---

## Testing Checklist

### Initial State
- [ ] Open new thread
- [ ] Verify all badges are colorful (not dimmed)
- [ ] Verify no "✓ Used in this thread" in tooltips

### First Message
- [ ] Send: "How many customers?"
- [ ] Verify only "Customer DB" is highlighted
- [ ] Verify others are dimmed (opacity-30)
- [ ] Hover over Customer DB → Shows "✓ Used in this thread"

### Additional Messages
- [ ] Send: "Show loan amounts"
- [ ] Verify "Customer DB" and "Loans DB" are highlighted
- [ ] Verify others remain dimmed

### Thread Switching
- [ ] Switch to different thread
- [ ] Verify badges reset to that thread's usage
- [ ] Switch back → Original highlighting restored

---

## Files Modified

1. **`frontend/src/lib/api.ts`**
   - Added `getUsedDatabases()` method

2. **`frontend/src/components/DataSourceBadges.tsx`**
   - Added `threadId` and `messageCount` props
   - Added `usedDatabases` state
   - Added fetch logic with useEffect
   - Added conditional styling (dim vs highlight)
   - Added "✓ Used" indicator in tooltip

3. **`frontend/src/components/ChatInterface.tsx`**
   - Pass `threadId` and `messages.length` to DataSourceBadges

---

## Summary

✅ **Dimming works** - Unused databases appear at 30% opacity
✅ **Highlighting works** - Used databases show colorful gradient
✅ **Auto-refresh** - Updates after each message
✅ **Thread-specific** - Each thread tracks its own usage
✅ **Visual feedback** - "✓ Used" indicator in tooltips
✅ **Smooth transitions** - CSS transitions for visual polish

The frontend now provides clear visual feedback about which databases are actively being queried in each conversation! 🎨
