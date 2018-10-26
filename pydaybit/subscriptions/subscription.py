import asyncio
import re
import time

from pydaybit.daybit_channels import DaybitChannel
from pydaybit.exceptions import PrimaryKeyError
from pydaybit.utility import optional


class Subscription(DaybitChannel):
    def __init__(self, socket, topic, params=None, max_queue=2 ** 5, timeout_secs=3, primary_key='id'):
        super().__init__(socket, topic, params, max_queue, timeout_secs=timeout_secs)
        self.loop = None
        self.primary_key = primary_key
        self.subtopic = re.search(r"/subscription:([^;]*)(;.*)?", topic).group(1)
        self.updated_timestamp = None

    def __truediv__(self, other):
        return self.socket.channel(';'.join([self.topic, str(other)]),
                                   channel_t=type(self))

    async def join(self, payload=None):
        return await super().join(payload)

    def update(self, response):
        response = response[0]
        if 'action' not in response:
            return

        action = response['action']
        new_data = response.get('data', [{}])
        self.updated_timestamp = self.socket.estimated_timestamp()

        assert action in ['init', 'insert', 'update', 'upsert', 'delete']

        if action == 'init':
            self.data = {}

        if isinstance(self.primary_key, tuple):
            primary_key = '-'.join(self.primary_key)
        else:
            primary_key = self.primary_key

        try:
            if isinstance(self.primary_key, tuple):
                if len(new_data) == 0:
                    pass
                elif set(self.primary_key) <= set(new_data[0].keys()):
                    for row in new_data:
                        key = '-'.join(str(row[key]) for key in self.primary_key)
                        self._update_single_row(action, key, row)
                else:
                    raise NotImplementedError
            elif primary_key is None:
                self.data = new_data
            else:
                primary_key = self.primary_key
                for row in new_data:
                    self._update_single_row(action, row[self.primary_key], row)

        except KeyError:
            raise PrimaryKeyError('primary-key({}) is missing in the received data: {}'.format(primary_key, new_data))

    def _update_single_row(self, action, key, value):
        if action == 'delete':
            self.data.pop(key, None)
        else:
            writable = False
            if action == 'init':
                writable = True
            elif action == 'update':
                if key in self.data:
                    writable = True
            elif action == 'insert':
                if key not in self.data:
                    writable = True
            elif action == 'upsert':
                writable = True

            if writable:
                self.data[key] = value

    def reset_data(self):
        self.data = {}
        self.updated_timestamp = None

    async def __call__(self, *args, **kwargs):
        if self.loop is None:
            self.subscribe(*args, **kwargs)
            return await self.wait()
        if self.updated_timestamp is None:
            await self.request(**kwargs)
        return self.data

    def subscribe(self, *args, **kwargs):
        if self.loop is None:
            self.loop = asyncio.ensure_future(self._loop(*args, **kwargs), loop=self.socket.loop)

    async def _loop(self, *args, **kwargs):
        if 'callback_future' in kwargs:
            self.callback_future = kwargs['callback_future']

        try:
            await self.join()
            await self.request(*args, **kwargs)
            while True:
                await self.receive()
        except Exception as e:
            if self.callback_future is not None:
                self.callback_future.set_exception(e)
                self.callback_future = None
        finally:
            await self.leave()

    async def leave(self, wait_response=True):
        if self.loop is not None:
            self.loop.cancel()
            self.loop = None
        await super().leave(wait_response)


class Coins(Subscription):
    def __init__(self, socket, topic, *args, **kwargs):
        super().__init__(socket, topic,
                         primary_key='sym',
                         *args, **kwargs)


class CoinPrices(Subscription):
    def __init__(self, socket, topic, *args, **kwargs):
        super().__init__(socket, topic,
                         primary_key='sym',
                         *args, **kwargs)


class QuoteCoins(Subscription):
    def __init__(self, socket, topic, *args, **kwargs):
        super().__init__(socket, topic,
                         primary_key='sym',
                         *args, **kwargs)


