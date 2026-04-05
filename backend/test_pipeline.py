import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.agents.pipeline import run_pipeline

async def test():
    engine = create_async_engine(settings.database_url, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
    async with SessionLocal() as session:
        try:
            out = await run_pipeline(
                session,
                tracking_id="TEST-1234",
                image_path="test_image.jpg",
                image_bytes=b"dummy",
                reporter_user_id=1,
                reporter_name="Test User",
                language="en",
                tone="formal",
                manual_lat=28.0,
                manual_lon=77.0,
                manual_ward="Ward",
                manual_locality="Locality",
                citizen_description="Test desc"
            )
            print("PIPELINE SUCCESS")
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
