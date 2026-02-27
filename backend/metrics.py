from sqlalchemy.orm import Session
from models import ErpCost, MappingCostcodeTask


def get_matching_metrics(db: Session, project_id: str) -> dict:
    # Total unique cost codes for this project
    all_codes = set(
        r[0]
        for r in db.query(ErpCost.cost_code)
        .filter(ErpCost.project_id == project_id)
        .distinct()
        .all()
    )
    total_codes = len(all_codes) or 1

    # Fuzzy coverage: % of cost_codes with at least one fuzzy suggestion > 0.80
    fuzzy_covered = set(
        r[0]
        for r in db.query(MappingCostcodeTask.cost_code)
        .filter(
            MappingCostcodeTask.project_id == project_id,
            MappingCostcodeTask.method == "fuzzy",
            MappingCostcodeTask.confidence > 0.80,
        )
        .distinct()
        .all()
    )

    # LLM coverage
    llm_covered = set(
        r[0]
        for r in db.query(MappingCostcodeTask.cost_code)
        .filter(
            MappingCostcodeTask.project_id == project_id,
            MappingCostcodeTask.method == "llm",
            MappingCostcodeTask.confidence > 0.80,
        )
        .distinct()
        .all()
    )

    # Agreement rate: % of cost_codes where top-1 fuzzy == top-1 llm
    fuzzy_all = (
        db.query(MappingCostcodeTask)
        .filter(
            MappingCostcodeTask.project_id == project_id,
            MappingCostcodeTask.method == "fuzzy",
        )
        .order_by(MappingCostcodeTask.confidence.desc())
        .all()
    )
    llm_all = (
        db.query(MappingCostcodeTask)
        .filter(
            MappingCostcodeTask.project_id == project_id,
            MappingCostcodeTask.method == "llm",
        )
        .order_by(MappingCostcodeTask.confidence.desc())
        .all()
    )

    fuzzy_top1: dict[str, str] = {}
    for m in fuzzy_all:
        if m.cost_code not in fuzzy_top1:
            fuzzy_top1[m.cost_code] = m.task_name

    llm_top1: dict[str, str] = {}
    for m in llm_all:
        if m.cost_code not in llm_top1:
            llm_top1[m.cost_code] = m.task_name

    common_codes = set(fuzzy_top1) & set(llm_top1)
    if common_codes:
        agreements = sum(1 for c in common_codes if fuzzy_top1[c] == llm_top1[c])
        agreement_rate = agreements / len(common_codes)
    else:
        agreement_rate = 0.0

    # Human acceptance: how many approved mappings per method
    approved = (
        db.query(MappingCostcodeTask)
        .filter(
            MappingCostcodeTask.project_id == project_id,
            MappingCostcodeTask.status == "approved",
        )
        .all()
    )
    fuzzy_accepted = sum(1 for m in approved if m.method == "fuzzy")
    llm_accepted = sum(1 for m in approved if m.method == "llm")
    human_created = sum(1 for m in approved if m.method == "human")

    return {
        "fuzzy_coverage": round(len(fuzzy_covered) / total_codes, 4),
        "llm_coverage": round(len(llm_covered) / total_codes, 4),
        "agreement_rate": round(agreement_rate, 4),
        "human_acceptance": {
            "fuzzy": fuzzy_accepted,
            "llm": llm_accepted,
            "human_created": human_created,
        },
    }
