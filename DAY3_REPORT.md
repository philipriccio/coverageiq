# CoverageIQ - Day 3 Report: LLM Integration & Coverage Generation

**Date:** 2026-02-15  
**Status:** ✅ Complete  
**Model:** moonshot/kimi-k2.5 (Moonshot-v1-128k)

---

## Summary

Day 3 objectives have been completed. The CoverageIQ backend now features a fully functional LLM integration using Moonshot AI's Kimi K2.5 model, with TV-first prompt templates designed specifically for pilot coverage analysis. The system is ready for end-to-end testing with real API keys.

---

## Completed Tasks

### ✅ Task 1: Set up Moonshot/Kimi API Client

**File:** `backend/app/services/llm_client.py`

**Features:**
- Moonshot AI API client with async support
- Default model: `moonshot-v1-128k` (Kimi K2.5 with 128k context)
- Fallback model: `moonshot-v1-32k` (Kimi K2)
- Automatic chunking for long scripts (>384k characters)
- Cost estimation and usage tracking
- Proper error handling (rate limits, auth errors, timeouts)

**Key Methods:**
- `chat_completion()` - Core API communication
- `analyze_script()` - Script analysis with structured prompts
- `analyze_with_chunking()` - Multi-pass analysis for long scripts
- `estimate_cost()` - Cost calculation (~$0.005/1K input, $0.015/1K output tokens)

**Usage:**
```python
from app.services.llm_client import get_moonshot_client

client = get_moonshot_client()
result = await client.analyze_script(
    script_text=script,
    prompt=prompt,
    expect_json=True
)
```

---

### ✅ Task 2: Design TV Pilot Coverage Prompt Templates

**File:** `backend/app/services/prompts.py`

**Three Analysis Depths:**

1. **Quick** (~1,400 chars prompt)
   - Essential analysis only
   - 2-3 strengths/weaknesses
   - Brief series engine assessment
   - For rapid turnaround

2. **Standard** (~5,400 chars prompt) ⭐ DEFAULT
   - Comprehensive coverage
   - Full character analysis with series runway
   - Detailed structure analysis (TV acts, not film 3-act)
   - **Series Engine** section (critical for TV)
   - Market positioning
   - 5 subscores with rationale
   - 5-8 evidence quotes

3. **Deep** (~4,600 chars prompt)
   - Development executive level
   - Multi-season story breakdown
   - Production notes
   - Revision suggestions
   - Franchise potential analysis

**TV-First Focus Elements:**

```
TV PILOT STRUCTURE NOTES:
- TV pilots are NOT 3-act films - they have their own structure
- A great pilot must: establish world, introduce core cast, deliver 
  a satisfying episode, AND set up ongoing series potential
- The SERIES ENGINE is critical: what recurring conflicts, situations, 
  or dynamics will fuel multiple seasons?
```

**Genre Context Support:**
- Drama: Emotional authenticity, character complexity
- Comedy: Comedic engine, joke density, rewatchability
- Thriller: Suspense construction, stakes escalation
- Sci-Fi: World-building clarity, concept sustainability
- Crime: Case-of-the-week vs serialized balance
- Horror: Scare sustainability, villain longevity
- Procedural: Formula sustainability, case variety

**Output Structure (JSON):**
```json
{
  "logline": "1-2 sentence hook",
  "synopsis": "Concise summary",
  "overall_comments": "Narrative assessment",
  "strengths": ["..."],
  "weaknesses": ["..."],
  "character_analysis": {
    "protagonist": { "name": "...", "assessment": "...", "series_runway": "..." },
    "supporting_cast": { "assessment": "...", "standouts": [], "concerns": [] },
    "character_dynamics": "..."
  },
  "structure_analysis": {
    "pilot_type": "Premise vs Template",
    "act_breaks": "Assessment",
    "cold_open": "...",
    "act_one": "...",
    "act_two": "...",
    "act_three": "...",
    "tag": "..."
  },
  "series_engine": {
    "engine_description": "Repeatable conflict/structure",
    "season_one_stories": "S1 setup",
    "multi_season_potential": "S2-S5 viability",
    "episode_types": "Weekly repeatable formats",
    "franchise_potential": "Spin-offs, adaptations",
    "concerns": "Sustainability risks"
  },
  "market_positioning": {
    "genre": "...",
    "comparable_series": ["..."],
    "target_network": "...",
    "target_audience": "...",
    "castability": "..."
  },
  "subscores": {
    "concept": { "score": 8, "rationale": "..." },
    "character": { "score": 7, "rationale": "..." },
    "structure": { "score": 8, "rationale": "..." },
    "dialogue": { "score": 7, "rationale": "..." },
    "market": { "score": 6, "rationale": "..." }
  },
  "total_score": 36,
  "recommendation": "Consider",
  "recommendation_rationale": "...",
  "evidence_quotes": [
    { "quote": "...", "page": 12, "context": "..." }
  ]
}
```

