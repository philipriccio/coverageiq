# CoverageIQ

AI-powered script coverage generation for TV pilots and feature films.

## Features

- 📄 **PDF & Final Draft (.fdx) Support**: Upload scripts in industry-standard formats
- 🤖 **AI-Powered Analysis**: Powered by Moonshot Kimi K2.5 with 128k context
- 📊 **Comprehensive Reports**: Logline, synopsis, scores, strengths, weaknesses, and evidence quotes
- 📝 **Google Docs Export**: Primary output format with professional formatting
- 📑 **PDF Export**: Secondary format with color-coded recommendations
- 🔒 **Privacy First**: Scripts processed in memory only, never stored

## Tech Stack

- **Backend:** FastAPI + Python 3.11 + SQLAlchemy
- **Frontend:** React + TypeScript + Vite
- **Database:** SQLite (PostgreSQL ready)
- **AI:** Moonshot Kimi K2.5
- **PDF:** ReportLab
- **Google Docs:** Google API Client

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Moonshot API key (get at https://platform.moonshot.cn/)
- Google OAuth credentials (for Google Docs export)

### Setup

1. **Clone and enter directory:**
```bash
cd coverageiq
```

2. **Setup Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Setup Frontend:**
```bash
cd frontend
npm install
```

4. **Environment Variables:**
```bash
export MOONSHOT_API_KEY="your-key-here"
```

### Running Development Mode

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Access:**
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

### Google Docs Export Setup

Run once to authenticate:
```bash
python setup_google_auth.py
```

Follow the browser prompts to authorize CoverageIQ with your Google account.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/models` | List AI models |
| POST | `/api/scripts/upload` | Upload script |
| POST | `/api/coverage/generate` | Queue coverage analysis |
| POST | `/api/coverage/generate-sync` | Run analysis synchronously |
| GET | `/api/coverage/{id}` | Get coverage report |
| GET | `/api/coverage/` | List all reports |
| POST | `/api/coverage/{id}/export/google-doc` | Export to Google Docs |
| POST | `/api/coverage/{id}/export/pdf` | Export to PDF |
| DELETE | `/api/coverage/{id}` | Delete report |

## Scoring System

- **5 Categories × /10 = /50 Total:**
  - Concept & Premise
  - Structure & Pacing
  - Character & Dialogue
  - Market Viability
  - Writing Quality & Voice

- **Recommendations:**
  - 🔴 **Pass** (0-24): Not ready for consideration
  - 🟡 **Consider** (25-37): Shows promise with reservations
  - 🟢 **Recommend** (38-50): Strong contender

## Report Components

Every coverage report includes:
1. **Logline** (1-2 sentence hook)
2. **Synopsis** (concise summary)
3. **Overall Comments** (narrative assessment)
4. **Strengths** (bullet list)
5. **Weaknesses** (bullet list)
6. **Character Notes** (protagonist, supporting cast, dynamics)
7. **Structure Analysis** (TV pilot structure assessment)
8. **Market Positioning** (comparable series, target audience)
9. **Series Engine** (what fuels multiple seasons)
10. **Subscores** (5 categories × /10)
11. **Total Score** (/50)
12. **Recommendation** (Pass/Consider/Recommend)
13. **Evidence Quotes** (1-2 lines max with page references)

## Project Structure

```
coverageiq/
├── backend/                   # FastAPI application
│   ├── app/
│   │   ├── routers/
│   │   │   ├── scripts.py     # Script upload endpoints
│   │   │   └── coverage.py    # Coverage generation & export
│   │   ├── services/
│   │   │   ├── llm_client.py  # Moonshot API client
│   │   │   ├── prompts.py     # TV pilot prompts
│   │   │   ├── analysis.py    # Analysis pipeline
│   │   │   ├── google_docs_export.py  # Google Docs export
│   │   │   └── pdf_export.py  # PDF generation
│   │   ├── models.py          # Database models
│   │   └── database.py        # DB configuration
│   ├── test_data/             # Sample scripts
│   └── main.py                # Application entry
├── frontend/                  # React application
│   └── src/
│       ├── App.tsx            # Main UI with ReportViewer
│       └── App.css            # Styling
├── test_data/                 # Sample TV pilot scripts
├── setup_google_auth.py       # OAuth setup helper
└── docker-compose.yml         # Docker orchestration
```

## Testing

**With Sample Script:**
```bash
# Use the included test script
cat test_data/the_last_frontier_pilot.txt
```

**Test PDF Export:**
```bash
curl -X POST http://localhost:8000/api/coverage/{report_id}/export/pdf \
  -o coverage_report.pdf
```

**Test Google Docs Export:**
```bash
curl -X POST http://localhost:8000/api/coverage/{report_id}/export/google-doc \
  -H "Content-Type: application/json" \
  -d '{"email": "philipriccio@gmail.com"}'
```

## Development Status

### Day 1 ✅ Foundation
- Git repo initialized
- FastAPI backend
- React+Vite+TS frontend
- Docker configuration

### Day 2 ✅ Upload & Text Extraction
- File upload endpoints
- PDF text extraction
- Final Draft (.fdx) parsing
- Upload UI component

### Day 3 ✅ LLM Integration
- Moonshot/Kimi API client
- TV pilot prompt templates
- Analysis pipeline with chunking
- Structured JSON output

### Day 4 ✅ Report Generation & UI
- Google Docs export functionality
- PDF export with ReportLab
- React ReportViewer component
- Collapsible sections
- Score badges (color-coded)
- Evidence quotes display
- Full end-to-end flow

### Day 5 (Planned) History & Storage
- Dashboard view
- Report history
- Search/filter
- Draft comparison

## Privacy & Security

🔒 **Privacy-First Design:**
- Script content processed **in memory only**
- **Never stored** to disk or database
- Only metadata and generated reports persisted
- Zero script retention policy

📋 **Data Retention:**
- Reports: 90 days
- Audit logs: 30 days
- Error logs: 7 days (scrubbed)

## License

Internal use only - Hawco Productions

## Support

For issues or questions, contact Philip at philipriccio@gmail.com