class Markets(Subscription):
    def __init__(self, socket, topic, *args, **kwargs):
        super().__init__(socket, topic,
                         primary_key=('quote', 'base'),
                         *args, **kwargs)


class MarketSummaryIntervals(Subscription):
    def __init__(self, socket, topic, *args, **kwargs):
        super().__init__(socket, topic,
                         primary_key='seconds',
                         *args, **kwargs)


class MarketSummaries(Subscription):
    def __init__(self, socket, topic, *args, **kwargs):
        super().__init__(socket, topic,
                         primary_key=('quote', 'base'),
                         *args, **kwargs)


class OrderBooks(Subscription):
    def __init__(self, socket, topic, *args, **kwargs):
        super().__init__(socket, topic,
                         primary_key=('min_price', 'max_price'),
                         *args, **kwargs)


class PriceHistoryIntervals(Subscription):
    def __init__(self, socket, topic, *args, **kwargs):
        super().__init__(socket, topic,
                         primary_key='seconds',
                         *args, **kwargs)


class PriceHistories(Subscription):
    def __init__(self, socket, topic, *args, **kwargs):
        super().__init__(socket, topic,
                         primary_key=('quote', 'base', 'intvl', 'start_time'), *args, **kwargs)

    async def __call__(self, from_time, to_time):
        if self.loop is None:
            self.subscribe(payload={'from_time': from_time, 'to_time': to_time})
            return await self.wait()
        await self.request(payload={'from_time': from_time, 'to_time': to_time})
        return self.data


class Trades(Subscription):
    def __init__(self, socket, topic, *args, **kwargs):
        super().__init__(socket, topic, *args, **kwargs)

    async def __call__(self, size):
        if self.loop is None:
            self.subscribe(payload={'size': size})
            return await self.wait()
        await self.request(payload={'size': size})
        return self.data


class MyUser(Subscription):
    def __init__(self, socket, topic, *args, **kwargs):
        super().__init__(socket, topic, primary_key=None, *args, **kwargs)


class MyAssets(Subscription):
    def __init__(self, socket, topic, *args, **kwargs):
        super().__init__(socket, topic, primary_key='coin', *args, **kwargs)


class MyOrders(Subscription):
    def __init__(self, socket, topic, *args, **kwargs):
        super().__init__(socket, topic, *args, **kwargs)

    @optional('quote', 'base', 'to_id', 'size', 'sell', 'closed')
    async def __call__(self, **kwargs):
        return await super().__call__(**kwargs)


class MyTrades(Subscription):
    def __init__(self, socket, topic, *args, **kwargs):
        super().__init__(socket, topic, *args, **kwargs)

    @optional('quote', 'base', 'to_id', 'size')
    async def __call__(self, sell, **kwargs):
        kwargs.update({'sell': sell})
        return await super().__call__(**kwargs)


class MyDeposits(Subscription):
    def __init__(self, socket, topic, *args, **kwargs):
        super().__init__(socket, topic, *args, **kwargs)

    @optional('to_id', 'size')
    async def __call__(self, **kwargs):
        return await super().__call__(**kwargs)


class MyWithdrawal(Subscription):
    def __init__(self, socket, topic, *args, **kwargs):
        super().__init__(socket, topic, *args, **kwargs)

    @optional('to_id', 'size')
    async def __call__(self, **kwargs):
        return await super().__call__(**kwargs)


class MyTXSummaries(Subscription):
    def __init__(self, socket, topic, *args, **kwargs):
        super().__init__(socket, topic, *args, **kwargs)

    @optional('type', 'to_id', 'size')
    async def __call__(self, **kwargs):
        if 'type' in kwargs:
            assert kwargs['type'] in ['deposit', 'wdrl']
        return await super().__call__(**kwargs)


class MyAirdropHistories(Subscription):
    def __init__(self, socket, topic, *args, **kwargs):
        super().__init__(socket, topic, *args, **kwargs)

    @optional('to_id', 'size')
    async def __call__(self, **kwargs):
        return await super().__call__(**kwargs)
