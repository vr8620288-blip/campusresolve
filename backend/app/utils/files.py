import os
import uuid

from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings

settings = get_settings()

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "application/pdf": ".pdf",
}

MAX_BYTES = settings.MAX_UPLOAD_MB * 1024 * 1024


def ensure_upload_dir():
    os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)


def save_upload(file: UploadFile) -> tuple[str, int]:
    """Validates and saves an uploaded file. Returns (stored_path, size_bytes)."""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only JPG, PNG and PDF files are allowed.",
        )

    ensure_upload_dir()
    ext = ALLOWED_CONTENT_TYPES[file.content_type]
    stored_name = f"{uuid.uuid4().hex}{ext}"
    stored_path = os.path.join(settings.UPLOAD_DIRECTORY, stored_name)

    size = 0
    with open(stored_path, "wb") as out:
        while chunk := file.file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_BYTES:
                out.close()
                os.remove(stored_path)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File exceeds {settings.MAX_UPLOAD_MB}MB limit.",
                )
            out.write(chunk)

    return stored_path, size
