# Documentation Index

Complete guide to AI Data Agent documentation.

---

## 📖 Start Here

**New to the project?**
1. [Main README](./README.md) - Overview and current state
2. [Getting Started Guide](./guides/GETTING_STARTED.md) - Setup and first steps
3. [System Architecture](./architecture/SYSTEM_ARCHITECTURE.md) - How it works

---

## 📂 Documentation Structure

```
docs/
├── README.md                      # Main overview (START HERE)
├── INDEX.md                       # This file
├── architecture/                  # System design documents
│   ├── SYSTEM_ARCHITECTURE.md     # Complete architecture overview
│   └── DATASOURCE_ARCHITECTURE.md # Database connection model
├── implementation/                # Implementation details
│   ├── AGENTIC_EXECUTION.md       # SQL generation and retry logic
│   ├── DATABASE_TRACKING.md       # Usage tracking implementation
│   ├── DATABASE_NAMING_FIX.md     # Validation improvements
│   ├── FRONTEND_DATABASE_HIGHLIGHTING.md  # UI implementation
│   ├── SCHEMA_AND_OPTIMIZATION.md # Schema usage and optimization
│   └── VALIDATION_AND_DEBUG_FIX.md # Debug logging enhancement
└── guides/                        # How-to guides
    └── GETTING_STARTED.md         # Complete setup guide
```

---

## 🏗️ Architecture Documentation

### [System Architecture](./architecture/SYSTEM_ARCHITECTURE.md)
**Complete system overview**

Topics covered:
- Architecture diagram
- All components (Frontend, API, Orchestrator, Executor, Storage, Datasources)
- Data flow through the system
- Technology choices and rationale
- Performance metrics
- Extension points

**Read this to understand:** How the entire system fits together

---

### [Datasource Architecture](./architecture/DATASOURCE_ARCHITECTURE.md)
**Database connection model**

Topics covered:
- One datasource per database pattern
- PostgreSQL configuration
- Environment variables
- Connection pooling
- Cross-database query handling

**Read this to understand:** How databases are connected and managed

---

## 🛠️ Implementation Documentation

### [Agentic Execution](./implementation/AGENTIC_EXECUTION.md)
**SQL generation with automatic retry**

Topics covered:
- 5-stage LLM pipeline
- Agentic SQL generation loop
- Error recovery strategies
- Retry logic (up to 5 attempts)
- Step-by-step execution
- Summary generation

**Read this to understand:** How SQL is generated and executed

---

### [Database Usage Tracking](./implementation/DATABASE_TRACKING.md)
**Backend tracking implementation**

Topics covered:
- Storage layer additions
- Thread-level database tracking
- Orchestrator integration
- API endpoint for used databases
- Data flow

**Read this to understand:** How database usage is tracked

---

### [Frontend Database Highlighting](./implementation/FRONTEND_DATABASE_HIGHLIGHTING.md)
**UI implementation for database badges**

Topics covered:
- API client additions
- DataSourceBadges component
- Conditional styling (dimmed vs highlighted)
- Auto-refresh mechanism
- Visual states

**Read this to understand:** How UI shows which databases are used

---

### [Schema Usage and Optimization](./implementation/SCHEMA_AND_OPTIMIZATION.md)
**Schema files and token optimization**

Topics covered:
- Confirmation that schema YAMLs are fully used
- Where schemas are loaded
- Error loop optimization (only last attempt sent)
- Token savings (~37% reduction)

**Read this to understand:** How schemas are used and optimized

---

### [Validation and Debug Fix](./implementation/VALIDATION_AND_DEBUG_FIX.md)
**Database ID validation and logging**

Topics covered:
- Fixed validation to return correct database IDs
- Summary.yaml usage confirmed
- Full prompt/response logging added
- Enhanced debug output

**Read this to understand:** How validation works and debug logging

---

### [Database Naming Fix](./implementation/DATABASE_NAMING_FIX.md)
**Fixed database vs table name confusion**

Topics covered:
- Problem with "customers" vs "customer_db"
- Prompt enhancements for clarity
- Schema loading improvements
- Validation fixes

**Read this to understand:** Historical issue that was fixed

---

## 📚 Guides

### [Getting Started](./guides/GETTING_STARTED.md)
**Complete setup and usage guide**

