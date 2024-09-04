import re
from puremagic import from_string
from PIL.Image import Resampling
from fastapi import HTTPException
from PIL import Image
from io import BytesIO


def validate_file(contents: bytes, max_size: int, supported_file_types: dict):
    file_size = len(contents)
    if not(0 < file_size <= max_size):
        raise HTTPException(status_code=400, detail="File size is not between 0 and 1 MB!")

    file_type = from_string(contents, mime=True)
    if file_type not in supported_file_types:
        raise HTTPException(status_code=400, detail="Supported file types are {}".format(supported_file_types))

    return file_type


def find_nearest_size(sizes, width, height):
    # Находит ближайший допустимый размер для заданных ширины и высоты.
    distances = [(abs(w - width) + abs(h - height), (w, h)) for w, h in sizes]
    return min(distances)[1]


def resize_image(image_bytes: bytes, file_type: str, sizes: tuple) -> bytes:
    with Image.open(BytesIO(image_bytes)) as img:
        width, height = img.size
        nearest_size = find_nearest_size(sizes, width, height)
        img = img.resize(nearest_size, Resampling.LANCZOS)
        output = BytesIO()
        img.save(output, format=file_type.upper().split('/')[-1])
        return output.getvalue()
