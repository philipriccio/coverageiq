# CoverageIQ - Project Status
**Last Updated:** 2026-03-18

## Current Status
Upgrade sprint completed locally and pushed-ready.

### Major Changes
- Primary LLM switched from Moonshot/Kimi to **OpenAI GPT-4.1**
- **Claude Sonnet 4.5** remains fallback if OpenAI fails
- PostgreSQL support confirmed and completed for async runtime + Alembic migration flow
- Added **report history** API + frontend tab
- Added **shot library** (`coverage_examples`) for starred example reports
- Added **domain knowledge store** (`domain_knowledge`) with `/admin` UI

## Required Environment Variables
### Render backend
- `OPENAI_API_KEY=...`
- `ANTHROPIC_API_KEY=...`
- `DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DBNAME`
  - Render may also provide `postgres://...`; app runtime normalizes it automatically
- `CORS_ORIGINS=https://coverageiq-frontend.pages.dev,http://localhost:5173,...`
- `PYTHON_VERSION=3.11.9`

### Local development
- `DATABASE_URL=sqlite+aiosqlite:///./coverageiq.db`
- `OPENAI_API_KEY=...`
- `ANTHROPIC_API_KEY=...`

## PostgreSQL Status
The app runtime already had partial PostgreSQL URL normalization in `backend/app/database.py`.
This sprint completed the missing deployment path by:
- keeping async runtime on `postgresql+asyncpg://`
- updating Alembic to normalize env/database URLs for migrations
- adding `psycopg2-binary` so Alembic can run sync migrations against PostgreSQL
- preserving SQLite local support

## New Database Tables
- `coverage_examples`
- `domain_knowledge`

## Production Migration Steps
1. Provision a Render PostgreSQL database.
2. Set backend `DATABASE_URL` to the Render connection string.
3. Add `OPENAI_API_KEY` in Render.
4. Run Alembic migrations in the backend environment.
5. Redeploy backend.

## Frontend Additions
- New **History** tab in main app
- Click any past report to reopen full coverage view
- Recommendation color badges: Pass red, Consider yellow, Recommend green
- `★ Flag as example` button on completed reports
- `/admin` page for managing domain knowledge entries

## Validation
- Python backend modules compile successfully
- `frontend/npm run build` passes
