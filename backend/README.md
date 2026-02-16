# CoverageIQ Backend

FastAPI backend for CoverageIQ - AI-powered script coverage generation.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

API will be available at http://localhost:8000

## Endpoints

- `GET /` - Root
- `GET /health` - Health check
- `GET /api/models` - List available LLM models
- `POST /api/scripts/upload` - Upload a script
- `POST /api/coverage/generate` - Generate coverage
- `GET /api/coverage/{id}` - Get coverage by ID
