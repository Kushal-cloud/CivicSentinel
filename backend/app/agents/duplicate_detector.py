from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import asin, cos, radians, sin, sqrt
from typing import Optional

import imagehash  # type: ignore
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.complaint import Complaint


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return r * c


def compute_image_phash(pil_image: Image.Image) -> str:
    ph = imagehash.phash(pil_image, hash_size=8)
    return str(ph)


@dataclass
class DuplicateResult:
    duplicate_of_tracking_id: str | None
    confidence: float


async def find_duplicate(
    session: AsyncSession,
    *,
    image_phash_hex: str,
    latitude: float | None,
    longitude: float | None,
    max_hamming_distance: int = 10,
    max_distance_km: float = 0.5,
    lookback_days: int = 30,
) -> DuplicateResult:
    if latitude is None or longitude is None or not image_phash_hex:
        return DuplicateResult(duplicate_of_tracking_id=None, confidence=0.0)

    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    res = await session.execute(
        select(Complaint)
        .where(Complaint.latitude.is_not(None))
        .where(Complaint.longitude.is_not(None))
        .where(Complaint.created_at >= cutoff)
        .order_by(Complaint.created_at.desc())
        .limit(1500)
    )
    candidates = res.scalars().all()
    if not candidates:
        return DuplicateResult(duplicate_of_tracking_id=None, confidence=0.0)

    target_hash = imagehash.hex_to_hash(image_phash_hex)

    best: tuple[str, float] | None = None
    for c in candidates:
        if not c.image_phash:
            continue
        try:
            ch = imagehash.hex_to_hash(c.image_phash)
        except Exception:
            continue
        ham = target_hash - ch  # Hamming distance between hashes
        if ham > max_hamming_distance:
            continue
        dist = _haversine_km(latitude, longitude, c.latitude, c.longitude)
        if dist > max_distance_km:
            continue

        # Confidence: smaller hash distance and smaller geo distance => higher confidence.
        confidence = max(0.0, (max_distance_km - dist) / max_distance_km) * max(0.0, (max_hamming_distance - ham) / max_hamming_distance)
        if best is None or confidence > best[1]:
            best = (c.tracking_id, confidence)

    if best and best[1] > 0.25:
        return DuplicateResult(duplicate_of_tracking_id=best[0], confidence=best[1])
    return DuplicateResult(duplicate_of_tracking_id=None, confidence=0.0)