Sections:
- Prerequisites
- Quick start (5 minutes)
- Environment configuration
- First steps
- UI overview
- Testing the system
- Debugging
- Common issues
- Next steps

**Read this to:** Get up and running quickly

---

## 🔍 Quick Reference

### By Topic

**Want to understand the architecture?**
→ [System Architecture](./architecture/SYSTEM_ARCHITECTURE.md)

**Want to set up the project?**
→ [Getting Started Guide](./guides/GETTING_STARTED.md)

**Want to understand SQL execution?**
→ [Agentic Execution](./implementation/AGENTIC_EXECUTION.md)

**Want to add a database?**
→ [Datasource Architecture](./architecture/DATASOURCE_ARCHITECTURE.md)

**Want to customize prompts?**
→ See `backend/knowledge/prompts/` and [System Architecture](./architecture/SYSTEM_ARCHITECTURE.md#9-prompt-management)

**Want to debug issues?**
→ [Getting Started - Debugging](./guides/GETTING_STARTED.md#debugging)

---

## 📊 By Role

### For Developers

**Getting started:**
1. [Getting Started Guide](./guides/GETTING_STARTED.md)
2. [System Architecture](./architecture/SYSTEM_ARCHITECTURE.md)
3. [Agentic Execution](./implementation/AGENTIC_EXECUTION.md)

**Extending the system:**
- Adding features: [System Architecture - Extension Points](./architecture/SYSTEM_ARCHITECTURE.md#extension-points)
- Adding databases: [Datasource Architecture](./architecture/DATASOURCE_ARCHITECTURE.md)

### For Data Engineers

**Understanding data flow:**
1. [Datasource Architecture](./architecture/DATASOURCE_ARCHITECTURE.md)
2. [System Architecture - Data Flow](./architecture/SYSTEM_ARCHITECTURE.md#data-flow)
3. Schema files in `backend/knowledge/data_schemas/`

### For DevOps

**Deployment:**
1. [Getting Started - Production Deployment](./guides/GETTING_STARTED.md#production-deployment)
2. [System Architecture - Scalability](./architecture/SYSTEM_ARCHITECTURE.md#scalability-considerations)
3. Environment configuration

### For Product Managers

**Current capabilities:**
1. [Main README](./README.md) - Feature overview
2. [Getting Started - Testing](./guides/GETTING_STARTED.md#testing-the-system)
3. [System Architecture - Performance](./architecture/SYSTEM_ARCHITECTURE.md#performance-metrics)

---

## 📝 Related Files

### In Root Directory

- **`CLAUDE.md`** - Project context for Claude (keep updated)
- **`README.md`** - Main project readme
- **`.env.example`** - Environment template

### In Backend

- **`backend/README.md`** - Backend-specific readme
- **`backend/knowledge/`** - Configuration files
  - `data_schemas/` - Database schemas (YAML)
  - `prompts/` - LLM prompts (YAML)
  - `docs/` - Additional documentation
  - `datasources.yaml` - Datasource configuration

---

## 🔄 Keeping Documentation Updated

### When to Update

**System Architecture:**
- Adding new components
- Changing data flow
- Technology stack changes

**Implementation Docs:**
- New features added
- Bug fixes that change behavior
- Optimization changes

**Getting Started:**
- Setup process changes
- New environment variables
- Configuration changes

**CLAUDE.md (Important!):**
- Any project structure changes
- New features or capabilities
- Architecture updates

### How to Update

1. Edit relevant markdown file
2. Update "Last Updated" date
3. Update version if needed
4. Cross-reference related docs
5. Commit with clear message

---

## 🆘 Getting Help

### First Steps

1. Check [Getting Started](./guides/GETTING_STARTED.md#common-issues)
2. Enable debug mode (`LLM_DEBUG=true`)
3. Review relevant implementation doc

### Still Stuck?

1. Check `CLAUDE.md` for project context
2. Review debug logs
3. Check code comments
4. Review related docs

---

## 📈 Documentation Versions

**v1.0** (2025-10-27)
- Initial comprehensive documentation
- System architecture documented
- All implementation details covered
- Getting started guide created
- Index organized

**Changes from previous:**
- Consolidated scattered MD files
- Organized into clear structure
- Added comprehensive main README
- Created cross-references
- Added quick reference sections

---

**Last Updated:** 2025-10-27
**Documentation Version:** 1.0
