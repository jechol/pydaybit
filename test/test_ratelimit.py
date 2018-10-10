import asyncio

import pytest
from async_timeout import timeout as atimeout

from pydaybit.ratelimit import RateLimit


@pytest.mark.asyncio
async def test_in_limit(event_loop):
    rl = RateLimit(loop=event_loop)
    rl.add_limit('get_server_time', 10)

    async with atimeout(0.9, loop=event_loop):
        for i in range(10):
            await rl.wait('get_server_time')


@pytest.mark.asyncio
async def test_over_limit(event_loop):
    rl = RateLimit(loop=event_loop)
    rl.add_limit('get_server_time', 10)

    with pytest.raises(asyncio.TimeoutError):
        async with atimeout(1, loop=event_loop):
            for i in range(11):
                await rl.wait('get_server_time')
