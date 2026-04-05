from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from app.core.config import settings

@dataclass
class DetectionResult:
    issue_category: str
    detected_issues: list[dict[str, Any]]
    raw_model_available: bool

def _dummy_detection() -> list[dict[str, Any]]:
    return [
        {
            "class_name": "unknown_hazard",
            "bbox_xyxy": [100, 100, 200, 200],
            "confidence": 0.12,
            "description": "System defaulted to dummy detection because Gemini API key is not configured.",
        }
    ]

def detect_issues(pil_image, *, image_bytes: bytes | None = None) -> DetectionResult:
    if not settings.gemini_api_key or not image_bytes:
        detected_issues = _dummy_detection()
        return DetectionResult(
            issue_category="unknown_hazard",
            detected_issues=detected_issues,
            raw_model_available=False,
        )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.gemini_api_key)
        prompt = (
            "Analyze the image and identify the primary civic infrastructure issue. "
            "Choose a category closest to: pothole, broken_streetlight, garbage_dump, water_leak, "
            "vandalism, overgrown_vegetation, structural_damage, or other. "
            "Respond strictly in JSON format with three keys: "
            "1. 'category' (string), "
            "2. 'confidence' (float between 0 and 1 representing your certainty), "
            "3. 'description' (a brief 1-sentence visible description of the problem)."
        )

        response = client.models.generate_content(
            model='gemini-2.0-flash-lite',
            contents=[prompt, types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg')],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        
        data = json.loads(response.text)
        category = data.get("category", "other").lower().replace(" ", "_")
        conf = float(data.get("confidence", 0.5))
        desc = data.get("description", "")

        detected = [{
            "class_name": category,
            "confidence": conf,
            "description": desc,
            "bbox_xyxy": [0,0,0,0], # BBoxes are omitted for Gemini prompt MVP
        }]

        return DetectionResult(
            issue_category=category,
            detected_issues=detected,
            raw_model_available=True
        )

    except Exception as e:
        print(f"Gemini Vision Error: {e}")
        return DetectionResult(
            issue_category="unknown_hazard",
            detected_issues=_dummy_detection(),
            raw_model_available=False,
        )

