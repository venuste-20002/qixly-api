import os
from typing import Optional

from fastapi import UploadFile, status

from src.utils.custom_errors import AppError

accepted_image_formats = [
    "image/jpg",
    "image/jpeg",
    "image/png",
]


def save_image(image: Optional[UploadFile]) -> str | None:
    if image is None:
        return None

    image_dir = "images"
    if image.content_type not in accepted_image_formats:
        raise AppError(
            "File format not accepted only images",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    os.makedirs(image_dir, exist_ok=True)
    image_path = os.path.join(image_dir, image.filename)

    with open(image_path, "wb") as f:
        f.write(image.file.read())

    return f"{image.filename}"
