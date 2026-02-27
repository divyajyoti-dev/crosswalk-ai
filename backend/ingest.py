import csv
import io
from datetime import date
from sqlalchemy.orm import Session
from models import ErpCost, FieldLog


def ingest_erp_csv(db: Session, file_content: str) -> int:
    reader = csv.DictReader(io.StringIO(file_content))
    count = 0
    for row in reader:
        entry = ErpCost(
            project_id=row["project_id"].strip(),
            cost_code=row["cost_code"].strip(),
            cost_code_name=row["cost_code_name"].strip(),
            budget=float(row.get("budget", 0) or 0),
            actual_to_date=float(row.get("actual_to_date", 0) or 0),
            as_of_date=(
                date.fromisoformat(row["as_of_date"].strip())
                if row.get("as_of_date", "").strip()
                else None
            ),
        )
        db.add(entry)
        count += 1
    db.commit()
    return count


def ingest_field_csv(db: Session, file_content: str) -> int:
    reader = csv.DictReader(io.StringIO(file_content))
    count = 0
    for row in reader:
        entry = FieldLog(
            project_id=row["project_id"].strip(),
            log_date=date.fromisoformat(row["log_date"].strip()),
            task_name=row["task_name"].strip(),
            crew=row.get("crew", "").strip() or None,
            hours=float(row["hours"]),
            pct_complete=(
                float(row["pct_complete"])
                if row.get("pct_complete", "").strip()
                else None
            ),
            notes=row.get("notes", "").strip() or None,
        )
        db.add(entry)
        count += 1
    db.commit()
    return count
