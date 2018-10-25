import asyncio
import logging
import ssl as ssl_lib
import time
from decimal import Decimal

import websockets

from pydaybit import daybit_url, daybit_api_key, daybit_api_secret, PARAM_API_KEY, PARAM_API_SECRET
from pydaybit.daybit_channels import API
from pydaybit.phoenix.message import PHOENIX_EVENT
from pydaybit.phoenix.phoenix import Phoenix
from pydaybit.ratelimit import RateLimit
from pydaybit.subscriptions import Coins, CoinPrices, QuoteCoins, Markets, MarketSummaryIntervals, MarketSummaries, \
    OrderBooks, PriceHistoryIntervals, PriceHistories, Trades, MyUser, MyAssets, MyOrders, MyTrades, MyAirdropHistories, \
    MyTXSummaries
from pydaybit.utility import optional

logger = logging.getLogger(__name__)


class Daybit(Phoenix):
    def __init__(self, url=None, params={}, loop=None, heartbeat_secs=30, sync_timestamp_secs=30, timeout_secs=3,
                 ssl=None):
        if url is None:
            url = daybit_url()
        if 'api_key' not in params:
            params[PARAM_API_KEY] = daybit_api_key()
            params[PARAM_API_SECRET] = daybit_api_secret()

        if url[:3] == 'wss' and ssl is None:
            ssl_context = ssl_lib.SSLContext(ssl_lib.PROTOCOL_TLSv1_2)
            ssl_context.options |= ssl_lib.OP_NO_SSLv2
            ssl_context.options |= ssl_lib.OP_NO_SSLv3
            ssl_context.options |= ssl_lib.OP_NO_TLSv1
            ssl_context.options |= ssl_lib.OP_NO_TLSv1_1

            ssl = ssl_context

        Phoenix.__init__(self, url, params, loop, heartbeat_secs, timeout_secs, ssl=ssl)
        self._init_subscriptions()
        self.rate_limit = RateLimit(loop=self.loop)
        self._init_rate_limits()
        self._timestamp_diff = 0
        self._sync_timestamp_secs = sync_timestamp_secs

    def _init_subscriptions(self):
        self.coins = self.channel('/subscription:coins', channel_t=Coins)
        self.coin_prices = self.channel('/subscription:coin_prices', channel_t=CoinPrices)
        self.quote_coins = self.channel('/subscription:quote_coins', channel_t=QuoteCoins)
        self.markets = self.channel('/subscription:markets', channel_t=Markets)
        self.market_summary_intvls = self.channel('/subscription:market_summary_intvls',
                                                  channel_t=MarketSummaryIntervals)
        self.market_summaries = self.channel('/subscription:market_summaries', channel_t=MarketSummaries)
        self.order_books = self.channel('/subscription:order_books', channel_t=OrderBooks)
        self.price_history_intvls = self.channel('/subscription:price_history_intvls', channel_t=PriceHistoryIntervals)
        self.price_histories = self.channel('/subscription:price_histories', channel_t=PriceHistories)
        self.trades = self.channel('/subscription:trades', channel_t=Trades)
        self.my_users = self.channel('/subscription:my_users', channel_t=MyUser)
        self.my_assets = self.channel('/subscription:my_assets', channel_t=MyAssets)
        self.my_orders = self.channel('/subscription:my_orders', channel_t=MyOrders)
        self.my_trades = self.channel('/subscription:my_trades', channel_t=MyTrades)
        self.my_tx_summaries = self.channel('/subscription:my_tx_summaries', channel_t=MyTXSummaries)
        self.my_airdrop_histories = self.channel('/subscription:my_airdrop_histories', channel_t=MyAirdropHistories)

    def _init_rate_limits(self):
        self.rate_limit.add_limit('get_server_time', 10)
        self.rate_limit.add_limit('cancel_orders', 5)
        self.rate_limit.add_limit('cancel_all_my_orders', 5)
        self.rate_limit.add_limit('create_wdrl', 10)
        self.rate_limit.add_limit('coins', 3)
        self.rate_limit.add_limit('coin_prices', 3)
        self.rate_limit.add_limit('quote_coins', 3)
        self.rate_limit.add_limit('markets', 3)
        self.rate_limit.add_limit('market_summary_intvls', 3)
        self.rate_limit.add_limit('market_summaries', 3)
        self.rate_limit.add_limit('order_books', 3)
        self.rate_limit.add_limit('price_history_intvls', 3)
        self.rate_limit.add_limit('price_histories', 8)
        self.rate_limit.add_limit('trades', 3)
        self.rate_limit.add_limit('my_users', 3)
        self.rate_limit.add_limit('my_assets', 3)
        self.rate_limit.add_limit('my_orders', 3)
        self.rate_limit.add_limit('my_trades', 3)
        self.rate_limit.add_limit('my_tx_summaries', 3)
        self.rate_limit.add_limit('my_airdrop_histories', 3)

    async def connect(self):
        try:
            await super().connect()
            self._coroutines.append(asyncio.ensure_future(self._sync_timestamp_coro(), loop=self.loop))
            await self.sync_timestamp()

        except websockets.exceptions.InvalidStatusCode as e:
            if e.status_code == 403:
                raise ConnectionError('{} Error, check your api_key or api_secret.'.format(e.status_code))
            else:
                raise ConnectionError('{} Error'.format(e.status_code))

    async def push(self, channel, event, payload, timeout=3, retry=3, wait_response=True):
        if self._phoenix is channel:
            pass
        elif event not in PHOENIX_EVENT.values():
            if channel.topic == '/api':
                await self.rate_limit.wait(event)
            else:
                await self.rate_limit.wait(channel.subtopic)

        return await super().push(channel=channel,
                                  event=event,
                                  payload=payload,
                                  timeout=timeout,
                                  retry=retry,
                                  wait_response=wait_response)

    async def sync_timestamp(self):
        server_timestamp = await self.get_server_time()
        here_timestamp = self.timestamp()
        self._timestamp_diff = server_timestamp - here_timestamp

    async def _sync_timestamp_coro(self):
        while True:
            await asyncio.sleep(self._sync_timestamp_secs, loop=self.loop)
            await self.sync_timestamp()

    async def api(self):
        topic = '/api'
        try:
            channel = self._channels[topic]
        except KeyError:
            channel = API(self, topic, timeout_secs=self._timeout_secs)
            self._channels[topic] = channel
            await channel.join()
        return channel

    async def get_server_time(self):
        return await (await self.api()).get_server_time()

    async def create_order(self, sell: bool,
                           quote: str,
                           base: str,
                           amount: Decimal,
                           role: str,
                           cond_type: str = 'none',
                           price: Decimal = Decimal('0'),
                           cond_arg1: Decimal = Decimal('0'),
                           cond_arg2: Decimal = Decimal('0'),
                           **kwargs):
        market = (await self.markets())['{}-{}'.format(quote, base)]
        coins = (await self.coins())

        tick_price = Decimal(market['tick_price'])
        tick_amount = Decimal(coins[base]['tick_amount'])

        price = Decimal(price).quantize(tick_price)
        amount = Decimal(amount).quantize(tick_amount)

        return await (await self.api()).create_order(sell, quote, base, amount, role, price, cond_type,
                                                     cond_arg1, cond_arg2, **kwargs)

    async def cancel_order(self, order_id):
        return await (await self.api()).cancel_order(order_id)

    async def cancel_orders(self, order_ids):
        assert isinstance(order_ids, list)
        assert len(order_ids) > 0
        order_ids = ",".join([str(order_id) for order_id in order_ids])
        return await (await self.api()).cancel_orders(order_ids)

    async def cancel_all_my_orders(self):
        return await (await self.api()).cancel_all_my_orders()

    @optional('to_tag')
    async def create_wdrl(self, coin, to_addr, amount, **kwargs):
        return await (await self.api()).create_wdrl(coin, to_addr, amount, **kwargs)

    @staticmethod
    def timestamp():
        return int(round(time.time() * 1000))

    # estimated server timestamp
    def estimated_timestamp(self):
        return int(round(time.time() * 1000 + self._timestamp_diff))
