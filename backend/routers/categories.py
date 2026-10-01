from fastapi import APIRouter, BackgroundTasks, Depends

import reclassify_job
from db import repo
from models import Category
from reclassify_job import ReclassifyJobStatus
from routers.auth import get_current_username

router = APIRouter()


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
    return reclassify_job.start(username, background_tasks)


@router.get(
    "/api/admin/recipes/reclassify-categories/status",
    response_model=ReclassifyJobStatus,
)
def get_reclassify_status(username: str = Depends(get_current_username)):
    return reclassify_job.get_status(username)
