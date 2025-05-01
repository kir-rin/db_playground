from typing import AsyncGenerator
import pytest
import asyncio

import backoff
from sqlalchemy.ext.asyncio.session import AsyncSession

from lost_update_problem.models import Account, AccountWithVersion


# Note:
#   동시성 문제를 해결하기 위해서는 낙관적 락, 비관적 락, 분산 락등을 사용한다.
#   그 중의 분산 락은 TTL로 인해 락이 해제되고 나서, 커밋되는 경우 갱신 분실 문제가 일어날 수 있기 때문에
#   낙관적 락을 같이 사용할 수 있다.
#   cf. https://haon.blog/article/toss-slash/broker-issue-concurrency-and-network-latency/#%EB%B6%84%EC%82%B0-%EB%9D%BD-%ED%83%80%EC%9E%84%EC%95%84%EC%9B%83-%EC%84%A4%EC%A0%95%EA%B3%BC-%EA%B7%B8%EC%97%90-%EB%94%B0%EB%A5%B8-%EA%B0%B1%EC%8B%A4%EB%AC%B8%EC%A0%9C
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


@pytest.mark.asyncio()
async def test_resolve_lost_update_with_pessimistic_lock(async_session: AsyncGenerator[AsyncSession, None]):
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
                account = await session.get_one(Account, ident=id, with_for_update=True)
                account.balance += diff
                await session.commit()

    coro_list = [update_balance(id=1, diff=-1) for _ in range(10)]

    await asyncio.gather(*coro_list)
    async with async_session() as session:
        session: AsyncSession
        async with session.begin():
            account = await session.get_one(Account, ident=1)
            assert account.balance == 0


@pytest.mark.asyncio()
async def test_resolve_lost_update_with_optimistic_lock(async_session: AsyncGenerator[AsyncSession, None]):
    async with async_session() as session:
        session: AsyncSession
        async with session.begin():
            session.add(AccountWithVersion(id=1, balance=10))
            account = await session.get_one(AccountWithVersion, ident=1)
    assert account.balance == 10

    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    async def update_balance(id: int, diff: int):
        async with async_session() as session:
            session: AsyncSession
            async with session.begin():
                account = await session.get_one(AccountWithVersion, ident=id)
                account.balance += diff
                await session.commit()

    coro_list = [update_balance(id=1, diff=-1) for _ in range(10)]

    await asyncio.gather(*coro_list)
    async with async_session() as session:
        session: AsyncSession
        async with session.begin():
            account = await session.get_one(AccountWithVersion, ident=1)
            assert account.balance == 0
