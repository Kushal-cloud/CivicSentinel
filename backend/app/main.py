from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.analytics import router as analytics_router
from app.api.routes.admin import router as admin_router
from app.api.routes.complaints import router as complaints_router
from app.api.routes.auth import router as auth_router
from app.core.db import engine
from app.models import Complaint, ComplaintEvent, User  # noqa: F401


app = FastAPI(title="CivicSentinel API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    # Frontend uses `Authorization: Bearer ...` headers (no cookies),
    # so we can safely disable credentials to avoid wildcard+credentials CORS blocks.
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(complaints_router)
app.include_router(admin_router)
app.include_router(analytics_router)


@app.on_event("startup")
async def _startup() -> None:
    # Create tables for MVP. For production, use Alembic migrations.
    from app.core.db import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Start SLA escalation scheduler.
    from app.services.escalation_service import start_escalation_scheduler

    start_escalation_scheduler()

