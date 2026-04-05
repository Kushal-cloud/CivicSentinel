from __future__ import annotations

import io
import re
from typing import Any

import numpy as np
from PIL import Image, ImageFilter


ALLOWED_MIME_SUBSTRINGS = {
    "jpeg": [".jpg", ".jpeg"],
    "png": [".png"],
}


def _looks_like_image(filename: str) -> bool:
    lower = filename.lower()
    return any(lower.endswith(ext) for exts in ALLOWED_MIME_SUBSTRINGS.values() for ext in exts)


def validate_image_bytes(image_bytes: bytes, *, filename: str) -> None:
    # Basic validation: non-empty and decodable.
    if not image_bytes or len(image_bytes) < 50:
        raise ValueError("Invalid image data")
    if not _looks_like_image(filename):
        # We still try to decode; if it fails we reject.
        pass
    try:
        Image.open(io.BytesIO(image_bytes)).verify()
    except Exception as e:
        raise ValueError("Invalid or unsupported image format") from e


def preprocess_image_for_detection(image_bytes: bytes, *, target_size: int = 640) -> dict[str, Any]:
    """
    Returns:
      - pil_image: RGB PIL image (preprocessed)
      - np_image_float: float32 normalized array (H,W,3) in [0,1]
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # Resize with aspect ratio preservation.
    w, h = img.size
    scale = min(target_size / max(w, 1), target_size / max(h, 1))
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    img = img.resize((new_w, new_h), resample=Image.BILINEAR)

    # Pad to target square (letterbox style).
    canvas = Image.new("RGB", (target_size, target_size), (0, 0, 0))
    pad_x = (target_size - new_w) // 2
    pad_y = (target_size - new_h) // 2
    canvas.paste(img, (pad_x, pad_y))

    # Noise reduction (cheap, model-agnostic).
    canvas = canvas.filter(ImageFilter.MedianFilter(size=3))

    np_img = np.asarray(canvas, dtype=np.float32) / 255.0
    return {"pil_image": canvas, "np_image_float": np_img}

