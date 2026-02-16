# CoverageIQ MVP - Execution Plan
**Prepared for:** Hawco Productions (Philip)  
**Date:** 2026-02-15  
**Updated:** 2026-02-15 (v1.1 — Locked MVP Requirements)  
**Status:** Internal Tool → Potential Commercialization

> **Change Log v1.1:** Updated with Philip's locked MVP requirements: PDF + Final Draft (.fdx) input, Google Docs + PDF output, 5 subscores (/50 total) with Pass/Consider/Recommend mapping, strict privacy rails (zero script storage), and explicit data retention policy.

---

## 1. PRODUCT SPECIFICATION

### 1.1 Core Purpose
CoverageIQ is an AI-powered script coverage tool that analyzes screenplays and generates professional-grade coverage reports traditionally done by human readers.

### 1.2 Target Users
- **Phase 1 (Internal):** Philip at Hawco Productions - single user, full admin access
- **Phase 2 (External):** Screenwriters, producers, script consultants, film schools, coverage services

### 1.3 Core Features (MVP)
| Feature | Priority | Description |
|---------|----------|-------------|
| Script Upload | P0 | PDF primary + Final Draft (.fdx) format support |
| Genre/Comps Selection | P0 | Pre-analysis configuration |
| AI Analysis Engine | P0 | Multi-dimension script analysis |
| Coverage Report Generation | P0 | Google Doc primary output + PDF export |
| Report Storage | P0 | Persistent history with search |
| Draft Comparison | P1 | Side-by-side revision analysis |
| Export Options | P1 | PDF, HTML, JSON export |
| User Auth (Phase 2) | P2 | Multi-user support with roles |

### 1.4 Coverage Report Components
Every report must include:
1. **Logline** (1-2 sentences)
2. **Synopsis** (1 page max)
3. **Overall Comments** (narrative assessment)
4. **Strengths** (bullet list)
5. **Weaknesses** (bullet list)
6. **Character Notes** (analysis of protagonist/antagonist/supporting)
7. **Structure Analysis** (3-act assessment, pacing notes)
8. **Market Positioning** (comparable films, target audience)
9. **Subscores** (5 categories × /10 = /50 total):
   - Concept & Premise (/10)
   - Structure & Pacing (/10)
   - Character & Dialogue (/10)
   - Market Viability (/10)
   - Writing Quality & Voice (/10)
10. **Overall Score** (/50 total mapped to Pass/Consider/Recommend)
    - Pass: 0-24 (Not ready for consideration)
    - Consider: 25-37 (Shows promise with reservations)
    - Recommend: 38-50 (Strong contender, pursue immediately)
11. **Recommendation** (Pass/Consider/Recommend with reasoning derived from /50 total)
12. **Evidence Quotes** (1-2 lines max, clearly labeled direct script quotes with page references; no large excerpts)

---

## 2. USER EXPERIENCE FLOW

