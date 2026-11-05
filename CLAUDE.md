# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Factory Inventory Management System Demo with GitHub integration - Full-stack application with Vue 3 frontend, Python FastAPI backend, and in-memory mock data (no database).

> ⚠️ **This repository and any fork you create are PUBLIC.** Do not commit credentials, internal hostnames, or private registry URLs. `client/.npmrc` pins the public npm registry and `client/package-lock.json` is gitignored to prevent locally-configured registries from leaking into commits — leave both in place.

## Critical Tool Usage Rules

### Subagents
Use the Task tool with these specialized subagents for appropriate tasks:

- **vue-expert**: Use for Vue 3 frontend features, UI components, styling, and client-side functionality
  - Examples: Creating components, fixing reactivity issues, performance optimization, complex state management
  - **MANDATORY RULE: ANY time you need to create or significantly modify a .vue file, you MUST delegate to vue-expert**
- **code-reviewer**: Use after writing significant code to review quality and best practices
- **Explore**: Use for understanding codebase structure, searching for patterns, or answering questions about how components work
- **general-purpose**: Use for complex multi-step tasks or when other agents don't fit

### Skills
- **backend-api-test** skill: Use when writing or modifying tests in `tests/backend` directory with pytest and FastAPI TestClient

### MCP Tools
- **ALWAYS use GitHub MCP tools** (`mcp__github__*`) for ALL GitHub operations
  - Exception: Local branches only - use `git checkout -b` instead of `mcp__github__create_branch`
- **ALWAYS use Playwright MCP tools** (`mcp__playwright__*`) for browser testing
  - Test against: `http://localhost:3000` (frontend), `http://localhost:8001` (API)

## Stack
- **Frontend**: Vue 3 + Composition API + Vite (port 3000)
- **Backend**: Python FastAPI (port 8001)
- **Data**: JSON files in `server/data/` loaded via `server/mock_data.py`

## Quick Start

```bash
# Backend
cd server
uv run python main.py

# Frontend
cd client
npm install && npm run dev
```

## Commands

```bash
./scripts/start.sh / ./scripts/stop.sh      # Install missing deps and run/stop both servers (same as /start, /stop)
cd client && npm run build                  # Production build (no client lint or test setup exists)
cd tests && uv run pytest -v                # All backend tests
cd tests && uv run pytest backend/test_inventory.py::TestInventoryEndpoints::<test_name> -v   # Single test
cd server && uv run python generate_data.py # Regenerate sample data (check it writes where you expect before committing)
```

Backend deps (`fastapi`, `pytest`, `httpx`, ...) are declared only in `server/pyproject.toml`; there is no `pyproject.toml` in `tests/` or the repo root. If `uv run pytest` in `tests/` cannot import them, run it from `server/` with `../tests/backend` as the path. `tests/README.md` lists a `test_orders.py` that does not exist; the real files are `test_dashboard.py`, `test_inventory.py`, `test_misc_endpoints.py`.

## Architecture

- **Backend** (`server/main.py`): single file holding Pydantic models, shared `apply_filters` / `filter_by_month` helpers, and all routes. `server/mock_data.py` loads every JSON file in `server/data/` once at import, so data edits need a server restart. Quarter filters (`Q1-2025`...) are expanded by `QUARTER_MAP` and matched by substring against `order_date`.
- **Frontend** (`client/src`): routes are declared in `main.js` (Dashboard, Inventory, Orders, Demand, Spending, Reports). `api.js` is the only HTTP layer and hardcodes `http://localhost:8001/api`. It omits any filter whose value is `'all'`.
- **Filter state**: `composables/useFilters.js` holds module-level refs (a shared singleton across all views) and maps the Time Period selection to the `month` query param via `getCurrentFilters()`. New filters must be added there, in `api.js`, and in the backend endpoint.
- **i18n and auth**: `composables/useI18n.js` with `locales/en.js` and `ja.js`. Add new UI strings to both. `useAuth.js` is client-side only.
- **Dev tooling**: `.claude/agents`, `.claude/commands` and `.claude/hooks` define the subagents, slash commands and tool-usage logger referenced above.

## Key Patterns

**Filter System**: 4 filters (Time Period, Warehouse, Category, Order Status) apply to all data via query params
**Data Flow**: Vue filters → `client/src/api.js` → FastAPI → In-memory filtering → Pydantic validation → Computed properties
**Reactivity**: Raw data in refs (`allOrders`, `inventoryItems`), derived data in computed properties

## API Endpoints
- `GET /api/inventory` - Filters: warehouse, category
- `GET /api/orders` - Filters: warehouse, category, status, month
- `GET /api/dashboard/summary` - All filters
- `GET /api/demand`, `/api/backlog` - No filters
- `GET /api/spending/*` - Summary, monthly, categories, transactions

## Common Issues
1. Use unique keys in v-for (not `index`) - use `sku`, `month`, etc.
2. Validate dates before `.getMonth()` calls
3. Update Pydantic models when changing JSON data structure
4. Inventory filters don't support month (no time dimension)
5. Revenue goals: $800K/month single, $9.6M YTD all months

## File Locations
- Views: `client/src/views/*.vue`
- API Client: `client/src/api.js`
- Backend: `server/main.py`, `server/mock_data.py`
- Data: `server/data/*.json`
- Styles: `client/src/App.vue`

## Design System
- Colors: Slate/gray (#0f172a, #64748b, #e2e8f0)
- Status: green/blue/yellow/red
- Charts: Custom SVG, CSS Grid for layouts
- No emojis in UI
