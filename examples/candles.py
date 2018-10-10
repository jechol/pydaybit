import asyncio
import logging
from datetime import datetime

import dateparser
import numpy as np
import pandas as pd
from tabulate import tabulate

from pydaybit.daybit import Daybit


async def get_candles(start_time, end_time, interval, quote, base, max_size=100):
    if isinstance(start_time, str):
        start_time = dateparser.parse(start_time)
    if isinstance(end_time, str):
        end_time = dateparser.parse(end_time)

    if isinstance(start_time, datetime):
        start_time = int(start_time.timestamp() * 1000)
    if isinstance(end_time, datetime):
        end_time = int(end_time.timestamp() * 1000)

    if max_size > 100:
        logging.warning('maximum candles per request is 100. it will use 100 as instead of {}.'.format(max_size))
        max_size = 100

    async with Daybit() as daybit:
        all = pd.DataFrame(columns=['close', 'low', 'high', 'close', 'vol'])
        channel = daybit.price_histories / quote / base / interval
        for to_time in range(end_time, start_time, -(max_size * interval * 1000)):
            from_time = max(start_time, to_time - ((max_size - 1) * interval * 1000))

            channel.reset_data()
            candles = await channel(from_time=from_time,
                                    to_time=to_time)
            n = len(candles)
            if n == 0:
                break

            index = np.array([datetime.fromtimestamp(candles[i]['start_time'] / 1000) for i in sorted(candles.keys())])
            data = np.array([[candles[i]['open'],
                              candles[i]['low'],
                              candles[i]['high'],
                              candles[i]['close'],
                              candles[i]['base_vol']] for i in sorted(candles.keys())])

            sub = pd.DataFrame(index=index,
                               columns=['close', 'low', 'high', 'close', 'vol'],
                               data=data)
            all = pd.concat([sub, all])
        return all


df = asyncio.get_event_loop().run_until_complete(get_candles(start_time='2018 Jan 2 10:00 PM',
                                                             end_time='now',
                                                             interval=60,
                                                             quote='USDT',
                                                             base='BTC',
                                                             max_size=50))
print(tabulate(df, headers='keys', tablefmt='psql', floatfmt='.8'))
print(len(df))
