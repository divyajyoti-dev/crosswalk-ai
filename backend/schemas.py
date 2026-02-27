from pydantic import BaseModel
from typing import Any
from datetime import datetime


class IngestResponse(BaseModel):
    ok: bool
    rows: int


class RunResponse(BaseModel):
    ok: bool
    alerts_created: int
    mappings_created: int


class AlertOut(BaseModel):
    id: int
    project_id: str
    alert_type: str
    severity: str
    title: str
    summary: str
    evidence: Any
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class MappingOut(BaseModel):
    id: int
    project_id: str
    cost_code: str
    task_name: str
    confidence: float
    method: str
    status: str
    updated_at: datetime

    class Config:
        from_attributes = True


class ApproveRequest(BaseModel):
    mapping_id: int


class CreateMappingRequest(BaseModel):
    project_id: str
    cost_code: str
    task_name: str


class MatchingMetrics(BaseModel):
    fuzzy_coverage: float
    llm_coverage: float
    agreement_rate: float
    human_acceptance: dict
