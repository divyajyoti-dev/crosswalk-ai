import logging
from datetime import date
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from db import get_db, init_db
from models import ErpCost, FieldLog, MappingCostcodeTask, RiskAlert
from schemas import (
    IngestResponse,
    RunResponse,
    AlertOut,
    MappingOut,
    ApproveRequest,
    CreateMappingRequest,
    MatchingMetrics,
)
from ingest import ingest_erp_csv, ingest_field_csv
from matching import run_matching
from alerts import generate_alerts
from metrics import get_matching_metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Database tables created")
    yield


app = FastAPI(title="ForgeSight API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _resolve_project_id(db: Session, project_id: str | None) -> str:
    if project_id:
        return project_id
    row = db.query(ErpCost.project_id).first()
    if row:
        return row[0]
    raise HTTPException(status_code=400, detail="No data ingested yet")


# ---------------------------------------------------------------------------
# Ingest
# ---------------------------------------------------------------------------
@app.post("/ingest/erp", response_model=IngestResponse)
async def ingest_erp(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = (await file.read()).decode("utf-8")
    rows = ingest_erp_csv(db, content)
    return IngestResponse(ok=True, rows=rows)


@app.post("/ingest/field", response_model=IngestResponse)
async def ingest_field(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = (await file.read()).decode("utf-8")
    rows = ingest_field_csv(db, content)
    return IngestResponse(ok=True, rows=rows)


# ---------------------------------------------------------------------------
# Run pipeline
# ---------------------------------------------------------------------------
@app.post("/run", response_model=RunResponse)
async def run_pipeline(
    project_id: str | None = None, db: Session = Depends(get_db)
):
    pid = _resolve_project_id(db, project_id)
    mappings_created = run_matching(db, pid)
    alerts_created = generate_alerts(db, pid)
    return RunResponse(
        ok=True, alerts_created=alerts_created, mappings_created=mappings_created
    )


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------
@app.get("/alerts")
async def list_alerts(db: Session = Depends(get_db)):
    alerts = db.query(RiskAlert).order_by(RiskAlert.created_at.desc()).all()
    return {"alerts": [AlertOut.model_validate(a) for a in alerts]}


@app.get("/alerts/{alert_id}")
async def get_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(RiskAlert).filter(RiskAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"alert": AlertOut.model_validate(alert)}


@app.post("/alerts/{alert_id}/ack")
async def ack_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(RiskAlert).filter(RiskAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = "ack"
    db.commit()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Mappings
# ---------------------------------------------------------------------------
@app.get("/mappings")
async def list_mappings(db: Session = Depends(get_db)):
    mappings = (
        db.query(MappingCostcodeTask)
        .order_by(MappingCostcodeTask.updated_at.desc())
        .all()
    )
    return {"mappings": [MappingOut.model_validate(m) for m in mappings]}


@app.post("/mappings/approve")
async def approve_mapping(req: ApproveRequest, db: Session = Depends(get_db)):
    mapping = (
        db.query(MappingCostcodeTask)
        .filter(MappingCostcodeTask.id == req.mapping_id)
        .first()
    )
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    mapping.status = "approved"
    mapping.method = "human"
    db.commit()
    return {"ok": True}


@app.post("/mappings/create")
async def create_mapping(req: CreateMappingRequest, db: Session = Depends(get_db)):
    mapping = MappingCostcodeTask(
        project_id=req.project_id,
        cost_code=req.cost_code,
        task_name=req.task_name,
        confidence=1.0,
        method="human",
        status="approved",
    )
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    return {"ok": True, "id": mapping.id}


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
@app.get("/metrics/matching", response_model=MatchingMetrics)
async def matching_metrics(
    project_id: str | None = None, db: Session = Depends(get_db)
):
    pid = _resolve_project_id(db, project_id)
    return get_matching_metrics(db, pid)


# ---------------------------------------------------------------------------
# Metadata (for frontend dropdowns)
# ---------------------------------------------------------------------------
@app.get("/meta/cost-codes")
async def get_cost_codes(db: Session = Depends(get_db)):
    rows = db.query(ErpCost.cost_code, ErpCost.cost_code_name).distinct().all()
    return {"cost_codes": [{"code": r[0], "name": r[1]} for r in rows]}


@app.get("/meta/task-names")
async def get_task_names(db: Session = Depends(get_db)):
    rows = db.query(FieldLog.task_name).distinct().all()
    return {"task_names": [r[0] for r in rows]}


# ---------------------------------------------------------------------------
# Seed — small mechanical example dataset
# ---------------------------------------------------------------------------
@app.post("/seed")
async def seed_data(db: Session = Depends(get_db)):
    pid = "MECH-001"

    # Clear existing seed data
    db.query(RiskAlert).filter(RiskAlert.project_id == pid).delete()
    db.query(MappingCostcodeTask).filter(MappingCostcodeTask.project_id == pid).delete()
    db.query(FieldLog).filter(FieldLog.project_id == pid).delete()
    db.query(ErpCost).filter(ErpCost.project_id == pid).delete()
    db.flush()

    # ERP cost codes
    erp_data = [
        ("1500", "Ductwork Installation", 50000, 32000),
        ("1510", "VAV Box Installation", 25000, 18000),
        ("2200", "Electrical Rough-in", 40000, 15000),
        ("3300", "Demolition", 15000, 12000),
        ("4100", "Hanger & Support Installation", 20000, 8500),
    ]
    for code, name, budget, actual in erp_data:
        db.add(
            ErpCost(
                project_id=pid,
                cost_code=code,
                cost_code_name=name,
                budget=budget,
                actual_to_date=actual,
                as_of_date=date(2024, 3, 10),
            )
        )

    # Field logs — includes a labor spike on "Hang duct" + risk keywords in notes
    field_data = [
        # Hang duct: steady ~4 hrs, then spike to 14-15 on last 2 days
        ("2024-03-01", "Hang duct", "Crew A", 4.0, 0.05, None),
        ("2024-03-02", "Hang duct", "Crew A", 4.0, 0.10, None),
        ("2024-03-03", "Hang duct", "Crew A", 4.5, 0.15, None),
        ("2024-03-04", "Hang duct", "Crew A", 3.5, 0.20, None),
        ("2024-03-05", "Hang duct", "Crew A", 4.0, 0.25, None),
        ("2024-03-06", "Hang duct", "Crew A", 4.0, 0.30, None),
        ("2024-03-07", "Hang duct", "Crew A", 3.5, 0.35, None),
        ("2024-03-09", "Hang duct", "Crew A", 14.0, 0.50, None),
        (
            "2024-03-10",
            "Hang duct",
            "Crew A",
            15.0,
            0.60,
            "Safety concern — working at height near open shaft",
        ),
        # Install VAV
        ("2024-03-02", "Install VAV", "Crew B", 5.0, 0.10, None),
        ("2024-03-03", "Install VAV", "Crew B", 5.0, 0.20, None),
        ("2024-03-04", "Install VAV", "Crew B", 5.5, 0.30, None),
        ("2024-03-05", "Install VAV", "Crew B", 5.0, 0.40, None),
        ("2024-03-06", "Install VAV", "Crew B", 4.5, 0.50, None),
        ("2024-03-07", "Install VAV", "Crew B", 5.0, 0.60, None),
        ("2024-03-08", "Install VAV", "Crew B", 5.0, 0.70, None),
        # Run wiring
        ("2024-03-03", "Run wiring", "Crew C", 6.0, 0.05, None),
        ("2024-03-04", "Run wiring", "Crew C", 6.0, 0.15, None),
        (
            "2024-03-05",
            "Run wiring",
            "Crew C",
            5.5,
            0.25,
            "Rework needed on panel B wiring per updated drawings",
        ),
        ("2024-03-06", "Run wiring", "Crew C", 6.0, 0.35, None),
        ("2024-03-07", "Run wiring", "Crew C", 6.5, 0.45, None),
        # Demo duct
        ("2024-03-01", "Demo duct", "Crew D", 8.0, 0.30, None),
        (
            "2024-03-02",
            "Demo duct",
            "Crew D",
            7.5,
            0.55,
            "Found blocked access in corridor, waiting on GC to clear path",
        ),
        ("2024-03-03", "Demo duct", "Crew D", 8.0, 0.80, None),
        # Install hangers
        ("2024-03-04", "Install hangers", "Crew A", 3.0, 0.10, None),
        ("2024-03-05", "Install hangers", "Crew A", 3.0, 0.20, None),
        ("2024-03-06", "Install hangers", "Crew A", 3.5, 0.30, None),
        ("2024-03-07", "Install hangers", "Crew A", 3.0, 0.40, None),
        ("2024-03-08", "Install hangers", "Crew A", 3.0, 0.50, None),
    ]

    for log_date, task, crew, hours, pct, notes in field_data:
        db.add(
            FieldLog(
                project_id=pid,
                log_date=date.fromisoformat(log_date),
                task_name=task,
                crew=crew,
                hours=hours,
                pct_complete=pct,
                notes=notes,
            )
        )

    db.commit()
    return {
        "ok": True,
        "project_id": pid,
        "erp_rows": len(erp_data),
        "field_rows": len(field_data),
    }