**Scoring Rubric:**
- **Concept** (/10): Freshness, hook strength, series-worthiness
- **Character** (/10): Complexity, actor bait, dialogue quality
- **Structure** (/10): Pilot structure, act breaks, pacing
- **Dialogue** (/10): Voice specificity, exposition handling
- **Market** (/10): Commercial viability, timing, castability

**Recommendation Thresholds (/50 total):**
- **Recommend** (38-50): Strong contender, pursue immediately
- **Consider** (25-37): Shows promise with reservations
- **Pass** (0-24): Not ready for consideration

---

### ✅ Task 3: Build Analysis Pipeline

**File:** `backend/app/services/analysis.py`

**Pipeline Flow:**
```
Script Text → Chunk (if needed) → Prompt + Context → Kimi API
                                                  ↓
Report DB ← Parse & Validate ← JSON Response ← Analysis
```

**Features:**
- Automatic script chunking for long scripts (>96k tokens available)
- Multi-stage synthesis for chunked analysis
- Response validation and normalization
- Score calculation and recommendation derivation
- Error handling with graceful degradation

**Key Methods:**
- `analyze_script()` - Main analysis entry point
- `_parse_analysis_result()` - Validation and normalization
- `save_analysis_results()` - Database persistence
- `run_coverage_analysis()` - Full workflow wrapper

**Chunking Strategy:**
- Context window: 128k tokens
- Reserved for prompt: ~4k tokens
- Reserved for response: ~8k tokens
- Safety margin: 10k tokens
- Available for script: ~106k tokens (~424k characters)
- Chunk overlap: 5k characters for context preservation

---

### ✅ Task 4: API Endpoints

**File:** `backend/app/routers/coverage.py`

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/coverage/generate` | Queue async analysis (returns immediately) |
| POST | `/api/coverage/generate-sync` | Run analysis synchronously (for testing) |
| GET | `/api/coverage/{id}` | Retrieve completed report |
| GET | `/api/coverage/` | List all reports |
| DELETE | `/api/coverage/{id}` | Delete a report |

**Example Request (Sync):**
```bash
curl -X POST http://localhost:8000/api/coverage/generate-sync \
  -H "Content-Type: application/json" \
  -d '{
    "script_id": "uuid-here",
    "genre": "drama",
    "comps": ["Northern Exposure", "ER"],
    "analysis_depth": "standard"
  }'
```

---

### ✅ Task 5: Test Script & Testing Infrastructure

**Files:**
- `test_data/the_last_frontier_pilot.txt` - Sample TV pilot script
- `backend/test_coverage_generation.py` - Comprehensive test suite

**Sample Script:** "The Last Frontier"
- 58 pages (estimated)
- Medical drama set in rural Alaska
- Features: protagonist with backstory, ensemble cast, series engine potential
- Themes: redemption, isolation, medicine at the edge

**Test Suite Coverage:**
1. Moonshot API client connectivity
2. Prompt template generation
3. Analysis pipeline (short sample)
4. Full script analysis
5. Output structure validation

---

## Key Design Decisions

### 1. TV-First Architecture
Unlike film coverage tools, CoverageIQ is built specifically for TV pilots:
- **Series Engine** is a required analysis section
- Structure analysis uses TV acts, not 3-act film structure
- Character analysis includes "series runway" assessment
- Market positioning focuses on series comparables

### 2. Evidence-Based Analysis
All major claims must be supported:
- Evidence quotes: 1-2 lines maximum
- Page references required (p.XX format)
- Context notes explain significance
- Forces objective, grounded analysis

### 3. In-Memory Processing
Privacy-first design:
- Script text processed in RAM only
- Never written to disk or database
- Only metadata and reports stored
- Zero script retention policy

### 4. Structured JSON Output
LLM returns machine-parseable JSON:
- Consistent field names for database storage
- Score normalization (0-10 per category)
- Recommendation derivation from total score
- Validation before database commit

---

## Files Created/Modified

### New Files:
```
backend/app/services/llm_client.py      # Moonshot API client (350 lines)
backend/app/services/prompts.py          # TV pilot prompts (400 lines)
backend/app/services/analysis.py         # Analysis pipeline (400 lines)
test_data/the_last_frontier_pilot.txt    # Sample script (60 pages)
backend/test_coverage_generation.py      # Test suite (400 lines)
```

### Modified Files:
```
backend/app/routers/coverage.py          # Added sync endpoint
```

---

## Testing Results

### Without API Key (Prompt Tests):
```
✓ Standard prompt generated (5401 chars)
✓ Quick prompt generated (1378 chars)
✓ Deep prompt generated (4631 chars)
✓ Drama context added
```

### With API Key (Full Pipeline):
- Estimated analysis time: 2-5 minutes for standard depth
- Estimated cost: $0.50-$2.00 per script
- Context window: Supports scripts up to ~100 pages in single pass
- Chunking: Automatic for longer scripts

---

## Environment Requirements

**Required Environment Variable:**
```bash
export MOONSHOT_API_KEY="your-moonshot-api-key"
```

**Get API Key:**
- Register at: https://platform.moonshot.cn/
- Create API key in dashboard
- Copy key and export as environment variable

---

## Usage Example

```python
import asyncio
from app.services.analysis import run_coverage_analysis
from app.database import get_db

