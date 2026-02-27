import logging
from collections import defaultdict
from sqlalchemy.orm import Session
from models import ErpCost, FieldLog, MappingCostcodeTask, RiskAlert

logger = logging.getLogger(__name__)

RISK_KEYWORDS_HIGH = {"safety", "rework", "hazard"}
RISK_KEYWORDS_LOW = {"blocked", "rfi", "delay", "waiting"}
ALL_RISK_KEYWORDS = RISK_KEYWORDS_HIGH | RISK_KEYWORDS_LOW


def generate_alerts(db: Session, project_id: str) -> int:
    """Generate deterministic alerts. Deletes previous alerts for the project first."""

    db.query(RiskAlert).filter(RiskAlert.project_id == project_id).delete()
    db.flush()

    count = 0
    count += _alert_unmapped_spend(db, project_id)
    count += _alert_labor_spike(db, project_id)
    count += _alert_keyword_risk(db, project_id)
    db.commit()
    return count


# ---------------------------------------------------------------------------
# ALERT 1: unmapped_spend (high)
#   actual_to_date > 0 AND (no approved mapping OR no field_log for mapped tasks)
# ---------------------------------------------------------------------------
def _alert_unmapped_spend(db: Session, project_id: str) -> int:
    erp_rows = (
        db.query(ErpCost)
        .filter(ErpCost.project_id == project_id, ErpCost.actual_to_date > 0)
        .all()
    )

    approved = (
        db.query(MappingCostcodeTask.cost_code, MappingCostcodeTask.task_name)
        .filter(
            MappingCostcodeTask.project_id == project_id,
            MappingCostcodeTask.status == "approved",
        )
        .all()
    )
    approved_by_code: dict[str, set[str]] = defaultdict(set)
    for row in approved:
        approved_by_code[row.cost_code].add(row.task_name)

    field_tasks = set(
        r[0]
        for r in db.query(FieldLog.task_name)
        .filter(FieldLog.project_id == project_id)
        .distinct()
        .all()
    )

    count = 0
    for erp in erp_rows:
        mapped_tasks = approved_by_code.get(erp.cost_code, set())
        has_mapping = bool(mapped_tasks)
        has_field_data = bool(mapped_tasks & field_tasks)

        if not has_mapping or not has_field_data:
            db.add(
                RiskAlert(
                    project_id=project_id,
                    alert_type="unmapped_spend",
                    severity="high",
                    title=f"Unmapped Spend: {erp.cost_code} — {erp.cost_code_name}",
                    summary=(
                        f"Cost code {erp.cost_code} ({erp.cost_code_name}) has "
                        f"${erp.actual_to_date:,.2f} actual spend but no verified field activity."
                    ),
                    evidence={
                        "cost_code": erp.cost_code,
                        "cost_code_name": erp.cost_code_name,
                        "actual_to_date": erp.actual_to_date,
                        "budget": erp.budget,
                        "has_approved_mapping": has_mapping,
                        "has_field_data": has_field_data,
                    },
                    status="open",
                )
            )
            count += 1
    return count


# ---------------------------------------------------------------------------
# ALERT 2: labor_spike (med)
#   last 2 days avg > 2x previous 5 days avg  AND  last 2 days total >= 12 hrs
# ---------------------------------------------------------------------------
def _alert_labor_spike(db: Session, project_id: str) -> int:
    logs = (
        db.query(FieldLog)
        .filter(FieldLog.project_id == project_id)
        .order_by(FieldLog.log_date)
        .all()
    )

    by_task: dict[str, list[FieldLog]] = defaultdict(list)
    for log in logs:
        by_task[log.task_name].append(log)

    count = 0
    for task_name, task_logs in by_task.items():
        dates = sorted(set(l.log_date for l in task_logs))
        if len(dates) < 3:
            continue

        last_2_dates = set(dates[-2:])
        prev_dates = set(dates[:-2][-5:])  # up to 5 days before the last 2

        if not prev_dates:
            continue

        last_2_hours = sum(l.hours for l in task_logs if l.log_date in last_2_dates)
        prev_hours = sum(l.hours for l in task_logs if l.log_date in prev_dates)

        last_2_avg = last_2_hours / len(last_2_dates)
        prev_avg = prev_hours / len(prev_dates)

        if prev_avg > 0 and last_2_avg > 2 * prev_avg and last_2_hours >= 12:
            db.add(
                RiskAlert(
                    project_id=project_id,
                    alert_type="labor_spike",
                    severity="med",
                    title=f"Labor Spike: {task_name}",
                    summary=(
                        f"'{task_name}' averaged {last_2_avg:.1f} hrs/day over "
                        f"last 2 days vs {prev_avg:.1f} hrs/day prior."
                    ),
                    evidence={
                        "task_name": task_name,
                        "last_2_days_total_hours": last_2_hours,
                        "last_2_days_avg": round(last_2_avg, 2),
                        "prev_days_avg": round(prev_avg, 2),
                        "spike_ratio": round(last_2_avg / prev_avg, 2),
                    },
                    status="open",
                )
            )
            count += 1
    return count


# ---------------------------------------------------------------------------
# ALERT 3: keyword_risk
#   safety/rework/hazard → med,  blocked/rfi/delay/waiting → low
# ---------------------------------------------------------------------------
def _alert_keyword_risk(db: Session, project_id: str) -> int:
    logs = (
        db.query(FieldLog)
        .filter(FieldLog.project_id == project_id, FieldLog.notes.isnot(None))
        .all()
    )

    count = 0
    for log in logs:
        notes_lower = log.notes.lower()
        found = {kw for kw in ALL_RISK_KEYWORDS if kw in notes_lower}
        if not found:
            continue

        severity = "med" if found & RISK_KEYWORDS_HIGH else "low"
        db.add(
            RiskAlert(
                project_id=project_id,
                alert_type="keyword_risk",
                severity=severity,
                title=f"Risk Keyword in Field Notes ({log.task_name})",
                summary=(
                    f"Keywords [{', '.join(sorted(found))}] found in notes "
                    f"for '{log.task_name}' on {log.log_date}."
                ),
                evidence={
                    "log_id": log.id,
                    "task_name": log.task_name,
                    "log_date": str(log.log_date),
                    "crew": log.crew,
                    "keywords_found": sorted(found),
                    "snippet": log.notes[:200],
                },
                status="open",
            )
        )
        count += 1
    return count
