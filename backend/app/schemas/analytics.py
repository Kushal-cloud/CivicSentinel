from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class AnalyticsSummary(BaseModel):
    total_complaints: int
    by_status: dict[str, int]
    by_issue_category: dict[str, int]
    by_department: dict[str, int]
    severity_average: float | None = None
    resolution_times_minutes_p50: float | None = None
    resolution_times_minutes_p90: float | None = None


class HeatmapCell(BaseModel):
    lat_bin: float
    lon_bin: float
    count: int


class AnalyticsHeatmap(BaseModel):
    grid_size_degrees: float = 0.05
    cells: list[HeatmapCell]


class PredictiveRiskZone(BaseModel):
    ward: str | None = None
    grid_key: str
    risk_score: float
    recent_count: int
    previous_count: int


class PredictiveAnalyticsOut(BaseModel):
    zones: list[PredictiveRiskZone]

