from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RecommendationResult:
    recommendations: list[str]
    preventive_actions: list[str]


def recommend(issue_category: str | None, severity_score: float | None = None) -> RecommendationResult:
    key = (issue_category or "").lower()
    sev = float(severity_score or 0.0)

    if "garbage" in key or "waste" in key or "overflow" in key:
        return RecommendationResult(
            recommendations=[
                "Send sanitation team to clear the overflow and restore cleanliness.",
                "Inspect nearby waste accumulation sources and identify illegal dumping points.",
            ],
            preventive_actions=[
                "Increase collection frequency in the affected ward/locality during peak demand days.",
                "Deploy additional bins and signage to reduce overflow risk.",
            ],
        )
    if "streetlight" in key or "electric" in key or "power" in key:
        urgent = sev >= 60
        return RecommendationResult(
            recommendations=[
                "Inspect the streetlight pole, wiring, and control system; repair or replace damaged components.",
                "If there is sparking or exposed wiring, isolate the area and arrange immediate safety checks.",
            ]
            + (["Escalate to emergency electrical safety checks due to high urgency."] if urgent else []),
            preventive_actions=[
                "Perform periodic electrical inspections for similar poles in the vicinity.",
                "Implement protective maintenance schedules for high-failure corridors.",
            ],
        )
    if "water" in key or "leak" in key or "sewer" in key:
        return RecommendationResult(
            recommendations=[
                "Locate the leak source and dispatch repair crew to seal/replace affected sections.",
                "If water contamination risk is suspected, arrange sampling and temporary mitigation.",
            ],
            preventive_actions=[
                "Conduct pressure/condition checks on adjacent pipeline segments.",
                "Update maintenance schedules for recurring leak hotspots.",
            ],
        )
    if "manhole" in key:
        return RecommendationResult(
            recommendations=[
                "Secure the area and arrange immediate inspection of the manhole cover/opening.",
                "Repair/replace the cover and verify proper sealing to prevent hazards.",
            ],
            preventive_actions=[
                "Carry out periodic inspections and cover integrity checks across similar sites.",
                "Install hazard markings for vulnerable points during nighttime.",
            ],
        )
    if "pothole" in key or "road" in key or "damage" in key:
        return RecommendationResult(
            recommendations=[
                "Assess road surface damage and perform patch repair or full surface correction as required.",
                "If visibility is impaired, apply temporary safety measures and signage.",
            ],
            preventive_actions=[
                "Review drainage conditions to reduce recurrence.",
                "Plan preventive resurfacing for corridors with frequent failures.",
            ],
        )

    return RecommendationResult(
        recommendations=[
            "Dispatch a field inspection team to verify the issue and determine corrective actions.",
        ],
        preventive_actions=[
            "Monitor the area for recurrence and update maintenance schedules based on observed failures.",
        ],
    )

