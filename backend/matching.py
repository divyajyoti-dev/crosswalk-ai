import os
import json
import logging
import random
from sqlalchemy.orm import Session
from rapidfuzz import fuzz
from models import ErpCost, FieldLog, MappingCostcodeTask

logger = logging.getLogger(__name__)


def generate_fuzzy_matches(db: Session, project_id: str) -> int:
    """For each cost_code_name, compare against unique task_names using token_set_ratio.
    Insert top 3 matches per cost_code. method='fuzzy'."""

    cost_codes = (
        db.query(ErpCost.cost_code, ErpCost.cost_code_name)
        .filter(ErpCost.project_id == project_id)
        .distinct()
        .all()
    )
    task_names = [
        r[0]
        for r in db.query(FieldLog.task_name)
        .filter(FieldLog.project_id == project_id)
        .distinct()
        .all()
    ]

    if not cost_codes or not task_names:
        return 0

    # Clear old fuzzy mappings
    db.query(MappingCostcodeTask).filter(
        MappingCostcodeTask.project_id == project_id,
        MappingCostcodeTask.method == "fuzzy",
    ).delete()

    count = 0
    for cost_code, cost_code_name in cost_codes:
        scored = []
        for task in task_names:
            score = fuzz.token_set_ratio(cost_code_name.lower(), task.lower())
            scored.append((task, score / 100.0))

        scored.sort(key=lambda x: x[1], reverse=True)
        for task, conf in scored[:3]:
            db.add(
                MappingCostcodeTask(
                    project_id=project_id,
                    cost_code=cost_code,
                    task_name=task,
                    confidence=round(conf, 4),
                    method="fuzzy",
                    status="suggested",
                )
            )
            count += 1

    db.commit()
    return count


def generate_llm_matches(db: Session, project_id: str) -> int:
    """If LLM_API_KEY set, prompt an OpenAI-compatible API.
    Otherwise stub by jittering fuzzy results."""

    api_key = os.getenv("LLM_API_KEY", "")

    cost_codes = (
        db.query(ErpCost.cost_code, ErpCost.cost_code_name)
        .filter(ErpCost.project_id == project_id)
        .distinct()
        .all()
    )
    task_names = [
        r[0]
        for r in db.query(FieldLog.task_name)
        .filter(FieldLog.project_id == project_id)
        .distinct()
        .all()
    ]

    if not cost_codes or not task_names:
        return 0

    # Clear old llm mappings
    db.query(MappingCostcodeTask).filter(
        MappingCostcodeTask.project_id == project_id,
        MappingCostcodeTask.method == "llm",
    ).delete()

    count = 0

    if api_key:
        try:
            count = _llm_real(db, project_id, api_key, cost_codes, task_names)
            return count
        except Exception as e:
            logger.error(f"LLM matching failed, falling back to stub: {e}")
            db.rollback()

    # Stub: reuse fuzzy results with jittered confidence
    logger.info("LLM_API_KEY not set — stubbing LLM matches from fuzzy results")
    fuzzy_mappings = (
        db.query(MappingCostcodeTask)
        .filter(
            MappingCostcodeTask.project_id == project_id,
            MappingCostcodeTask.method == "fuzzy",
        )
        .all()
    )

    for fm in fuzzy_mappings:
        jitter = random.uniform(-0.05, 0.05)
        conf = max(0.0, min(1.0, fm.confidence + jitter))
        db.add(
            MappingCostcodeTask(
                project_id=project_id,
                cost_code=fm.cost_code,
                task_name=fm.task_name,
                confidence=round(conf, 4),
                method="llm",
                status="suggested",
            )
        )
        count += 1

    db.commit()
    return count


def _llm_real(
    db: Session,
    project_id: str,
    api_key: str,
    cost_codes: list,
    task_names: list[str],
) -> int:
    from openai import OpenAI

    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
    )
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    count = 0

    for cost_code, cost_code_name in cost_codes:
        prompt = (
            f"Match the construction cost code '{cost_code_name}' to the most likely field tasks.\n"
            f"Available tasks: {json.dumps(task_names)}\n"
            f"Return a JSON array of up to 3 matches:\n"
            f'[{{"task_name": "...", "confidence": 0.0-1.0}}]\n'
            f"Only valid JSON, no explanation."
        )
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        text = resp.choices[0].message.content.strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        matches = json.loads(text)

        for m in matches[:3]:
            if m["task_name"] in task_names:
                db.add(
                    MappingCostcodeTask(
                        project_id=project_id,
                        cost_code=cost_code,
                        task_name=m["task_name"],
                        confidence=round(float(m["confidence"]), 4),
                        method="llm",
                        status="suggested",
                    )
                )
                count += 1

    db.commit()
    return count


def run_matching(db: Session, project_id: str) -> int:
    fuzzy_count = generate_fuzzy_matches(db, project_id)
    llm_count = generate_llm_matches(db, project_id)
    return fuzzy_count + llm_count
