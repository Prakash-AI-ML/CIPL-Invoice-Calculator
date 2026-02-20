import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.config import engine, AsyncSessionLocal  # Assuming this import path

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:  # No bind=engine needed
        try:
            yield session
            await session.commit()  # Only if writes occurred; optional for reads
        except Exception:
            await session.rollback()
            raise
        finally:
            await asyncio.shield(session.close())  # Shields from cancellation