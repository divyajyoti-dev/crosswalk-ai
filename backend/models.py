from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, JSON
from sqlalchemy.sql import func

from db import Base


class ErpCost(Base):
    __tablename__ = "erp_cost"
    id = Column(Integer, primary_key=True)
    project_id = Column(String, nullable=False, index=True)
    cost_code = Column(String, nullable=False)
    cost_code_name = Column(String, nullable=False)
    budget = Column(Float, default=0)
    actual_to_date = Column(Float, default=0)
    as_of_date = Column(Date)


class FieldLog(Base):
    __tablename__ = "field_log"
    id = Column(Integer, primary_key=True)
    project_id = Column(String, nullable=False, index=True)
    log_date = Column(Date, nullable=False)
    task_name = Column(String, nullable=False)
    crew = Column(String, nullable=True)
    hours = Column(Float, nullable=False)
    pct_complete = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)


class MappingCostcodeTask(Base):
    __tablename__ = "mapping_costcode_task"
    id = Column(Integer, primary_key=True)
    project_id = Column(String, nullable=False, index=True)
    cost_code = Column(String, nullable=False)
    task_name = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    method = Column(String, nullable=False)  # fuzzy | llm | human
    status = Column(String, default="suggested")  # suggested | approved | rejected
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class RiskAlert(Base):
    __tablename__ = "risk_alert"
    id = Column(Integer, primary_key=True)
    project_id = Column(String, nullable=False, index=True)
    alert_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)  # high | med | low
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    evidence = Column(JSON)
    status = Column(String, default="open")  # open | ack | resolved
    created_at = Column(DateTime, server_default=func.now())
