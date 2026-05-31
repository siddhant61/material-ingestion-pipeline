import os
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, Float, DateTime, JSON

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db") # Use a real DB in prod

Base = declarative_base()

class PipelineRun(Base):
    __tablename__ = "pipeline_runs"
    pipeline_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    material_id = Column(String, nullable=False)
    status = Column(String, default="pending")
    progress = Column(Float, default=0.0)
    report_url = Column(String, nullable=True)
    error_details = Column(String, nullable=True)
    config = Column(JSON, default={})
    start_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    end_time = Column(DateTime(timezone=True), nullable=True)

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
