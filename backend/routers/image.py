import io
import os
import pathlib

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image, ImageOps

from db import repo
from routers.auth import get_current_username

UPLOADS_DIR = pathlib.Path(os.environ.get("UPLOADS_DIR", "/app/uploads"))
ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20MB
MAX_IMAGE_LONG_SIDE = 600


router = APIRouter()


@router.post("/api/recipes/{id}/image")
def upload_recipe_image(
    id: int,
    file: UploadFile = File(...),
    username: str = Depends(get_current_username),
):
    recipe = repo.get_by_id(id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    if recipe.username is not None and recipe.username != username:
        raise HTTPException(status_code=403, detail="このレシピを編集する権限がありません")

    if file.content_type not in ALLOWED_IMAGE_MIME_TYPES:
        raise HTTPException(status_code=415, detail="サポートされていない画像形式です")

    try:
        raw = file.file.read()
    except Exception:
        raise HTTPException(status_code=422, detail="画像の読み込みに失敗しました")

    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="ファイルサイズが20MBを超えています")

    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
    except Exception:
        raise HTTPException(status_code=422, detail="画像の読み込みに失敗しました")

    img = ImageOps.exif_transpose(img)

    if img.mode == "RGBA":
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    if max(img.size) > MAX_IMAGE_LONG_SIDE:
        img.thumbnail((MAX_IMAGE_LONG_SIDE, MAX_IMAGE_LONG_SIDE))

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    image_name = f"{id}.jpg"
    img.save(UPLOADS_DIR / image_name, format="JPEG", quality=80)

    repo.set_image_path(id, image_name)
    return {"image_path": image_name}


@router.delete("/api/recipes/{id}/image", status_code=204)
def delete_recipe_image(id: int, username: str = Depends(get_current_username)):
    recipe = repo.get_by_id(id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    if recipe.username is not None and recipe.username != username:
        raise HTTPException(status_code=403, detail="このレシピを編集する権限がありません")

    image_path = UPLOADS_DIR / f"{id}.jpg"
    try:
        os.remove(image_path)
    except FileNotFoundError:
        pass

    repo.set_image_path(id, None)
