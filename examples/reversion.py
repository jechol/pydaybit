import asyncio
import time
from datetime import datetime
from decimal import Decimal

import numpy as np
import pandas as pd

from pydaybit.daybit import Daybit
from pydaybit.exceptions import ResponseError


def millisecs(timestamp):
    return int(timestamp * 1000)


def current():
    return time.time()


class ReversionMovingAverage:
    def __init__(self,
                 window_size=5,
                 trade_frequency_in_secs=60,
                 asset_per_trade=0.05,
                 slippage=0.0001,
                 threshold=0.0005,
                 duration=None,
                 quote='USDT',
                 base='BTC',
                 daybit=None):
        self.daybit = daybit
        self.loop = None
        self.base_value = None

        self.window_size = window_size
        self.quote = quote
        self.base = base
        self.freq = trade_frequency_in_secs
        self.threshold = threshold
        self.trade_unit = asset_per_trade
        self.slippage = slippage
        self.base_amount = Decimal(0)
        self.latest_order = None
        self.current_tick = 0
        self.end_tick = duration
        self.tick_price = Decimal('0.00000001')

    async def tick(self):
        self.current_tick += 1

        await self._sync_unit_time()
        await self.daybit.cancel_all_my_orders()

        if self.base_value is None:
            self.base_value = await self.net_value()

        current_net_value = await self.net_value()
        avg = await self.average_price()
        price = await self.current_price()
        filled_amount = await self.filled_amount()
        self.base_amount = (self.base_amount + filled_amount).quantize(self.tick_price)

        op = '='
        if avg < price:
            op = '<'
        elif avg > price:
            op = '>'

        print('{} profit: {} average: {} {} current: {} amount({}): {}'.format(datetime.now(),
                                                                               current_net_value - self.base_value,
                                                                               avg,
                                                                               op,
                                                                               price,
                                                                               self.base,
                                                                               self.base_amount))
        a_price = (avg * Decimal(1 + self.threshold)).quantize(self.tick_price)
        if avg > price * Decimal(1 + self.threshold):
            print('buy')
            self.latest_order = await self.daybit.create_order(
                sell=False,
                quote=self.quote,
                base=self.base,
                amount=self.trade_unit,
                role='both',
                price=price * Decimal(1 + self.slippage))
        elif avg < price * Decimal(1 - self.threshold):
            print('sell')
            self.latest_order = await self.daybit.create_order(
                sell=True,
                quote=self.quote,
                base=self.base,
                amount=self.trade_unit,
                role='both',
                price=price * Decimal(1 - self.slippage))
        else:
            print('nothing')

    async def run(self, *, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop
        if self.daybit is None:
            self.daybit = Daybit(loop=self.loop)
        try:
            await self.daybit.connect()
            self.base_value = await self.net_value()

            print('start trading.')

            while True:
                try:
                    if self.current_tick == self.end_tick:
                        break
                    await self.tick()
                except (asyncio.TimeoutError, ResponseError):
                    pass
        except Exception as e:
            print(e)
            raise e
        finally:
            await self.daybit.disconnect()

    async def filled_amount(self):
        if self.latest_order is not None:
            my_orders = await self.daybit.my_orders()
            order = my_orders[self.latest_order['id']]
            amount = Decimal(order['amount']).quantize(self.tick_price)
            if order['sell'] is True:
                amount *= -1
            return amount
        return Decimal(0)

    async def average_price(self, axis='close'):
        candles = await self.candles(from_time=millisecs(current() - self.freq * self.window_size),
                                     to_time=millisecs(current() - self.freq))
        average = Decimal(candles[axis].mean()).quantize(self.tick_price)
        return average

    async def current_price(self):
        channel = self.daybit.price_histories / self.quote / self.base / self.freq
        channel.reset_data()
        prices = await channel(from_time=millisecs(current()),
                               to_time=millisecs(current()))
        price = prices[sorted(prices.keys())[-1]]['close']
        return Decimal(price).quantize(self.tick_price)

    async def candles(self, from_time, to_time):
        channel = self.daybit.price_histories / self.quote / self.base / self.freq
        channel.reset_data()
        prices = await channel(from_time=from_time,
                               to_time=to_time)

        index = np.array([datetime.fromtimestamp(prices[i]['start_time'] / 1000) for i in sorted(prices.keys())])
        data = np.array([[Decimal(prices[i]['open']),
                          Decimal(prices[i]['low']),
                          Decimal(prices[i]['high']),
                          Decimal(prices[i]['close']),
                          Decimal(prices[i]['base_vol'])] for i in sorted(prices.keys())])

        df = pd.DataFrame(index=index,
                          columns=['open', 'low', 'high', 'close', 'vol'],
                          data=data)

        return df

    async def net_value(self):
        my_assets = await self.daybit.my_assets()
        net = Decimal(my_assets[self.quote]['investment_usd']) + Decimal(my_assets[self.base]['investment_usd'])
        return net.quantize(self.tick_price)

    async def _sync_unit_time(self):
        remain_sec = (self.freq - time.time() % self.freq) % self.freq
        if remain_sec > 0:
            await asyncio.sleep(remain_sec, loop=self.loop)


print('This code may have bugs and cause property loss. Running this code is at your own risk.')
asyncio.get_event_loop().run_until_complete(ReversionMovingAverage().run())
