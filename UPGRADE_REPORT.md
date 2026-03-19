# CoverageIQ Upgrade Report

## What changed and where

### 1) GPT-4.1 primary + Claude fallback
- `backend/app/services/llm_client.py`
  - Replaced Moonshot client with `OpenAIClient`
  - Primary model: `gpt-4.1`
  - Claude fallback remains `claude-sonnet-4-5`
- `backend/app/services/analysis.py`
  - Analysis pipeline now calls OpenAI first and falls back to Claude on failure
- `backend/main.py`
  - `/api/models` now advertises GPT-4.1 as default
- `backend/requirements.txt`
  - Added `openai>=1.0.0`
  - Removed Moonshot dependency
- `.env.example`, `STATUS.md`
  - Added `OPENAI_API_KEY`

### 2) PostgreSQL migration path
- `backend/app/database.py`
  - Existing async runtime PostgreSQL normalization was already partly present and remains valid
- `backend/alembic/env.py`
  - Completed Alembic URL normalization for SQLite and PostgreSQL
  - Converts async URLs to sync-compatible ones for migrations
- `backend/requirements.txt`
  - Added `psycopg2-binary` for Alembic sync migrations
  - `asyncpg` remains for runtime DB access

### 3) Report history
- `backend/app/routers/coverage.py`
  - Added `GET /api/coverage/history`
- `frontend/src/App.tsx`
  - Added History tab
  - Added clickable history cards that reopen full report view
- `frontend/src/App.css`
  - Added history UI styling

### 4) Shot library + domain knowledge base
- `backend/app/models.py`
  - Added `coverage_examples`
  - Added `domain_knowledge`
- `backend/alembic/versions/b6f6b7d9f2a1_add_examples_knowledge_and_openai_defaults.py`
  - Migration for new tables
- `backend/app/routers/coverage.py`
  - Added report flagging endpoint
  - Added admin knowledge CRUD endpoints
- `backend/app/services/prompts.py`
  - Added prompt injection builder for domain expertise + example coverage
- `backend/app/services/analysis.py`
  - Injects up to 2 featured examples matching genre
  - Injects relevant domain knowledge entries (`genre` + `general`)
- `frontend/src/App.tsx`
  - Added `★ Flag as example`
  - Added `/admin` page UI

## Env vars Philip needs to add to Render

### Required
- `OPENAI_API_KEY=...`
- `ANTHROPIC_API_KEY=...`
- `DATABASE_URL=...`
  - Preferred runtime format: `postgresql+asyncpg://...`
  - If Render gives `postgres://...`, the app normalizes it at runtime
- `CORS_ORIGINS=...`
- `PYTHON_VERSION=3.11.9`

## Manual steps needed post-deploy
1. Create/provision Render PostgreSQL database.
2. Update backend `DATABASE_URL` in Render.
3. Add `OPENAI_API_KEY` in Render.
4. Run Alembic migrations in backend environment.
5. Redeploy backend.
6. Visit `/admin` and seed a few `general` or genre-specific knowledge entries.
7. Generate a report and star at least one strong result to start the shot library.

## Issues encountered and resolutions
- **PostgreSQL support was only partially done**
  - Runtime async URL handling existed, but Alembic migration handling was incomplete.
  - Fixed by normalizing env URLs for sync Alembic execution and adding `psycopg2-binary`.
- **Frontend build initially failed because TypeScript binary was not installed locally**
  - Resolved with `npm install`, then `npm run build` passed.

## What to test first
1. Generate a new report with GPT-4.1 and confirm `model_used` shows `gpt-4.1`.
2. Open the History tab and verify the report appears.
3. Click the history item and confirm the full report reloads.
4. Star the report and confirm button state changes.
5. Add a domain knowledge entry at `/admin`.
6. Generate another report in same genre and confirm prompt injection behavior via backend logs / quality shift.
7. Run migration against PostgreSQL and verify reports persist across deploys.

## Validation completed
- Python compile check passed for backend modules.
- `npm run build` passed in `frontend/`.
