# CoverageIQ Coolify Migration Report

## Summary
CoverageIQ already had existing Coolify resources, so I updated those instead of creating duplicates:
- Backend app: `vso00koos400w88kskwgko04`
- Frontend app: `jg0sowwscgsgswok84s44040`
- PostgreSQL DB: `f0ok0s4o4gwgcs8g0gcw0w04`

I also updated the repo with Docker-based deployment config:
- `backend/Dockerfile`
- `frontend/Dockerfile`
- `frontend/nginx.conf`

## Coolify Resources
### Backend
- **App UUID:** `vso00koos400w88kskwgko04`
- **Name:** `coverageiq-backend`
- **Base directory:** `/backend`
- **Build pack:** `dockerfile`
- **Dockerfile location:** `/backend/Dockerfile`
- **Domain:** `https://api.coverageiq.companytheatre.ca`

### Frontend
- **App UUID:** `jg0sowwscgsgswok84s44040`
- **Name:** `coverageiq-frontend`
- **Base directory:** `/frontend`
- **Build pack:** `dockerfile`
- **Dockerfile location:** `/frontend/Dockerfile`
- **Domain:** `https://coverageiq.companytheatre.ca`

### PostgreSQL
- **DB UUID:** `f0ok0s4o4gwgcs8g0gcw0w04`
- **Name:** `coverageiq-db`
- **Internal URL:** `postgres://coverageiq:***@f0ok0s4o4gwgcs8g0gcw0w04:5432/coverageiq`
- **App runtime URL used:** `postgresql+asyncpg://coverageiq:***@f0ok0s4o4gwgcs8g0gcw0w04:5432/coverageiq`

## Environment Variables Set
### Backend
- `DATABASE_URL=postgresql+asyncpg://coverageiq:***@f0ok0s4o4gwgcs8g0gcw0w04:5432/coverageiq`
- `CORS_ORIGINS=https://coverageiq.companytheatre.ca,http://localhost:5173`
- `OPENAI_API_KEY=sk-proj-***`
- `ANTHROPIC_API_KEY=sk-ant-api03-***`
- `PYTHON_VERSION=3.11.9`

### Frontend
- `VITE_API_URL=https://api.coverageiq.companytheatre.ca`

## Notes
- I used **two hostnames** because frontend and backend are separate Coolify apps:
  - Frontend: `coverageiq.companytheatre.ca`
  - Backend API: `api.coverageiq.companytheatre.ca`
- This is slightly different from the original brief line that said `VITE_API_URL=https://coverageiq.companytheatre.ca`; that single hostname would conflict with the frontend app.
- The old backend Coolify env still contains `MOONSHOT_API_KEY`. It is now stale and can be removed later.

## Deploy Trigger
Both apps had deploys triggered via API.
Latest queued deployments:
- Backend: `vw804owks8s4gssoocksws0k`
- Frontend: `ec8400co44okgg4gc00ows48`

## DNS Records Philip Needs to Add
Create **A records** pointing to `159.89.120.69`:
- `coverageiq.companytheatre.ca` → `159.89.120.69`
- `api.coverageiq.companytheatre.ca` → `159.89.120.69`

## Verification Steps
1. Wait for DNS to propagate.
2. In Coolify, confirm both deployments complete successfully.
3. Visit `https://coverageiq.companytheatre.ca` and confirm the frontend loads.
4. Visit `https://api.coverageiq.companytheatre.ca/health` and confirm the backend returns healthy JSON.
5. Generate a test coverage report from the frontend.
6. Confirm the backend connects to PostgreSQL and reports persist.
7. Confirm browser requests succeed with no CORS errors.

## Pending / Blockers
1. **Git push failed.**
   - Local commit created successfully: `61ac260 chore: add Coolify deployment config (Dockerfiles, nginx)`
   - `git push origin main` failed because the configured GitHub credential/token is not usable in this non-interactive session.
   - Until that commit is pushed, Coolify will still deploy from the old remote `main` branch contents.
2. **Deploy success is not yet verified end-to-end.**
   - Deploys were queued, but with the push blocked, successful Dockerfile-based deployment still depends on getting commit `61ac260` onto GitHub.

## Recommendation on Render / Cloudflare Cleanup
**Do not delete Render or Cloudflare Pages yet.**
Only remove them after:
- the Dockerfile changes are pushed,
- both Coolify deploys succeed,
- DNS is live,
- frontend + backend smoke tests pass,
- and Philip confirms the migrated app is working.
