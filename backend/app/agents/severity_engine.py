from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any


@dataclass
class SeverityResult:
    severity_score: float
    priority: int
    risk_notes: list[str]


def _class_weight(issue_category: str | None) -> float:
    if not issue_category:
        return 0.6
    key = issue_category.lower()
    if "open_manhole" in key or "manhole" in key:
        return 1.3
    if "electric" in key or "streetlight" in key or "power" in key:
        return 1.1
    if "water_leak" in key or "water" in key or "leak" in key:
        return 1.0
    if "garbage" in key or "overflow" in key or "waste" in key:
        return 0.8
    if "pothole" in key or "road" in key or "damage" in key:
        return 1.1
    return 0.7


def estimate_severity(
    *,
    issue_category: str | None,
    detected_issues: list[dict[str, Any]] | None,
    risk_factor: float = 1.0,
) -> SeverityResult:
    detected_issues = detected_issues or []

    target_size = 640
    max_area_fraction = 0.0
    max_conf = 0.0
    for d in detected_issues:
        bbox = d.get("bbox_xyxy") or []
        if len(bbox) != 4:
            continue
        x1, y1, x2, y2 = [float(v) for v in bbox]
        area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
        area_fraction = area / float(target_size * target_size)
        conf = float(d.get("confidence") or 0.0)
        max_area_fraction = max(max_area_fraction, area_fraction)
        max_conf = max(max_conf, conf)

    base = 30.0 * _class_weight(issue_category) * risk_factor
    coverage = 70.0 * (sqrt(max_area_fraction) if max_area_fraction > 0 else 0.0)
    confidence_term = 15.0 * max_conf
    severity = base * 0.4 + coverage * 0.4 + confidence_term * 0.2
    severity = max(0.0, min(100.0, severity))

    # Map to priority (1 = highest).
    if severity >= 80:
        priority = 1
    elif severity >= 60:
        priority = 2
    elif severity >= 40:
        priority = 3
    elif severity >= 20:
        priority = 4
    else:
        priority = 5

    notes = []
    if max_area_fraction >= 0.1:
        notes.append("High visible coverage")
    if max_conf >= 0.6:
        notes.append("High model confidence")
    if risk_factor >= 1.3:
        notes.append("Elevated ward risk factor")

    return SeverityResult(severity_score=round(severity, 2), priority=priority, risk_notes=notes)