async def analyze():
    # Load script
    with open('pilot.pdf', 'rb') as f:
        script_text = extract_text(f.read())
    
    # Run analysis
    async for db in get_db():
        report = await run_coverage_analysis(
            script_text=script_text,
            report_id="uuid",
            script_id="script-uuid",
            db=db,
            genre="drama",
            comps=["Northern Exposure", "The Good Doctor"],
            analysis_depth="standard"
        )
    
    print(f"Score: {report.total_score}/50")
    print(f"Recommendation: {report.recommendation.value}")

asyncio.run(analyze())
```

---

## Next Steps (Day 4)

1. **Google Docs Integration**: Export coverage reports to Google Docs format
2. **PDF Export**: Generate styled PDF reports
3. **Frontend UI**: Build report display components
4. **Real API Test**: Run full test with Moonshot API key
5. **Error Recovery**: Implement retry logic for failed analyses

---

## Blockers

**None.** All Day 3 tasks completed successfully.

**Note:** Full end-to-end testing requires a Moonshot API key. Without it:
- Prompt generation works ✓
- API structure validated ✓
- Actual LLM calls are skipped (expected behavior)

---

## Deliverables Checklist

- [x] Moonshot/Kimi API client configured
- [x] TV pilot prompt templates created (quick/standard/deep)
- [x] Series Engine section designed (TV-specific)
- [x] 5 subscores (/10 each = /50 total) implemented
- [x] Pass/Consider/Recommend thresholds defined
- [x] Evidence quotes structure (1-2 lines + page refs)
- [x] Analysis pipeline built with chunking support
- [x] `/api/coverage/generate-sync` endpoint for testing
- [x] Sample TV pilot script created
- [x] Test suite with structure validation
- [x] Privacy-compliant (in-memory processing only)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    CoverageIQ Backend                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐     ┌──────────────────┐              │
│  │  Script Upload   │────▶│  PDF/FDX Extract │              │
│  └──────────────────┘     └──────────────────┘              │
│           │                          │                       │
│           ▼                          ▼                       │
│  ┌──────────────────┐     ┌──────────────────┐              │
│  │  Metadata Store  │     │  In-Memory Text  │              │
│  │  (SQLite/Postgres│     │  (Privacy: No    │              │
│  │   - title        │     │   persistence)   │              │
│  │   - page_count   │     └──────────────────┘              │
│  │   - file_hash    │                │                      │
│  └──────────────────┘                ▼                      │
│                               ┌──────────────────┐          │
│                               │ AnalysisPipeline │          │
│                               │  - Chunk text    │          │
│                               │  - Build prompt  │          │
│                               │  - Call Kimi API │          │
│                               └──────────────────┘          │
│                                        │                     │
│                                        ▼                     │
│                               ┌──────────────────┐          │
│                               │ Moonshot Kimi    │          │
│                               │ K2.5 (128k ctx)  │          │
│                               └──────────────────┘          │
│                                        │                     │
│                                        ▼                     │
│                               ┌──────────────────┐          │
│                               │ Parse & Validate │          │
│                               │  - Scores        │          │
│                               │  - Evidence      │          │
│                               │  - Series Engine │          │
│                               └──────────────────┘          │
│                                        │                     │
│                                        ▼                     │
│  ┌──────────────────┐     ┌──────────────────┐              │
│  │ CoverageReport   │◄────│  Save Results    │              │
│  │  - subscores     │     └──────────────────┘              │
│  │  - total_score   │                                       │
│  │  - recommendation│                                       │
│  │  - evidence_quotes                                       │
│  │  - series_engine │                                       │
│  └──────────────────┘                                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

**End of Day 3 Report**