import logging
import threading
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel

from category_ai import (
    CategoryClassificationError,
    build_recipe_classification_text,
    classify_categories,
)
from db import repo
from models import Category
from routers.auth import get_current_username


logger = logging.getLogger(__name__)
router = APIRouter()


class ReclassifyJobStatus(BaseModel):
    status: Literal["idle", "running", "completed", "failed"] = "idle"
    total: int = 0
    processed: int = 0
    reclassified: int = 0
    skipped_locked: int = 0
    failed: int = 0


# プロセス内メモリで保持するため uvicorn はシングルワーカー前提
_jobs: dict[str, ReclassifyJobStatus] = {}
_jobs_lock = threading.Lock()


def _update_job(username: str, **fields) -> None:
    with _jobs_lock:
        _jobs[username] = _jobs[username].model_copy(update=fields)


def _run_reclassify(username: str, recipe_ids: list[int]) -> None:
    try:
        categories = repo.list_categories()
        name_to_id = {c.name: c.id for c in categories}
        category_names = [c.name for c in categories]
        reclassified = skipped_locked = failed = 0
        for processed, recipe_id in enumerate(recipe_ids, start=1):
            if repo.is_categories_locked(recipe_id):
                skipped_locked += 1
            elif (recipe := repo.get_by_id(recipe_id)) is not None:
                text = build_recipe_classification_text(
                    recipe.name or "",
                    [ing.name for ing in recipe.ingredients if ing.name],
                    [s.description for s in recipe.steps if s.description],
                )
                try:
                    matched_names = classify_categories(text, category_names)
                    repo.set_recipe_categories(
                        recipe_id, [name_to_id[n] for n in matched_names], source="ai"
                    )
                    reclassified += 1
                except CategoryClassificationError as e:
                    logger.warning("recipe_id=%s のカテゴリ分類に失敗: %s", recipe_id, e)
                    failed += 1
            _update_job(
                username,
                processed=processed,
                reclassified=reclassified,
                skipped_locked=skipped_locked,
                failed=failed,
            )
        _update_job(username, status="completed")
    except Exception:
        logger.exception("username=%s のカテゴリ一括分類ジョブが異常終了", username)
        _update_job(username, status="failed")


@router.get("/api/categories", response_model=list[Category])
def list_categories():
    return repo.list_categories()


@router.post(
    "/api/admin/recipes/reclassify-categories",
    response_model=ReclassifyJobStatus,
    status_code=202,
)
def start_reclassify_all_categories(
    background_tasks: BackgroundTasks, username: str = Depends(get_current_username)
):
    with _jobs_lock:
        current = _jobs.get(username)
        if current is not None and current.status == "running":
            return current
        recipe_ids = repo.list_recipe_ids_by_username(username)
        _jobs[username] = ReclassifyJobStatus(status="running", total=len(recipe_ids))
        job = _jobs[username]
    background_tasks.add_task(_run_reclassify, username, recipe_ids)
    return job


@router.get(
    "/api/admin/recipes/reclassify-categories/status",
    response_model=ReclassifyJobStatus,
)
def get_reclassify_status(username: str = Depends(get_current_username)):
    with _jobs_lock:
        return _jobs.get(username, ReclassifyJobStatus())
