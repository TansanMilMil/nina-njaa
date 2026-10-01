from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from db import repo
from images import ALLOWED_IMAGE_MIME_TYPES, remove_image_file, save_recipe_image
from models import RecipeDetail
from routers.deps import get_editable_recipe

router = APIRouter()


@router.post("/api/recipes/{id}/image")
def upload_recipe_image(
    id: int,
    file: UploadFile = File(...),
    recipe: RecipeDetail = Depends(get_editable_recipe),
):
    if file.content_type not in ALLOWED_IMAGE_MIME_TYPES:
        raise HTTPException(status_code=415, detail="サポートされていない画像形式です")
    try:
        raw = file.file.read()
    except Exception:
        raise HTTPException(status_code=422, detail="画像の読み込みに失敗しました")

    image_name = save_recipe_image(id, raw)
    remove_image_file(recipe.image_path)
    repo.set_image_path(id, image_name)
    return {"image_path": image_name}


@router.delete("/api/recipes/{id}/image", status_code=204)
def delete_recipe_image(id: int, recipe: RecipeDetail = Depends(get_editable_recipe)):
    remove_image_file(recipe.image_path)
    repo.set_image_path(id, None)
