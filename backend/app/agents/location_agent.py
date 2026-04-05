from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Any

import requests

from app.core.config import settings


@dataclass
class LocationResult:
    latitude: float | None
    longitude: float | None
    ward: str | None
    locality: str | None
    jurisdiction: str | None
    raw: dict[str, Any] | None = None


def _rational_to_float(r) -> float:
    # exifread uses Ratio-like objects with .num/.den or tuple-ish behavior.
    if hasattr(r, "num") and hasattr(r, "den"):
        return float(r.num) / float(r.den) if float(r.den) != 0 else 0.0
    try:
        s = str(r)
        if "/" in s:
            a, b = s.split("/", 1)
            return float(a) / float(b)
        return float(s)
    except Exception:
        return float("nan")


def extract_exif_gps_from_bytes(image_bytes: bytes) -> tuple[float | None, float | None]:
    try:
        import exifread  # type: ignore

        f = io.BytesIO(image_bytes)
        tags = exifread.process_file(f, details=False)
        lat_tag = tags.get("GPSLatitude")
        lon_tag = tags.get("GPSLongitude")
        if not lat_tag or not lon_tag:
            return None, None

        lat_vals = [_rational_to_float(v) for v in lat_tag.values]
        lon_vals = [_rational_to_float(v) for v in lon_tag.values]

        lat_deg = lat_vals[0]
        lat_min = lat_vals[1]
        lat_sec = lat_vals[2]
        lat = lat_deg + (lat_min / 60.0) + (lat_sec / 3600.0)

        lon_deg = lon_vals[0]
        lon_min = lon_vals[1]
        lon_sec = lon_vals[2]
        lon = lon_deg + (lon_min / 60.0) + (lon_sec / 3600.0)

        # Hemisphere
        lat_ref = tags.get("GPSLatitudeRef")
        lon_ref = tags.get("GPSLongitudeRef")
        if lat_ref and str(lat_ref).upper().startswith("S"):
            lat = -lat
        if lon_ref and str(lon_ref).upper().startswith("W"):
            lon = -lon

        if any(map(lambda x: x is None or x != x, [lat, lon])):  # NaN check
            return None, None
        return float(lat), float(lon)
    except Exception:
        return None, None


def reverse_geocode(lat: float, lon: float) -> dict[str, Any] | None:
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "format": "jsonv2",
            "lat": lat,
            "lon": lon,
            "zoom": 15,
            "addressdetails": 1,
        }
        headers = {"User-Agent": settings.osm_user_agent}
        resp = requests.get(url, params=params, headers=headers, timeout=20)
        if resp.status_code != 200:
            return None
        return resp.json()
    except Exception:
        return None


def detect_location(
    *,
    image_bytes: bytes | None,
    manual_lat: float | None,
    manual_lon: float | None,
) -> LocationResult:
    lat = manual_lat
    lon = manual_lon
    if (lat is None or lon is None) and image_bytes:
        ex_lat, ex_lon = extract_exif_gps_from_bytes(image_bytes)
        lat = lat if lat is not None else ex_lat
        lon = lon if lon is not None else ex_lon

    if lat is None or lon is None:
        return LocationResult(latitude=None, longitude=None, ward=None, locality=None, jurisdiction=None, raw=None)

    data = reverse_geocode(lat, lon)
    if not data:
        return LocationResult(latitude=lat, longitude=lon, ward=None, locality=None, jurisdiction=None, raw=None)

    addr = data.get("address", {}) if isinstance(data, dict) else {}
    ward = (
        addr.get("city_district")
        or addr.get("suburb")
        or addr.get("neighbourhood")
        or addr.get("borough")
    )
    locality = addr.get("locality") or addr.get("town") or addr.get("village") or addr.get("city")
    jurisdiction = addr.get("state") or addr.get("county") or addr.get("region") or addr.get("country")

    return LocationResult(
        latitude=lat,
        longitude=lon,
        ward=ward,
        locality=locality,
        jurisdiction=jurisdiction,
        raw=data,
    )

