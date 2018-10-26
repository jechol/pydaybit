import asyncio
import logging

import pytest

from pydaybit import Daybit
from pydaybit import daybit_url, DAYBIT_API_DEFAULT_URL
from pydaybit.exceptions import CommunicationError

logger = logging.getLogger('pydaybit')
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(stream_handler)


@pytest.mark.skipif(daybit_url() == DAYBIT_API_DEFAULT_URL, reason='Test must be under controlled.')
class TestAPI:
    @pytest.mark.asyncio
    async def test_without_context_manager(self, daybit_params, event_loop):
        daybit = Daybit(daybit_params['url'], params=daybit_params['params'], loop=event_loop)
        await daybit.connect()
        await daybit.disconnect()

    @pytest.mark.asyncio
    async def test_api_join(self, daybit_params, event_loop):
        async with Daybit(daybit_params['url'], params=daybit_params['params'], loop=event_loop) as daybit:
            async with daybit.channel('/api'):
                asyncio.sleep(0.1, loop=event_loop)

    @pytest.mark.asyncio
    async def test_api_key_denied(self, daybit_params, event_loop):
        with pytest.raises(ConnectionError):
            async with Daybit(daybit_params['url'], params={'api_key': 'THIS-IS-INVALID-KEY',
                                                            'api_secret': 'THIS-IS-INVALID-SECRET-KEY'},
                              loop=event_loop) as daybit:
                async with daybit.channel('/api'):
                    asyncio.sleep(0.1, loop=event_loop)

    @pytest.mark.asyncio
    async def test_subscription_catch_exception(self, daybit_params, event_loop):
        async with Daybit(daybit_params['url'], params=daybit_params['params'], loop=event_loop) as daybit:
            with pytest.raises(CommunicationError):
                await (daybit.market_summaries / -1)()

    @pytest.mark.asyncio
    async def test_api_request_not_existed_coin_symbol(self, daybit_params, event_loop):
        async with Daybit(daybit_params['url'], params=daybit_params['params'], loop=event_loop) as daybit:
            with pytest.raises(CommunicationError):
                await (daybit.coin_prices / 'unexisted')()

    @pytest.mark.asyncio
    async def test_rate_limit(self, daybit_params, event_loop):
        async with Daybit(daybit_params['url'], params=daybit_params['params'], loop=event_loop) as daybit:
            market_summary_intvls = list((await daybit.market_summary_intvls()).values())
            if len(market_summary_intvls) >= 2:
                intv1 = market_summary_intvls[0]['seconds']
                intv2 = market_summary_intvls[1]['seconds']
                rate_limit = daybit.rate_limit.get_limit('market_summaries')

                for _ in range(rate_limit):
                    await (daybit.market_summaries / intv1)()
                    await (daybit.market_summaries / intv2)()
                    await asyncio.sleep(1 / rate_limit + 0.05)

    @pytest.mark.skip(reason="Not implemented")
    async def test_timeout_propagation(self):
        pass
