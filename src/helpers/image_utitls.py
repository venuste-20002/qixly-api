import os
from fastapi import UploadFile

def save_image(image: UploadFile) -> str:
    if not image:
        return None

    image_dir = "images"
    os.makedirs(image_dir, exist_ok=True)
    image_path = os.path.join(image_dir, image.filename)

    with open(image_path, "wb") as f:
        f.write(image.file.read())

    return f"/images/{image.filename}"