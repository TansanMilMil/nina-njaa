from fastapi import APIRouter, Depends, HTTPException

from db import repo
from models import CookedLogCreate, CookedLogEntry, CookedLogRawEntry
from routers.auth import get_current_username

router = APIRouter()


@router.post("/api/cooked-logs/{recipe_id}", status_code=204)
def add_cooked_log(
    recipe_id: int,
    log_data: CookedLogCreate,
    username: str = Depends(get_current_username),
):
    if repo.get_by_id(recipe_id) is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    repo.add_cooked_log(username, recipe_id, log_data.memo)


@router.get("/api/cooked-logs", response_model=list[CookedLogEntry])
def get_cooked_logs(username: str = Depends(get_current_username)):
    return repo.get_cooked_logs(username)


@router.get("/api/cooked-logs/{recipe_id}", response_model=CookedLogEntry | None)
def get_cooked_log_for_recipe(recipe_id: int, username: str = Depends(get_current_username)):
    return repo.get_cooked_log_for_recipe(username, recipe_id)


@router.get(
    "/api/cooked-logs/{recipe_id}/entries", response_model=list[CookedLogRawEntry]
)
def get_cooked_log_entries(recipe_id: int, username: str = Depends(get_current_username)):
    return repo.get_cooked_log_entries(username, recipe_id)


@router.delete("/api/cooked-logs/{recipe_id}/entries/{entry_id}", status_code=204)
def delete_cooked_log_entry(
    recipe_id: int, entry_id: int, username: str = Depends(get_current_username)
):
    if not repo.delete_cooked_log_entry(username, recipe_id, entry_id):
        raise HTTPException(status_code=404, detail="Cooked log entry not found")


@router.put("/api/cooked-logs/{recipe_id}/entries/{entry_id}", status_code=204)
def update_cooked_log_entry(
    recipe_id: int,
    entry_id: int,
    log_data: CookedLogCreate,
    username: str = Depends(get_current_username),
):
    if not repo.update_cooked_log_entry(username, recipe_id, entry_id, log_data.memo):
        raise HTTPException(status_code=404, detail="Cooked log entry not found")
