import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from db.models import Base
from config import CONFIG


db_path = CONFIG.database.uri.replace('sqlite+aiosqlite:///', '')
folder = os.path.dirname(db_path)
os.makedirs(folder, exist_ok=True)

engine = create_async_engine(CONFIG.database.uri, echo=True)

SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
