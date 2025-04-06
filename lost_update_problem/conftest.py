import pytest_asyncio

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.ext.asyncio.session import AsyncSession

from .models import Base

# MySQL 연결 설정
DATABASE_URL = "mysql+aiomysql://root:root@localhost:3306/sql_tunning"


@pytest_asyncio.fixture()
async def async_engine():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture()
async def async_session(
    async_engine,
) -> AsyncGenerator[AsyncSession, None]:
    session = async_sessionmaker(async_engine, expire_on_commit=False)
    yield session
