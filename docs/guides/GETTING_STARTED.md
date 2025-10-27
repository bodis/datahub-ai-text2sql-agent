# Getting Started Guide

Complete setup and usage guide for the AI Data Agent.

---

## Prerequisites

### Required Software

- **Python 3.10+** - Backend runtime
- **Node.js 18+** - Frontend development
- **uv** - Python package manager ([install](https://github.com/astral-sh/uv))
- **npm** - Node package manager (comes with Node.js)

### Optional

- **PostgreSQL 14+** - For real database connections
- **Git** - Version control

### API Keys

- **Anthropic API Key** - Required for LLM functionality
  - Get one at: https://console.anthropic.com/
  - Free tier available for testing

---

## Quick Start (5 Minutes)

### 1. Clone Repository

```bash
git clone <repository-url>
cd ai_data_agent
```

### 2. Backend Setup

```bash
cd backend

# Copy environment template
cp .env.example .env

# Edit .env and add your API key
nano .env  # or use your favorite editor

# Install dependencies
uv sync

# Start backend
uv run uvicorn main:app --host 0.0.0.0 --port 5001 --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:5001
INFO:     Application startup complete.
INFO:     Registered PostgreSQL datasource: customer_db_source
INFO:     Registered PostgreSQL datasource: accounts_db_source
...
INFO:     Loaded 6 datasources and 6 database mappings
```

### 3. Frontend Setup

Open a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

**Expected output:**
```
  VITE ready in 500 ms
  ➜  Local:   http://localhost:3001/
```

### 4. Open Browser

Navigate to: http://localhost:3001

---

## Environment Configuration

### Backend `.env` File

```bash
# Anthropic API Configuration
ANTHROPIC_API_KEY=sk-ant-api03-...  # ← ADD YOUR KEY HERE

# Model Configuration
ANTHROPIC_WEAK_MODEL=claude-haiku-4-5
ANTHROPIC_PLANNING_MODEL=claude-sonnet-4-5-20250929
ANTHROPIC_DEVELOPER_MODEL=claude-sonnet-4-5-20250929

# Token limits
ANTHROPIC_MAX_TOKENS=4096

# Debug mode (set to true to enable detailed logging)
LLM_DEBUG=true

# PostgreSQL Data Source Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Individual database names
POSTGRES_CUSTOMER_DB=customer_db
POSTGRES_ACCOUNTS_DB=accounts_db
POSTGRES_LOANS_DB=loans_db
POSTGRES_INSURANCE_DB=insurance_db
POSTGRES_COMPLIANCE_DB=compliance_db
POSTGRES_EMPLOYEES_DB=employees_db
```

### Important Settings

**`ANTHROPIC_API_KEY`** (Required)
- Your Anthropic API key
- Get from: https://console.anthropic.com/

**`LLM_DEBUG`** (Optional, default: false)
- Set to `true` to see full LLM prompts and responses
- Useful for debugging and understanding how the system works
- Warning: Produces verbose logs

**PostgreSQL Settings** (Optional)
- Only needed if connecting to real databases
- Default values work for local PostgreSQL installation
- Can leave as-is if not using actual databases

---

## First Steps

### 1. Create a Thread

Click **"New Thread"** in the sidebar.

### 2. Ask a Question

Try these example questions:

**Simple:**
```
How many customers do we have?
```

**Complex:**
```
Show me the top 5 customers by account balance
```

**Multi-step:**
```
Which customers have both loans and insurance policies?
```

### 3. Observe the Response

Watch as:
1. Database badges light up (showing which databases are used)
2. Token counter updates
3. Response streams back
4. Debug panel shows LLM interactions (click "Debug" to expand)

---

## Understanding the UI

### Thread Sidebar

- **New Thread** - Creates fresh conversation
- **Thread List** - Shows all your threads
- **Select Thread** - Click to switch between conversations

### Chat Interface

**Top Bar:**
- **Database Badges** - Shows available databases
  - Dimmed (gray) = not used yet
  - Colorful = used in this thread
  - Hover for details

- **Token Display** - Real-time token usage
  - Input tokens
  - Output tokens
  - Total tokens
  - Number of LLM calls

**Messages:**
- **You** - Your questions (purple gradient)
- **Server** - AI responses (blue gradient)
- **Debug Panel** - Click to see LLM details

---

## Testing the System

### Test 1: Simple Query

**Question:**
```
How many customers do we have?
```

**Expected:**
- Uses `customer_db` (badge lights up)
- Single step execution
- Response: "We have [number] customers..."
- Tokens: ~4,000-6,000

### Test 2: Cross-Database Query

**Question:**
```
Show me customers with their account balances
```

**Expected:**
- Uses `customer_db` and `accounts_db` (both badges light up)
- Multi-step execution (2-3 steps)
- Response: Table or list of customers with balances
- Tokens: ~10,000-15,000

### Test 3: Aggregation

**Question:**
```
What's the average loan amount?
```

**Expected:**
- Uses `loans_db` (badge lights up)
- Single step with aggregation
- Response: "The average loan amount is $[amount]..."
- Tokens: ~5,000-8,000

### Test 4: Error Recovery

**Question:**
```
How many policies are there?
```

**Expected:**
- System might initially use wrong table name
- Automatic retry with corrected SQL
- Final success after 1-2 retries
- Debug panel shows retry attempts

---

## Debugging

### Enable Debug Mode

1. Edit `backend/.env`
2. Set `LLM_DEBUG=true`
3. Restart backend
4. Check terminal for detailed logs

### Debug Output

You'll see:
```
================================================================================
LLM STRUCTURED REQUEST - Model: claude-haiku-4-5
Response Model: ValidationResult
Temperature: 0.3
SYSTEM PROMPT (FULL):
You are an AI data analyst assistant...
[full prompt]

USER MESSAGES (FULL):
  Message 1 [user]:
User's question: "How many customers do we have?"
[full message]
================================================================================
```

### Common Debug Points

**Check Validation:**
- Is question marked as relevant?
- Are correct databases identified?

**Check Planning:**
- Are steps logical?
- Are correct tables mentioned?

**Check SQL Generation:**
- Is SQL syntactically correct?
- Are table names matching schema?

**Check Execution:**
- Any errors in SQL execution?
- How many retries needed?

---

## Common Issues

### Issue: "Failed to fetch threads"

**Cause:** Backend not running

**Solution:**
```bash
cd backend
uv run uvicorn main:app --host 0.0.0.0 --port 5001 --reload
```

### Issue: "ANTHROPIC_API_KEY not found"

**Cause:** Missing or incorrect API key

**Solution:**
1. Check `backend/.env` exists
2. Verify API key is correct
3. Restart backend

### Issue: "No datasources loaded"

**Cause:** Missing PostgreSQL configuration

**Solution:**
- Check `backend/knowledge/datasources.yaml`
- Verify environment variables in `.env`
- Check logs for connection errors

### Issue: Database badges not updating

**Cause:** Frontend not fetching updates

**Solution:**
1. Check browser console for errors
2. Verify backend API is accessible
3. Refresh page

### Issue: Responses are generic

**Cause:** No real database connections

**Solution:**
- System works with schema files only (no actual data)
- For real queries, set up PostgreSQL databases
- See [Adding Databases](./ADDING_DATABASES.md)

---

## Next Steps

### Learn More

1. **[System Architecture](../architecture/SYSTEM_ARCHITECTURE.md)** - Understand how it works
2. **[Agentic Execution](../implementation/AGENTIC_EXECUTION.md)** - Deep dive into SQL generation
3. **[Adding Databases](./ADDING_DATABASES.md)** - Connect real databases

### Customize

1. **Prompts** - Edit `backend/knowledge/prompts/*.yaml`
2. **Schemas** - Update `backend/knowledge/data_schemas/*.yaml`
3. **Models** - Change model versions in `.env`

### Extend

1. Add new LLM stages
2. Implement persistent storage
3. Add visualization features
4. Create custom datasources

---

## Production Deployment

### Checklist

- [ ] Remove or secure debug mode (`LLM_DEBUG=false`)
- [ ] Set up persistent storage (PostgreSQL for threads/messages)
- [ ] Configure CORS properly
- [ ] Add authentication/authorization
- [ ] Set up rate limiting
- [ ] Configure proper logging
- [ ] Use environment-specific configs
- [ ] Set up monitoring/alerting
- [ ] Implement backup strategy
- [ ] Configure SSL/TLS

### Environment Variables

Production `.env` should have:
```bash
ANTHROPIC_API_KEY=<production-key>
LLM_DEBUG=false
POSTGRES_HOST=<production-host>
# ... other production settings
```

---

## Getting Help

### Resources

1. **Documentation** - `/docs` directory
2. **Project Context** - `CLAUDE.md` in root
3. **Code Comments** - Inline documentation
4. **Debug Logs** - Enable `LLM_DEBUG=true`

### Common Questions

**Q: Do I need real PostgreSQL databases?**
A: No, system works with schema files only for testing.

**Q: How much do LLM calls cost?**
A: Depends on usage. Simple queries: ~$0.01-0.02, Complex: ~$0.05-0.10

**Q: Can I use other LLM providers?**
A: Currently Anthropic only, but `client.py` can be extended.

**Q: Is data persistent?**
A: No, in-memory storage (data lost on restart). Can be extended.

**Q: Can I add more databases?**
A: Yes! See [Adding Databases](./ADDING_DATABASES.md)

---

## Quick Reference

### Start Backend
```bash
cd backend
uv run uvicorn main:app --host 0.0.0.0 --port 5001 --reload
```

### Start Frontend
```bash
cd frontend
npm run dev
```

### Check Logs
```bash
# Backend logs in terminal where uvicorn is running
# Frontend logs in browser console (F12)
```

### Test API
```bash
# Check health
curl http://localhost:5001/api/data-sources

# List threads
curl http://localhost:5001/api/threads
```

---

**Need more help?** Check the [Troubleshooting Guide](./TROUBLESHOOTING.md)

**Ready to dive deeper?** See [System Architecture](../architecture/SYSTEM_ARCHITECTURE.md)