### 2.1 Primary Workflow (Happy Path)
```
┌─────────────────────────────────────────────────────────────┐
│  1. DASHBOARD                                               │
│     └─ View previous reports / Start new analysis           │
├─────────────────────────────────────────────────────────────┤
│  2. UPLOAD                                                  │
│     ├─ Drop PDF or Final Draft (.fdx) file                  │
│     ├─ Auto-extract title/page count (memory-only)          │
│     └─ Validation: file type, size, extractable text        │
├─────────────────────────────────────────────────────────────┤
│  3. CONFIGURE                                               │
│     ├─ Select Genre (dropdown: Drama, Comedy, Thriller, etc)│
│     ├─ Input Comparable Films (2-3 references)              │
│     ├─ Select Analysis Depth (Quick/Standard/Deep)          │
│     └─ Optional: Add custom notes/context                   │
├─────────────────────────────────────────────────────────────┤
│  4. PROCESSING                                              │
│     ├─ Extract text from PDF                                │
│     ├─ Chunk and send to LLM                                │
│     ├─ Stream progress (extraction → analysis → synthesis)  │
│     └─ Estimated time: 2-5 minutes                          │
├─────────────────────────────────────────────────────────────┤
│  5. REVIEW REPORT                                           │
│     ├─ View structured coverage                             │
│     ├─ Score breakdown (5 subscores /50 total)              │
│     ├─ Toggle sections expand/collapse                      │
│     ├─ Copy/share link                                      │
│     ├─ Export to Google Doc (primary)                       │
│     └─ Download PDF (secondary)                             │
├─────────────────────────────────────────────────────────────┤
│  6. HISTORY & COMPARISON                                    │
│     ├─ View all past reports (searchable)                   │
│     ├─ Compare two drafts side-by-side                      │
│     └─ Track score changes over revisions                   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Wireframe Descriptions

**Dashboard View:**
- Header: Logo + "New Analysis" button
- Main: Grid of recent reports (thumbnail, title, date, score)
- Empty state: "Upload your first script" with large dropzone

**Upload View:**
- Large dropzone with PDF + Final Draft (.fdx) icons
- File constraints shown (max 5MB, 5-200 pages)
- Progress bar during upload
- Validation errors displayed inline
- Drag-and-drop or click to select PDF or .fdx files

**Analysis View:**
- Real-time progress indicator
- Estimated time remaining
- Cancel button (if needed)
- Preview of extracted text (first page)

**Report View:**
- Sticky header with title, total score /50, recommendation badge (Pass/Consider/Recommend), export buttons
- Score breakdown showing 5 subscores (/10 each)
- Collapsible sections for each component
- Evidence quotes section (1-2 lines max, clearly labeled with page references)
- "Regenerate section" option (if output poor)
- Export to Google Doc (primary) and PDF (secondary)

---

## 3. DATA MODEL

### 3.1 Entity Relationship Diagram
**🔒 PRIVACY-FIRST DESIGN: Scripts and extracted text are NEVER persisted. Only reports and metadata are stored.**

```
┌─────────────┐       ┌─────────────────────────┐       ┌─────────────────┐
│    User     │1──────│   ScriptMetadata        │1──────│  CoverageReport │
├─────────────┤       ├─────────────────────────┤       ├─────────────────┤
│ id (PK)     │       │ id (PK)                 │       │ id (PK)         │
│ email       │       │ user_id (FK)            │       │ metadata_id(FK) │
│ created_at  │       │ filename_hash (SHA256)  │       │ genre           │
│ settings    │       │ title                   │       │ comps           │
└─────────────┘       │ author                  │       │ analysis_depth  │
                      │ page_count              │       │ status          │
                      │ file_hash (SHA256)      │       │ subscores []    │
                      │ format                  │       │ total_score /50 │
                      │ created_at              │       │ recommendation  │
                      └─────────────────────────┘       │ logline         │
                                                        │ synopsis        │
                                                        │ overall_comments│
                                                        │ strengths []    │
                                                        │ weaknesses []   │
                                                        │ character_notes │
                                                        │ structure       │
                                                        │ market_position │
                                                        │ evidence_quotes │  -- 1-2 lines max
                                                        │ created_at      │
                                                        └─────────────────┘
                                                                │
                                                                │ 1:N
                                                                ▼
                                                        ┌─────────────────┐
                                                        │  Comparison     │
                                                        ├─────────────────┤
                                                        │ id (PK)         │
                                                        │ report_a_id(FK) │
                                                        │ report_b_id(FK) │
                                                        │ diff_analysis   │
                                                        │ score_delta     │
                                                        │ created_at      │
                                                        └─────────────────┘
