import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.core.config import settings

async def main():
    engine = create_async_engine(settings.database_url, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
    async with SessionLocal() as db:
        res = await db.execute(text("SELECT id, email FROM users LIMIT 1"))
        user = res.fetchone()
        from jose import jwt
        from datetime import datetime, timedelta
        expire = datetime.utcnow() + timedelta(minutes=1440)
        to_encode = {"sub": str(user[0]), "exp": expire}
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm="HS256")
        print("TOKEN:", encoded_jwt)

asyncio.run(main())
