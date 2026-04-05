import asyncio
import os

from sqlalchemy import select

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User


async def main() -> None:
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin12345")
    admin_name = os.getenv("ADMIN_NAME", "CivicSentinel Admin")
    admin_phone = os.getenv("ADMIN_PHONE", "")

    async with AsyncSessionLocal() as session:
        res = await session.execute(select(User).where(User.email == admin_email))
        existing = res.scalar_one_or_none()
        if existing:
            print("Admin already exists.")
            return

        user = User(
            email=admin_email,
            password_hash=hash_password(admin_password),
            name=admin_name,
            phone=admin_phone or None,
            role=UserRole.admin,
        )
        session.add(user)
        await session.commit()
        print("Admin seeded:", admin_email)


if __name__ == "__main__":
    asyncio.run(main())

