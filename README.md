# CivicSentinel

CivicSentinel is a modular, AI-powered civic intelligence platform that automates the end-to-end lifecycle of civic issue detection, reporting, management, and analytics.

## What you get (MVP)

- Citizen web app to upload an image + optional manual location
- Backend pipeline:
  - image preprocessing
  - vision detection (YOLO, if model is available)
  - EXIF GPS parsing (fallback to manual lat/lon)
  - reverse geocoding (OpenStreetMap/Nominatim)
  - authority mapping (rule-based MVP)
  - NLP complaint generation (transformer-based if available, otherwise templates)
  - duplicate detection (phash + proximity)
  - severity prioritization + recommendations
- User review/confirmation endpoints
- Submission agent adapters (email + stubs for other channels)
- Complaint tracking + status events
- Admin dashboard APIs for analytics

## Run locally (Docker Compose)

1. Copy environment template:
   - `cp .env.example .env`
2. Build and start:
   - `docker compose up --build`
3. Open:
   - Backend: `http://localhost:8000`
   - Frontend: `http://localhost:5173`

## Notes

- Vision (YOLO) and NLP (transformers) are optional at runtime. If the model/runtime is not available, the system falls back to safe defaults so the platform remains functional end-to-end.
- City/ward -> department mapping is rule-based in the MVP. You can replace it with a boundary-based Jurisdiction Mapping Engine when you have authoritative boundary data.

## Admin seeding (MVP)

The backend includes a script to create an admin user for the admin dashboard.

- Run (from `backend/`): `python scripts/seed_admin.py`
- Default credentials (override via env vars):
  - `ADMIN_EMAIL=admin@example.com`
  - `ADMIN_PASSWORD=admin12345`

