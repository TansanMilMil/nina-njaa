import logging
import threading
from typing import Literal

from fastapi import BackgroundTasks
from pydantic import BaseModel

from category_ai import CategoryClassificationError, classify_recipe
from db import repo

logger = logging.getLogger(__name__)


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


def _run(username: str, recipe_ids: list[int]) -> None:
    try:
        categories = repo.list_categories()
        reclassified = skipped_locked = failed = 0
        for processed, recipe_id in enumerate(recipe_ids, start=1):
            if repo.is_categories_locked(recipe_id):
                skipped_locked += 1
            elif (recipe := repo.get_by_id(recipe_id)) is not None:
                try:
                    repo.set_recipe_categories(recipe_id, classify_recipe(recipe, categories), source="ai")
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


def start(username: str, background_tasks: BackgroundTasks) -> ReclassifyJobStatus:
    """実行中のジョブがあればそれを返し、なければ新規ジョブを開始する。"""
    with _jobs_lock:
        current = _jobs.get(username)
        if current is not None and current.status == "running":
            return current
        recipe_ids = repo.list_recipe_ids_by_username(username)
        job = _jobs[username] = ReclassifyJobStatus(status="running", total=len(recipe_ids))
    background_tasks.add_task(_run, username, recipe_ids)
    return job


def get_status(username: str) -> ReclassifyJobStatus:
    with _jobs_lock:
        return _jobs.get(username, ReclassifyJobStatus())
