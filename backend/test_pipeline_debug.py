import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.agents.pipeline import run_pipeline

async def test():
    engine = create_async_engine(settings.database_url, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
    print("Reading image...")
    with open("test.jpg", "rb") as f:
        img = f.read()
    
    async with SessionLocal() as session:
        print("Running pipeline...")
        try:
            out = await run_pipeline(
                session, tracking_id="TEST-12", image_path="test_image.jpg", image_bytes=img,
                reporter_user_id='37cd8c41-d1f1-4f5c-b8f3-e25f9c1aa94c', reporter_name="U", language="en", tone="formal",
                manual_lat=28.0, manual_lon=77.0, manual_ward="W", manual_locality="L", citizen_description="D"
            )
            print("PIPELINE SUCCESS")
        except Exception as e:
            print("PIPELINE ERROR:")
            import traceback; traceback.print_exc()

asyncio.run(test())
