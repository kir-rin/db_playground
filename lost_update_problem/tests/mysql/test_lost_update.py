from typing import AsyncGenerator
import pytest
import asyncio

from sqlalchemy.ext.asyncio.session import AsyncSession

from lost_update_problem.models import Account


@pytest.mark.asyncio()
async def test_lost_update(async_session: AsyncGenerator[AsyncSession, None]):
    async with async_session() as session:
        session: AsyncSession
        async with session.begin():
            session.add(Account(id=1, balance=10))
            account = await session.get_one(Account, ident=1)
    assert account.balance == 10

    async def update_balance(id: int, diff: int):
        async with async_session() as session:
            session: AsyncSession
            async with session.begin():
                account = await session.get_one(Account, ident=id)
                account.balance += diff
                await session.commit()

    coro_list = [update_balance(id=1, diff=-1) for _ in range(10)]

    await asyncio.gather(*coro_list)
    async with async_session() as session:
        session: AsyncSession
        async with session.begin():
            account = await session.get_one(Account, ident=1)
            assert account.balance != 0
