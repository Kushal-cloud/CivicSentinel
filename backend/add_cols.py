import asyncio
from app.core.db import engine
from sqlalchemy import text

async def alter():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE complaints ADD COLUMN IF NOT EXISTS upvotes INTEGER DEFAULT 0;"))
            print("Added upvotes")
        except Exception as e: print(e)
        try:
            await conn.execute(text("ALTER TABLE complaints ADD COLUMN IF NOT EXISTS resolved_image_path TEXT;"))
            print("Added resolved_image_path")
        except Exception as e: print(e)
        try:
            await conn.execute(text("ALTER TABLE complaints ADD COLUMN IF NOT EXISTS follow_up_count INTEGER DEFAULT 0;"))
            print("Added follow_up_count")
        except Exception as e: print(e)

if __name__ == "__main__":
    asyncio.run(alter())
