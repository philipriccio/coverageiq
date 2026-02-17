# CoverageIQ - Handoff Document for Mildred

**Prepared for:** Mildred (working on Philip's Mac mini)  
**Prepared by:** Janet (OpenClaw AI Assistant)  
**Date:** February 17, 2026  
**Project:** CoverageIQ - AI-Powered Script Coverage Tool  

---

## 📋 Table of Contents

1. [Project Overview](#1-project-overview)
2. [Current Status](#2-current-status)
3. [Tech Stack & Architecture](#3-tech-stack--architecture)
4. [File Structure](#4-file-structure)
5. [Environment Setup](#5-environment-setup)
6. [API Keys & Credentials](#6-api-keys--credentials)
7. [Database Schema](#7-database-schema)
8. [What Works vs What's Pending](#8-what-works-vs-whats-pending)
9. [Known Issues & Solutions](#9-known-issues--solutions)
10. [Deployment Notes](#10-deployment-notes)
11. [Development History](#11-development-history)
12. [Next Steps / Roadmap](#12-next-steps--roadmap)
13. [Important Context](#13-important-context)

---

## 1. Project Overview

CoverageIQ is an AI-powered script coverage platform built for Hawco Productions (Philip Riccio). It analyzes TV pilot scripts and generates professional-grade coverage reports traditionally done by human readers.

### Key Features
- **Script Upload**: PDF and Final Draft (.fdx) support
- **AI Analysis**: Three analysis depths (Quick/Standard/Deep)
- **Coverage Reports**: Logline, synopsis, character notes, structure analysis, market positioning
- **Scoring**: 5 subscores × /10 = /50 total, mapped to Pass/Consider/Recommend
- **Export**: Google Docs (primary) and PDF (secondary)
- **Privacy-First**: Scripts processed in memory only, never stored

### Target Users
- **Phase 1 (Current)**: Philip at Hawco Productions - single user, internal tool
- **Phase 2 (Future)**: Screenwriters, producers, script consultants (commercialization)

---

## 2. Current Status

### 🎯 Production Status: LIVE ✅

| Component | URL | Status |
|-----------|-----|--------|
| Frontend | https://02c4e396.coverageiq-frontend.pages.dev | ✅ Live |
| Backend API | https://coverageiq-backend.onrender.com | ✅ Live |
| API Docs | https://coverageiq-backend.onrender.com/docs | ✅ Live |

### GitHub Repository
- **URL**: https://github.com/philipriccio/coverageiq
- **Local Path**: `/data/.openclaw/workspace/coverageiq/`

### Cost Structure
- **Quick/Standard/Deep (clean)**: ~$0.04 per script (Moonshot AI)
- **Deep (mature content)**: ~$0.24 per script (Moonshot fails + Claude fallback)
- **Infrastructure**: $0/month (Render free tier + Cloudflare Pages)

---

## 3. Tech Stack & Architecture

### Backend
| Component | Technology | Version |
|-----------|------------|---------|
| Framework | FastAPI | 0.115.0 |
| Server | Uvicorn | 0.32.0 |
| Database | SQLite + aiosqlite | Async |
| ORM | SQLAlchemy | 2.0.36 |
| Migrations | Alembic | 1.18.4 |
| LLM Primary | Moonshot AI (Kimi K2.5) | moonshot-v1-128k |
| LLM Fallback | Anthropic (Claude) | claude-3-5-sonnet |
| PDF Parsing | pdfplumber | 0.11.9 |
| FDX Parsing | lxml | 6.0.2 |
| PDF Export | ReportLab | 4.2.5 |
| Google Docs | google-api-python-client | 2.154.0 |

### Frontend
| Component | Technology |
|-----------|------------|
| Framework | React 18 |
| Language | TypeScript |
| Build Tool | Vite |
| Styling | CSS (custom) |
| HTTP Client | Axios |

### Architecture Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT                               │
│              (React + TypeScript + Vite)                    │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTPS
┌───────────────────────▼─────────────────────────────────────┐
│                        API SERVER                           │
│              (FastAPI + Uvicorn + SQLite)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Script Upload│  │ PDF/FDX     │  │ Async Analysis      │  │
│  │ Handler     │  │ Extractor   │  │ Queue (Background)  │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│           │               │                    │             │
│           ▼               ▼                    ▼             │
│  ┌─────────────────────────────────────────────────────┐     │
│  │              LLM Analysis (Kimi/Claude)             │     │
│  └─────────────────────────────────────────────────────┘     │
│                          │                                   │
│           ┌──────────────┼──────────────┐                   │
│           ▼              ▼              ▼                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   SQLite    │  │ Google Docs │  │    PDF      │          │
│  │  Database   │  │   Export    │  │   Export    │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. File Structure

```
/data/.openclaw/workspace/coverageiq/
├── backend/                          # FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── database.py               # SQLAlchemy + aiosqlite config
│   │   ├── models.py                 # Database models (3 tables)
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── scripts.py            # Upload endpoints
│   │   │   └── coverage.py           # Analysis & export endpoints
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── extractor.py          # PDF/FDX text extraction
│   │       ├── llm_client.py         # Moonshot + Claude clients
│   │       ├── prompts.py            # TV pilot coverage prompts
│   │       ├── analysis.py           # Analysis pipeline
│   │       ├── job_manager.py        # Async job queue
│   │       ├── google_docs_export.py # Google Docs API
│   │       └── pdf_export.py         # PDF generation
│   ├── alembic/                      # Database migrations
│   │   ├── env.py
│   │   └── versions/
│   │       ├── eb58b88f066e_initial_migration.py
│   │       └── 8562ca56853a_add_analysisjob_table_for_async_queue.py
│   ├── venv/                         # Python virtual environment
│   ├── main.py                       # FastAPI entry point
│   ├── requirements.txt              # Python dependencies
│   └── coverageiq.db                 # SQLite database (local only)
│
├── frontend/                         # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── ProgressBar.tsx       # Progress bar component
│   │   │   └── ProgressBar.css
│   │   ├── App.tsx                   # Main application
│   │   ├── App.css                   # Styling
│   │   ├── main.tsx                  # Entry point
│   │   └── index.css
│   ├── dist/                         # Build output
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── PLAN.md                           # Original 7-day build plan
├── README.md                         # Basic project info
├── STATUS.md                         # Current project status
├── DAY2_REPORT.md                    # Day 2 completion report
├── DAY3_REPORT.md                    # Day 3 completion report
├── DAY4_REPORT.md                    # Day 4 completion report
├── HANDOFF_TO_MILDRED.md             # This file
│
└── dev-session-feb14.jsonl           # Development session transcripts
└── dev-session-feb15.jsonl
└── dev-session-feb16.jsonl
```

---

## 5. Environment Setup

### Prerequisites
- Python 3.11+ (Python 3.14 has compatibility issues, use 3.11)
- Node.js 18+
- Git

### Backend Setup

```bash
# Navigate to backend directory
cd /data/.openclaw/workspace/coverageiq/backend

# Create virtual environment (Python 3.11 required)
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (see next section)
export MOONSHOT_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export DATABASE_URL="sqlite+aiosqlite:///./coverageiq.db"

# Initialize database (auto-created on first run)
# Database tables are created automatically via lifespan event

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd /data/.openclaw/workspace/coverageiq/frontend

# Install dependencies
npm install

# Create .env file for API URL
echo "VITE_API_URL=http://localhost:8000" > .env

# Run development server
npm run dev

# Access at http://localhost:5173
```

### Production Build (Frontend)

```bash
cd /data/.openclaw/workspace/coverageiq/frontend
npm run build
# Output goes to dist/ directory
```

---

## 6. API Keys & Credentials

### Required API Keys

| Service | Key Name | Purpose | Source |
|---------|----------|---------|--------|
| Moonshot AI | `MOONSHOT_API_KEY` | Primary LLM for analysis | https://platform.moonshot.cn |
| Anthropic | `ANTHROPIC_API_KEY` | Fallback for mature content | https://console.anthropic.com |
| Google Cloud | `google-drive-credentials.json` | Google Docs export | Google Cloud Console |

### Environment Variables (Render.com)

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-api03-...
MOONSHOT_API_KEY=sk-RABtdhqQ5B5...
DATABASE_URL=sqlite+aiosqlite:///./coverageiq.db
PYTHON_VERSION=3.11.9

# CORS - comma-separated list of allowed frontend URLs
CORS_ORIGINS=https://02c4e396.coverageiq-frontend.pages.dev,http://localhost:5173
```

### Local Development .env (Backend)

Create `/data/.openclaw/workspace/coverageiq/backend/.env`:

```bash
MOONSHOT_API_KEY=sk-your-moonshot-key
ANTHROPIC_API_KEY=sk-your-anthropic-key
DATABASE_URL=sqlite+aiosqlite:///./coverageiq.db
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Google Docs OAuth Setup

For Google Docs export to work locally:

```bash
cd /data/.openclaw/workspace/coverageiq/backend
python setup_google_auth.py
# Follow browser prompts to authorize
# Creates .google-token.json file
```

**Note**: The `google-drive-credentials.json` file is already in the backend directory and configured for the Hawco Productions Google account.

---

## 7. Database Schema

### Three Main Tables

#### 1. `script_metadata` - Script Metadata Only
```sql
-- NO script content stored here - only metadata
id: VARCHAR(36) PRIMARY KEY
user_id: VARCHAR(36) INDEX
filename_hash: VARCHAR(64)  -- SHA256 of filename
file_hash: VARCHAR(64) INDEX  -- SHA256 of content (duplicate detection)
format: ENUM('pdf', 'fdx')
title: VARCHAR(500)
author: VARCHAR(500)
page_count: INTEGER
created_at: DATETIME
```

#### 2. `coverage_reports` - Generated Coverage
```sql
id: VARCHAR(36) PRIMARY KEY
script_id: VARCHAR(36) FK → script_metadata

-- Configuration
genre: VARCHAR(100)
comps: JSON  -- Array of comparable series
analysis_depth: VARCHAR(20)  -- 'quick', 'standard', 'deep'
status: ENUM('processing', 'completed', 'failed')

-- Scores (5 categories × /10 = /50 total)
subscores: JSON  -- {"concept": 8, "structure": 7, ...}
total_score: INTEGER  -- /50
recommendation: ENUM('Pass', 'Consider', 'Recommend')
  -- Pass: 0-24, Consider: 25-37, Recommend: 38-50

-- Report Content
logline: TEXT
synopsis: TEXT
overall_comments: TEXT
strengths: JSON  -- Array of strings
weaknesses: JSON  -- Array of strings
character_notes: TEXT
structure_analysis: TEXT
market_positioning: TEXT
evidence_quotes: JSON  -- [{"quote": "...", "page": 12, "context": "..."}]

-- Metadata
model_used: VARCHAR(50)  -- 'kimi-k2.5' or 'claude-3-5-sonnet'
created_at: DATETIME
completed_at: DATETIME
expires_at: DATETIME  -- 90 days from creation (data retention)
```

#### 3. `analysis_jobs` - Async Job Queue
```sql
id: VARCHAR(36) PRIMARY KEY
script_id: VARCHAR(36) FK
report_id: VARCHAR(36) FK → coverage_reports

status: ENUM('queued', 'processing', 'completed', 'failed')
progress: INTEGER  -- 0-100 percentage
error_message: TEXT

-- Stored for retry capability
genre: VARCHAR(100)
comps: JSON
analysis_depth: VARCHAR(20)
script_text_hash: VARCHAR(64)  -- For verification, NOT the text

-- Timestamps
created_at: DATETIME
updated_at: DATETIME
completed_at: DATETIME
```

### Data Retention Policy

| Data Type | Retention | Storage |
|-----------|-----------|---------|
| Script source files | ZERO | Never written to disk |
| Extracted text | ZERO | Parsed and discarded immediately |
| Raw LLM responses | ZERO | Discarded after parsing |
| Report metadata | 90 days | SQLite database |
| Coverage reports | 90 days | SQLite database |
| Audit/error logs | 7-30 days | No script content in logs |

---

## 8. What Works vs What's Pending

### ✅ What's Working (Production Ready)

#### Core Features
- [x] PDF script upload and text extraction
- [x] Final Draft (.fdx) file support
- [x] Text paste input for scripts
- [x] Three analysis depths: Quick, Standard, Deep
- [x] TV pilot-focused coverage with Series Engine analysis
- [x] Async job queue with progress tracking
- [x] Progress bar UI during analysis
- [x] 5 subscores (/10 each) = /50 total
- [x] Pass/Consider/Recommend mapping
- [x] Evidence quotes with page references
- [x] Google Docs export (primary output)
- [x] PDF export with color-coded styling
- [x] Privacy-compliant (zero script retention)

#### Infrastructure
- [x] Auto-deploy webhook (GitHub → Render)
- [x] CORS configured for production URLs
- [x] SQLite database with async support
- [x] Job status polling API
- [x] Error handling and logging
- [x] Claude fallback for mature content
- [x] English-only output enforcement

### 🚧 What's Pending / Known Limitations

#### High Priority (Recommended Next)
- [ ] **PostgreSQL Migration**: SQLite resets on Render deploy (reports lost)
- [ ] **Report History Page**: List past analyses in frontend
- [ ] **Drag-and-Drop Upload**: Better UX than file picker
- [ ] **Real Progress Tracking**: Currently simulated (0→25→50→75→100%)

#### Medium Priority
- [ ] **User Authentication**: Multi-user support (if commercializing)
- [ ] **Draft Comparison**: Side-by-side revision analysis
- [ ] **Script History**: Track multiple versions of same script
- [ ] **Better Error Messages**: User-friendly error display

#### Low Priority / Future
- [ ] **Mobile Responsive**: Improve mobile UX
- [ ] **Caching**: Don't re-analyze identical scripts
- [ ] **Rate Limiting**: Prevent abuse
- [ ] **Admin Dashboard**: Usage stats, monitoring

---

## 9. Known Issues & Solutions

### Issue 1: Render Free Tier Cold Starts
**Problem**: Service spins down after 15 min inactivity, 50+ second delay on first request  
**Solution**: This is expected on free tier. For production, upgrade to paid tier or implement keep-alive ping.

### Issue 2: SQLite Database Resets on Deploy
**Problem**: Render free tier has ephemeral filesystem - database resets on each deployment  
**Solution**: Migrate to PostgreSQL (Render provides free PostgreSQL tier)

### Issue 3: Moonshot Content Moderation
**Problem**: Moonshot API rejects scripts with mature content (HBO shows, adult themes) with "high risk" error  
**Solution**: Claude fallback implemented - automatically retries with Claude when Moonshot rejects

### Issue 4: Progress Bar is Simulated
**Problem**: Progress shows 0→25→50→75→100% but not tied to actual LLM progress  
**Status**: Acceptable UX but not precise. Real progress requires LLM streaming tokens.

### Issue 5: Deep Mode Token Limits (FIXED)
**Problem**: Deep mode generates 15-20K tokens but max_tokens was hardcoded to 8K, causing hangs  
**Solution**: Dynamic token limits now implemented (Quick=4K, Standard=8K, Deep=20K)

### Issue 6: Chinese Characters in Output (FIXED)
**Problem**: Kimi K2.5 (bilingual model) occasionally output Chinese text  
**Solution**: Added explicit "Respond in English only" instruction to system prompt

### Issue 7: CORS Errors (FIXED)
**Problem**: Frontend couldn't reach backend due to CORS misconfiguration  
**Solution**: Updated CORS_ORIGINS env var to include all frontend URLs

### Issue 8: SQLite Concurrency (FIXED)
**Problem**: "Concurrent operations are not permitted" errors under load  
**Solution**: Used NullPool to disable connection pooling for SQLite

---

## 10. Deployment Notes

### Current Deployment: Render + Cloudflare Pages

#### Backend (Render.com)
- **Service ID**: srv-d696u314tr6s73cgpft0
- **Region**: Oregon
- **Plan**: Free tier (Web Service)
- **Root Directory**: `/backend`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Python Version**: 3.11.9 (set via .python-version file)

**Auto-Deploy Webhook**:
```
https://api.render.com/deploy/srv-d696u314tr6s73cgpft0?key=h85p2YFAoFc
```
This is configured as a GitHub webhook - every push to main triggers deployment.

#### Frontend (Cloudflare Pages)
- **Project**: coverageiq-frontend
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Environment Variable**: `VITE_API_URL=https://coverageiq-backend.onrender.com`

### Deployment Checklist

Before deploying changes:

1. **Test locally**:
   ```bash
   cd backend && pytest  # if tests exist
   cd frontend && npm run build  # verify no build errors
   ```

2. **Update version** in `main.py` if significant changes

3. **Commit and push**:
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin main
   ```

4. **Verify deployment**:
   - Check Render dashboard for build status
   - Test health endpoint: `curl https://coverageiq-backend.onrender.com/health`
   - Test frontend loads correctly

5. **Update CORS** if new frontend URL:
   - Add new Cloudflare Pages URL to `CORS_ORIGINS` env var in Render

### Rollback Procedure

If deployment fails:
1. Check Render build logs for errors
2. If needed, revert commit: `git revert HEAD`
3. Push revert to trigger new deployment
4. Or manually trigger deploy of previous commit via Render dashboard

---

## 11. Development History

### Build Timeline: February 12-16, 2026

#### Day 1 (Feb 12): Foundation
- Repository setup
- FastAPI scaffold
- React + Vite + Tailwind setup
- Database models with privacy-first design

#### Day 2 (Feb 13-14): Upload & Extraction
- SQLAlchemy models with Alembic migrations
- PDF text extraction (pdfplumber)
- Final Draft (.fdx) parsing (lxml)
- Upload endpoints with memory-only processing

#### Day 3 (Feb 14): LLM Integration
- Moonshot/Kimi API client
- TV pilot-specific prompt templates
- Analysis pipeline with chunking
- 5 subscores + Pass/Consider/Recommend mapping

#### Day 4 (Feb 15 Morning): Report Generation
- Google Docs API integration
- PDF export with ReportLab
- React frontend with report display
- Collapsible sections, score badges, evidence quotes

#### Day 4 Evening (Feb 15): Deployment & Polish
- Render.com backend deployment (2+ hours of debugging)
- Cloudflare Pages frontend deployment
- File upload feature (drag-and-drop later)
- Auto-deploy webhook setup
- CORS configuration
- Moonshot API endpoint fix (.cn → .ai)
- Async job queue for timeout-free analysis
- Progress bar implementation
- Claude fallback for mature content
- Formatting fixes for JSON blobs
- English-only output enforcement
- SQLite concurrency fixes

#### Day 5 (Feb 16): Debugging Marathon
- Fixed SQLAlchemy concurrent session errors
- Fixed DEFAULT_MAX_TOKENS NameError
- Fixed wrong Claude model ID (404 errors)
- Fixed Deep mode token limit (8K → 20K)
- Fixed progress bar hanging at 60% → 85%
- Extended LLM timeout for Deep mode
- Added comprehensive debugging/logging
- **Critical discovery**: Local fixes weren't deployed to production
- Pushed all fixes to GitHub, verified Render deployment

### Session Transcripts Included

Three development session transcripts are included in this directory:
- `dev-session-feb14.jsonl` - Day 3-4 development (Company Theatre + CoverageIQ start)
- `dev-session-feb15.jsonl` - Day 4-5 development (Full deployment)
- `dev-session-feb16.jsonl` - Day 5 debugging (Bug fixes, production issues)

These contain the full conversation history and can be referenced for detailed context.

---

## 12. Next Steps / Roadmap

### Immediate (This Week)
1. **PostgreSQL Migration** - Critical for data persistence on Render
2. **Report History Page** - Frontend view of past analyses
3. **Philip Testing** - Get Philip to test with real Hawco scripts
4. **Quality Feedback** - Iterate on coverage quality based on professional standards

### Short-Term (This Month)
1. **Drag-and-Drop Upload** - Better file upload UX
2. **Real Progress Tracking** - If possible with LLM streaming
3. **User Authentication** - If moving toward multi-user
4. **Error Handling Improvements** - Better user-facing error messages

### Long-Term (3-6 Months)
1. **Draft Comparison** - Side-by-side revision analysis
2. **Commercial Launch** - If internal validation succeeds
3. **Multi-User Support** - Organizations, permissions
4. **API for Integrations** - Hawco internal tools integration

### Technical Debt
1. Migrate from SQLite to PostgreSQL
2. Add comprehensive test suite
3. Set up monitoring (Sentry or similar)
4. Implement proper logging infrastructure

---

## 13. Important Context

### Philip's Communication Style
- Clear, decisive feedback
- Iterative refinement (screenshot → feedback → fix)
- Trusts implementation judgment
- Values speed but prioritizes correctness
- Patient through extended debugging sessions
- "Proper fix" preferred over quick workarounds

### Cost Optimization Strategy
- **Primary LLM**: Moonshot Kimi K2.5 ($0.04/script)
- **Fallback LLM**: Claude ($0.20/script) - only when needed
- **Infrastructure**: Free tiers where possible (Render, Cloudflare Pages)
- **Development**: Use Kimi subagents for implementation, reserve Claude for strategy

### Privacy & Security Priorities
- **ZERO script storage** is critical - scripts are highly confidential
- Only metadata and generated reports stored
- In-memory processing only
- No training on script data
- 90-day retention for reports

### Current Pain Points
1. Database resets on deploy (SQLite on Render) - **highest priority fix**
2. Cold start delays on Render free tier
3. Simulated progress bar (not real progress)
4. No report history view in frontend

### What Philip Values
- Professional-grade coverage quality (comparable to human readers)
- Speed of iteration and deployment
- Privacy and security of scripts
- Cost-effective operation
- Clean, intuitive UI

---

## 📞 Quick Reference

### Health Check
```bash
curl https://coverageiq-backend.onrender.com/health
```

### API Documentation
```
https://coverageiq-backend.onrender.com/docs
```

### Key Files to Know
| File | Purpose |
|------|---------|
| `backend/app/models.py` | Database schema |
| `backend/app/services/prompts.py` | LLM prompts |
| `backend/app/services/llm_client.py` | LLM clients |
| `backend/app/services/analysis.py` | Analysis pipeline |
| `frontend/src/App.tsx` | Main frontend |
| `backend/main.py` | API entry point |

### Emergency Contacts
- **Render Dashboard**: https://dashboard.render.com/web/srv-d696u314tr6s73cgpft0
- **Cloudflare Pages**: https://dash.cloudflare.com (Philip's account)
- **GitHub Repo**: https://github.com/philipriccio/coverageiq

---

**End of Handoff Document**

*Good luck, Mildred! The project is in a solid state - the main thing needed now is the PostgreSQL migration for data persistence, and any refinements Philip requests based on his testing.*
