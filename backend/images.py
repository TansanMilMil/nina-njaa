import io
import os
import pathlib
import uuid

from fastapi import HTTPException
from PIL import Image, ImageOps

UPLOADS_DIR = pathlib.Path(os.environ.get("UPLOADS_DIR", "/app/uploads"))
ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20MB
MAX_IMAGE_LONG_SIDE = 600


def _to_rgb(img: Image.Image) -> Image.Image:
    if img.mode == "RGBA":
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        return background
    if img.mode != "RGB":
        return img.convert("RGB")
    return img


def _decode_image(raw: bytes) -> Image.Image:
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="ファイルサイズが20MBを超えています")
    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
    except Exception:
        raise HTTPException(status_code=422, detail="画像の読み込みに失敗しました")
    img = _to_rgb(ImageOps.exif_transpose(img))
    if max(img.size) > MAX_IMAGE_LONG_SIDE:
        img.thumbnail((MAX_IMAGE_LONG_SIDE, MAX_IMAGE_LONG_SIDE))
    return img


def save_recipe_image(recipe_id: int, raw: bytes) -> str:
    img = _decode_image(raw)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    image_name = f"{recipe_id}-{uuid.uuid4().hex[:8]}.jpg"
    img.save(UPLOADS_DIR / image_name, format="JPEG", quality=80)
    return image_name


def remove_image_file(image_path: str | None) -> None:
    # ファイル名にuuidを含めているためパスを推測構築せずDBの値を使う。
    # (コミットe00c13a以前は{id}.jpg固定だったため、uuidなしの{id}.jpg形式のファイルも存在しうる)
    if image_path is None:
        return
    try:
        (UPLOADS_DIR / image_path).unlink()
    except FileNotFoundError:
        pass