```

### 3.2 Key Fields Detail

**ScriptMetadata Table (NO extracted text stored):**
- `filename_hash`: SHA256 hash of original filename (not the filename itself)
- `file_hash`: SHA256 hash of file content (for duplicate detection)
- `format`: Enum ['pdf', 'fdx'] (PDF primary, Final Draft supported)
- **NO `extracted_text` field** — script content is processed in memory only
- **NO `file_path` field** — source files are never written to disk

**CoverageReport Table:**
- `status`: Enum ['processing', 'completed', 'failed']
- `subscores`: JSON array of 5 category scores (/10 each)
- `total_score`: Integer /50 (sum of subscores)
- `recommendation`: Enum ['Pass', 'Consider', 'Recommend'] derived from /50 total
- `evidence_quotes`: JSON array of {quote, page_ref} (max 1-2 lines each)
- Arrays stored as JSON: `strengths`, `weaknesses`, `subscores`
- **NO `raw_response` field** — full LLM responses are discarded after parsing

### 3.3 File Storage
**Scripts are NEVER stored to disk.**
- Source files processed entirely in memory (RAM)
- No intermediate file storage
- No caching of script content
- Only metadata and generated reports are persisted

---

## 4. TECH STACK RECOMMENDATION

### 4.1 Architecture Overview
```
┌─────────────────────────────────────────────────────────────┐
│                         CLIENT                              │
│              (React + TypeScript + Tailwind)                │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTPS/WSS
┌───────────────────────▼─────────────────────────────────────┐
│                        API SERVER                           │
│              (FastAPI / Node.js + Express)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Auth (JWT)  │  │ Upload      │  │ Analysis Queue      │  │
│  │ Middleware  │  │ Handler     │  │ (Bull/Celery)       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Database   │ │ File Storage │ │  LLM API     │
│  (SQLite →   │ │  (Local →    │ │ (OpenRouter/ │
│  Postgres)   │ │   S3)        │ │  Anthropic)  │
└──────────────┘ └──────────────┘ └──────────────┘
```

### 4.2 Component Details

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Frontend** | React 18 + Vite | Fast dev, great ecosystem, easy to host |
| **Styling** | Tailwind CSS | Utility-first, rapid UI development |
| **State** | Zustand | Lightweight, TypeScript-friendly |
| **Backend** | FastAPI (Python) | Excellent async, easy LLM integration |
| **Database** | SQLite → PostgreSQL | Start simple, migrate when needed |
| **Queue** | Celery + Redis | Async processing, retry logic |
| **PDF Parsing** | pdfplumber + pymupdf | Reliable text extraction |
| **LLM Client** | OpenRouter SDK | Multi-provider, cost optimization |
| **Auth (P2)** | Auth0/Clerk | Enterprise-ready, quick setup |
| **Deployment** | Docker + Fly.io | Simple containerized deployment |

### 4.3 LLM Strategy

**Primary Model:** Claude 3.5 Sonnet (Anthropic)
- Best at long-context analysis
- Excellent for creative writing assessment
- Reliable structured output

**Fallback Models:**
1. GPT-4o (OpenAI) - similar capability, price check
2. Gemini 1.5 Pro (Google) - longest context window
3. Local option: Llama 3.1 70B via Ollama (cost control)

**Cost Optimization:**
- Chunk scripts intelligently (scenes vs pages)
- Cache common analysis patterns
- Use cheaper models for text extraction
- Monitor token usage per report

---

## 5. SECURITY & PRIVACY CONSIDERATIONS

### 5.1 Threat Model
Scripts are highly confidential - leaks can destroy projects.

| Threat | Risk | Mitigation |
|--------|------|------------|
| Script theft | CRITICAL | Local processing, no cloud storage of raw scripts |
| LLM data retention | HIGH | Use zero-retention APIs, no training on data |
| Unauthorized access | HIGH | Auth required, encrypted storage |
| Man-in-the-middle | MEDIUM | TLS 1.3 everywhere |
| Insider threat | MEDIUM | Audit logs, principle of least privilege |

### 5.2 Security Measures

**Data Handling (Privacy Rails):**
- [ ] **NO script storage** — source files processed entirely in memory
- [ ] **NO extracted text retention** — script content never persisted to disk or database
- [ ] **NO raw LLM responses stored** — parsed and discarded immediately
- [ ] Memory-only processing enforced (RAM-only, no swap)
- [ ] No logging of script content (only metadata: title, page count, file hash)
- [ ] Temporary memory buffers cleared immediately after processing

**LLM Privacy:**
- [ ] Use Anthropic's API with data retention disabled
- [ ] Add legal disclaimer: "Scripts processed via third-party AI"
- [ ] Consider on-premise LLM for ultra-sensitive material
- [ ] Never use consumer ChatGPT interface (violates ToS for confidential data)

**Access Control (Phase 2):**
- [ ] JWT-based authentication
- [ ] Role-based access (admin, user, readonly)
- [ ] API rate limiting
- [ ] Session timeout after inactivity

**Compliance Notes:**
- Scripts may contain personal data (GDPR considerations if commercial)
- WGA writers may have specific concerns about AI training
- Document processing terms clearly for commercial launch

### 5.3 Data Retention Policy

**Explicit Data Retention Rules:**

| Data Type | Retention | Action |
|-----------|-----------|--------|
| **Script source files** | Zero retention | Never written to disk; held in memory only during processing |
| **Extracted text** | Zero retention | Parsed and immediately discarded; never stored |
| **Raw LLM responses** | Zero retention | Parsed into report structure, then discarded |
| **Report metadata** | 90 days | Title, page count, file hash, genre, comps |
| **Coverage reports** | 90 days | Generated analysis, scores, recommendations, evidence quotes |
| **Audit logs** | 30 days | Access timestamps, user actions (no script content) |
| **Error logs** | 7 days | Error messages (scrubbed of any script content) |

**User-Initiated Deletion:**
- Users can delete reports immediately (hard delete, no soft delete)
- Deletion cascades to all associated data
- No backups of user data retained after deletion

**Automated Cleanup:**
- Nightly job purges expired data
- No archives maintained beyond retention periods
- Verification: Monthly audit confirms zero script data retention

### 5.4 Security & Privacy Checklist (Pre-Launch)
- [ ] Penetration test on API endpoints
- [ ] Review LLM provider data handling agreements
- [ ] Implement audit logging for all script access
- [ ] Create data retention/deletion policies
- [ ] Backup encryption verification

---

## 6. COST CONTROLS

### 6.1 Cost Breakdown (Per Report)

| Component | Cost Range | Notes |
|-----------|------------|-------|
| PDF Text Extraction | $0 | Local processing |
| Final Draft (.fdx) Parsing | $0 | Local XML parsing |
| LLM Analysis (Claude) | $0.50 - $2.00 | Depends on script length |
| Google Docs API | $0 | Included in GCP free tier |
| Storage (reports only) | ~$0.001 | Minimal metadata storage (zero script storage) |
| Compute | ~$0.05 | Container processing time |
| **Total per report** | **$0.55 - $2.05** | |

### 6.2 Budget Planning

**Internal Use (Phase 1):**
- Estimated 20 scripts/month
- Monthly cost: $12-42
- Acceptable without strict limits

**Commercial (Phase 2):**
- Need tiered pricing
- Set hard limits: max tokens per analysis
- Implement usage quotas per user

### 6.3 Cost Control Mechanisms

1. **Token Limits:** Hard cap at 100k tokens per analysis
2. **Model Fallback:** Auto-switch to cheaper models if costs spike
3. **Caching:** Don't re-analyze identical scripts
4. **Monitoring:** Daily cost alerts via webhook
5. **Pre-processing:** Local deduplication, format optimization

### 6.4 Pricing Strategy (Commercial Phase)

| Tier | Price | Includes |
|------|-------|----------|
| Free | $0 | 1 report/month, watermarked |
| Pro | $29/mo | 20 reports, full features |
| Studio | $99/mo | 100 reports, team sharing |
| Enterprise | Custom | Unlimited, SLA, on-prem option |

---

## 7. SEVEN-DAY BUILD PLAN

### Day 1: Foundation & Setup
**Theme:** Get the infrastructure running

| Task | Time | Deliverable |
|------|------|-------------|
| Initialize project repo | 1h | Git repo with structure |
| Set up FastAPI backend | 2h | `/health` endpoint working |
| Configure database models | 2h | SQLAlchemy models defined |
| Create React frontend scaffold | 2h | Vite + Tailwind running |
| Docker setup | 1h | `docker-compose up` works |

**End of Day 1:** Can run dev environment locally

---

### Day 2: Upload & Text Extraction
**Theme:** Handle script ingestion (memory-only, no persistence)

| Task | Time | Deliverable |
|------|------|-------------|
| Build file upload endpoint | 2h | POST /api/scripts/upload (memory-only) |
| Implement PDF text extraction | 3h | pdfplumber integration (primary format) |
| Implement Final Draft (.fdx) parsing | 1h | XML-based .fdx reader |
| Create upload UI component | 2h | Drag-drop with PDF + .fdx support |

**End of Day 2:** Can upload PDF/.fdx and see extracted text (no files stored)

---

### Day 3: LLM Integration
**Theme:** Connect to AI analysis

| Task | Time | Deliverable |
|------|------|-------------|
| Set up OpenRouter/Anthropic client | 1h | API client configured |
| Design prompt templates | 3h | Structured prompts for each section |
| Build analysis pipeline | 3h | Chunking → LLM → Parsing |
| Test with sample scripts | 1h | 3 test runs, iterate prompts |

**End of Day 3:** Can run analysis manually via API, get structured output

---

### Day 4: Report Generation & UI
**Theme:** Make it usable

| Task | Time | Deliverable |
|------|------|-------------|
| Create report data structures | 2h | JSON schema with 5 subscores (/50 total) |
| Build report display components | 3h | Collapsible sections, score breakdown |
| Implement Google Docs API integration | 2h | Google Doc as primary output format |
| Add PDF export option | 1h | Secondary PDF generation |
| Connect upload → analysis → display | 1h | Full happy path working |

**End of Day 4:** Can upload script and view coverage report in Google Docs + PDF

---

### Day 5: History & Storage
**Theme:** Persistence and retrieval

| Task | Time | Deliverable |
|------|------|-------------|
| Save reports to database | 2h | CRUD operations working |
| Build dashboard view | 2h | List of past reports |
| Implement search/filter | 1h | Title/date search |
| Add report detail view | 2h | Individual report pages |
| Delete/archive functionality | 1h | Soft delete option |

**End of Day 5:** Can view history, re-open old reports

---

### Day 6: Draft Comparison
**Theme:** Value-add feature

| Task | Time | Deliverable |
|------|------|-------------|
| Design comparison UI | 1h | Side-by-side layout |
| Build comparison engine | 3h | Diff analysis logic |
| Score tracking visualization | 2h | Simple chart of changes |
| Implement comparison workflow | 2h | Select two reports, compare |

**End of Day 6:** Can compare two versions of same script

---

### Day 7: Privacy, Security & Polish
**Theme:** Production readiness with privacy-first design

| Task | Time | Deliverable |
|------|------|-------------|
| Add error handling everywhere | 2h | Graceful failures, retry logic |
| Implement memory-only processing | 1h | Verify no script data touches disk |
| Add privacy audit logging | 1h | Structured logs (metadata only, no script content) |
| Verify data retention compliance | 1h | Confirm zero script retention, 90-day report retention |
| Create deployment config | 1h | Fly.io or similar setup |
| Write documentation | 2h | README, API docs, user guide, data retention policy |

**End of Day 7:** MVP ready for internal use with privacy rails enforced

---

## 8. MASTER TODO CHECKLIST (Ordered)

### Phase 1: Foundation
- [ ] 1. Initialize Git repository
- [ ] 2. Set up Python virtual environment
- [ ] 3. Create FastAPI project structure
- [ ] 4. Set up React + Vite + Tailwind
- [ ] 5. Configure Docker and docker-compose
- [ ] 6. Create database models (SQLAlchemy) — **NO script storage, only metadata**
- [ ] 7. Set up database migrations (Alembic)
- [ ] 8. Configure environment variables (.env)

### Phase 2: Core Features
- [ ] 9. Build file upload API endpoint (memory-only, no disk writes)
- [ ] 10. Implement PDF text extraction (pdfplumber) — primary format
- [ ] 11. Implement Final Draft (.fdx) parsing — XML-based format support
- [ ] 12. Create upload UI with drag-drop (PDF + .fdx support)
- [ ] 13. Set up LLM API client (Anthropic)
- [ ] 14. Design prompt templates for 5 subscores (/10 each) + evidence quotes
- [ ] 15. Build async analysis pipeline (Celery) with memory-only processing
- [ ] 16. Create report data structures (subscores /50 total, Pass/Consider/Recommend mapping)
- [ ] 17. Build report display UI components with score breakdown
- [ ] 18. Implement Google Docs API integration (primary output)
- [ ] 19. Add PDF export functionality (secondary output)

### Phase 3: Persistence
- [ ] 20. Wire up database storage for reports + metadata only (NO script content)
- [ ] 21. Build dashboard/history view
- [ ] 22. Implement report search/filter
- [ ] 23. Create individual report pages
- [ ] 24. Add delete functionality (hard delete, immediate purge)

### Phase 4: Advanced Features
- [ ] 25. Design draft comparison UI
- [ ] 26. Implement comparison logic
- [ ] 27. Add score tracking/charting
- [ ] 28. Create comparison workflow

### Phase 5: Production
- [ ] 29. Add comprehensive error handling
- [ ] 30. Implement memory-only processing verification (no script data on disk)
- [ ] 31. Add privacy audit logging (metadata only, no script content)
- [ ] 32. Implement data retention automation (90-day report expiry)
- [ ] 33. Set up monitoring (Sentry/similar)
- [ ] 34. Configure deployment (Fly.io)
- [ ] 35. Write user documentation
- [ ] 36. Create API documentation
- [ ] 37. Write data retention policy document
- [ ] 38. Privacy & security review

### Phase 6: Commercial Prep (Future)
- [ ] 36. Multi-user authentication system
- [ ] 37. Stripe integration for payments
- [ ] 38. Usage quotas and limits
- [ ] 39. Team/organization support
- [ ] 40. Admin dashboard
- [ ] 41. White-label options
- [ ] 42. API access for enterprise

---

## 9. TODAY'S FIRST TASKS (Day 1)

### Immediate Actions (Next 4 Hours)

#### Task 1: Repository Setup (30 min)
```bash
# Commands to run
mkdir coverageiq
cd coverageiq
git init
echo "# CoverageIQ" > README.md
echo ".env" > .gitignore
echo "__pycache__/" >> .gitignore
echo "node_modules/" >> .gitignore
echo "*.db" >> .gitignore
git add .
git commit -m "Initial commit"
```

#### Task 2: Backend Scaffold (1 hour)
- Create `backend/` directory
- Set up Python virtual environment
- Install FastAPI, SQLAlchemy, Alembic
- Create basic folder structure:
  ```
  backend/
  ├── app/
  │   ├── __init__.py
  │   ├── main.py          # FastAPI app
  │   ├── config.py        # Settings
  │   ├── models.py        # Database models
  │   ├── routers/
  │   │   └── scripts.py   # Upload endpoints
  │   └── services/
  │       └── pdf_extractor.py
  ├── alembic/             # Migrations
  ├── tests/
  └── requirements.txt
  ```

#### Task 3: Frontend Scaffold (1 hour)
- Create `frontend/` directory
- Run: `npm create vite@latest . -- --template react-ts`
- Install Tailwind CSS
- Create folder structure:
  ```
  frontend/
  ├── src/
  │   ├── components/
  │   │   ├── Upload/
  │   │   └── Dashboard/
  │   ├── pages/
  │   ├── services/
  │   │   └── api.ts
  │   └── App.tsx
  └── package.json
  ```

#### Task 4: Docker Setup (1.5 hours)
- Create `Dockerfile` for backend
- Create `Dockerfile` for frontend (dev mode)
- Create `docker-compose.yml` with:
  - Backend service
  - Frontend service
  - Redis (for future queue)
  - PostgreSQL (or use SQLite for now)
- Test: `docker-compose up` should start everything

#### Task 5: Verify & Commit (30 min)
- Test both services communicate
- Verify hot reload works
- Commit Day 1 progress

### Deliverable for Today
A working development environment where:
- Backend runs on http://localhost:8000
- Frontend runs on http://localhost:5173
- Both can communicate
- Code changes auto-reload
- Can make first git commit with structure

---

## 10. RISK MITIGATION

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| PDF extraction fails on complex layouts | Medium | High | Test with 20+ diverse scripts, fallback to OCR |
| LLM costs higher than expected | Medium | Medium | Set hard limits, implement caching |
| LLM output quality inconsistent | Medium | High | A/B test prompts, add manual override |
| Security breach/script leak | Low | Critical | Encrypt everything, minimal data retention |
| Analysis takes too long | Medium | Medium | Streaming responses, progress indicators |

---

## 11. SUCCESS METRICS

### MVP Success Criteria
- [ ] Can process 90%+ of PDF and Final Draft (.fdx) scripts successfully
- [ ] Analysis completes in under 5 minutes
- [ ] Report quality matches human reader (Philip's assessment)
- [ ] Scoring correctly implements 5 subscores (/10) = /50 total with Pass/Consider/Recommend mapping
- [ ] Evidence quotes limited to 1-2 lines max with page references
- [ ] Zero script data stored (verified via audit)
- [ ] Google Doc output functional as primary format
- [ ] Costs under $3/report

### Phase 2 Success Criteria
- [ ] 100+ paying users
- [ ] <5% churn rate
- [ ] Positive unit economics
- [ ] NPS score > 40

---

## 12. NEXT STEPS AFTER MVP

1. **Week 2-4:** Internal testing with Hawco scripts
2. **Month 2:** Invite beta users (5-10 screenwriters)
3. **Month 3:** Iterate based on feedback
4. **Month 4:** Decide on commercialization path
5. **Month 5-6:** If yes, build Phase 2 features

---

**Document Version:** 1.1  
**Prepared by:** Kimi  
**Review Date:** Post Day 7
