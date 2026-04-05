from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AuthorityMappingResult:
    department_name: str | None
    mapped_issue_category: str | None


def map_department(issue_category: str | None, *, detected_issues: list[dict] | None = None) -> AuthorityMappingResult:
    if not issue_category:
        return AuthorityMappingResult(department_name=None, mapped_issue_category=None)

    normalized = issue_category.lower().strip().replace("-", "_").replace(" ", "_")
    # Rule-based MVP mapping. Replace with boundary-aware Jurisdiction Mapping Engine later.
    road_keywords = {"pothole", "damaged_road", "road_damage", "crack", "street"}
    garbage_keywords = {"garbage", "overflow", "waste", "dump", "illegal_dumping"}
    electricity_keywords = {"streetlight", "lamp", "light_out", "power", "electrical"}
    water_keywords = {"water_leak", "leak", "water", "sewer", "pipeline"}
    manhole_keywords = {"manhole", "open_manho", "open_man e", "man_hole"}  # tolerant

    def contains_any(keywords: set[str]) -> bool:
        return any(k in normalized for k in keywords) or normalized in keywords

    if contains_any(garbage_keywords):
        return AuthorityMappingResult(department_name="Sanitation & Solid Waste", mapped_issue_category="garbage_overflow")
    if contains_any(electricity_keywords):
        return AuthorityMappingResult(department_name="Electricity & Street Lighting", mapped_issue_category="broken_streetlight")
    if contains_any(water_keywords):
        return AuthorityMappingResult(department_name="Water Supply & Sewerage", mapped_issue_category="water_leakage")
    if contains_any(manhole_keywords) or "manhole" in normalized:
        # Many cities route open manholes to sanitation/road safety; choose sanitation in MVP.
        return AuthorityMappingResult(department_name="Sanitation & Solid Waste", mapped_issue_category="open_manhole")
    if contains_any(road_keywords) or "pothole" in normalized or "road" in normalized:
        return AuthorityMappingResult(department_name="Road Maintenance", mapped_issue_category="damaged_road")

    # Default bucket
    return AuthorityMappingResult(department_name="Public Works (General)", mapped_issue_category=normalized)

