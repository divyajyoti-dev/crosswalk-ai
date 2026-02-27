# ForgeSight Backend

Risk Alert Dashboard backend for construction cost reconciliation.

## Prerequisites

- Python 3.11+
- PostgreSQL 15+

## Quick Start

### 1. Start PostgreSQL

```bash
docker run -d --name forgesight-pg \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=forgesight \
  -p 5432:5432 \
  postgres:15
```

### 2. Setup Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 3. Run

```bash
uvicorn main:app --reload --port 8000
```

## Test It

```bash
# Seed sample data
curl -X POST http://localhost:8000/seed

# Run matching + alert pipeline
curl -X POST http://localhost:8000/run

# View alerts
curl http://localhost:8000/alerts | python -m json.tool

# View single alert
curl http://localhost:8000/alerts/1 | python -m json.tool

# View mappings
curl http://localhost:8000/mappings | python -m json.tool

# View matching metrics
curl http://localhost:8000/metrics/matching | python -m json.tool

# Approve a mapping (use an id from /mappings)
curl -X POST http://localhost:8000/mappings/approve \
  -H "Content-Type: application/json" \
  -d '{"mapping_id": 1}'

# Create a manual mapping
curl -X POST http://localhost:8000/mappings/create \
  -H "Content-Type: application/json" \
  -d '{"project_id": "MECH-001", "cost_code": "1500", "task_name": "Hang duct"}'

# Re-run pipeline after approvals to see alerts update
curl -X POST http://localhost:8000/run
```

## CSV Upload

### ERP CSV Format

```csv
project_id,cost_code,cost_code_name,budget,actual_to_date,as_of_date
MECH-001,1500,Ductwork Installation,50000,32000,2024-03-10
MECH-001,1510,VAV Box Installation,25000,18000,2024-03-10
```

### Field Log CSV Format

```csv
project_id,log_date,task_name,crew,hours,pct_complete,notes
MECH-001,2024-03-01,Hang duct,Crew A,4,0.05,
MECH-001,2024-03-02,Demo duct,Crew D,7.5,0.55,Found blocked access
```

### Upload via curl

```bash
curl -X POST http://localhost:8000/ingest/erp -F "file=@erp_export.csv"
curl -X POST http://localhost:8000/ingest/field -F "file=@field_log.csv"
```

## Enable Real LLM Matching

Set in `.env`:

```
LLM_API_KEY=sk-...
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

Works with any OpenAI-compatible API. Without an API key, LLM matches are stubbed by jittering fuzzy results.

## Architecture

```
main.py        FastAPI app, all routes, seed endpoint
db.py          SQLAlchemy engine + session
models.py      4 tables: erp_cost, field_log, mapping_costcode_task, risk_alert
schemas.py     Pydantic request/response models
ingest.py      CSV → database
matching.py    RapidFuzz + optional LLM matching
alerts.py      Deterministic alert generation (no LLM)
metrics.py     Fuzzy vs LLM coverage, agreement, human acceptance
```

## Design Rules

- **LLM never decides alerts** — alerts are deterministic only
- **Matching logic is separate from alert logic**
- **Human overrides are preserved** across pipeline re-runs
