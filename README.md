# Pydaybit
[![CircleCI](https://circleci.com/gh/daybit-exchange/pydaybit.svg?shield=svg&circle-token=b7d9eaa9d871c3421f8ca3583be4a379f9b6b856)](https://circleci.com/gh/daybit-exchange/pydaybit)
[![pypi](https://img.shields.io/pypi/v/pydaybit.svg)](https://pypi.org/project/pydaybit/)
[![Downloads](https://pepy.tech/badge/pydaybit)](https://pypi.org/project/pydaybit/)
[![License](https://img.shields.io/github/license/daybit-exchange/pydaybit.svg)](https://github.com/daybit-exchange/pydaybit/blob/master/LICENSE)

**Pydaybit** is an API wrapper for [**DAYBIT**](https://www.daybit.com) exchange  written in Python.
It supports python 3.5 or newer.
   
## Disclaimer

USE THE SOFTWARE AT YOUR OWN RISK. THE AUTHORS AND ALL AFFILIATES ASSUME NO RESPONSIBILITY FOR YOUR TRADING RESULTS.

## Installation

    $ pip install --upgrade pydaybit

## Environment Variables
* `DAYBIT_API_KEY`
* `DAYBIT_API_SECRET`

## Examples


#### Server Timestamp
```python
import asyncio

from pydaybit import Daybit


async def daybit_get_server_time():
    async with Daybit() as daybit:
        server_timestamp = await daybit.get_server_time()
        print('Daybit: {}'.format(server_timestamp))


asyncio.get_event_loop().run_until_complete(daybit_get_server_time())
```

#### Without Enviroment Variables
```python
import asyncio
from pprint import pprint

from pydaybit import Daybit, PARAM_API_KEY, PARAM_API_SECRET


async def daybit_trades():
    async with Daybit(params={PARAM_API_KEY: "YOUR_API_KEY",
                              PARAM_API_SECRET: "YOUR_API_SECRET"}) as daybit:
        pprint(await daybit.trades(quote='USDT',
                                   base='BTC',
                                   num_trades=5), indent=2)


asyncio.get_event_loop().run_until_complete(daybit_markets())
```

#### Without Asynchronous Context Manager
```python
import asyncio
from pprint import pprint

from pydaybit import Daybit


async def daybit_markets():
    daybit = Daybit()
    await daybit.connect()
    pprint(await daybit.markets(), indent=2)
    await daybit.disconnect()


asyncio.get_event_loop().run_until_complete(daybit_markets())
```

#### Subscriptons
All Subscription APIs are updated in real time. Following `daybit_without_await()` will print coin prices as same as `daybit_coin_prices()`.
```python
import asyncio
from pprint import pprint

from pydaybit import Daybit


async def daybit_coin_prices():
    async with Daybit() as daybit:
        for _ in range(5):
            pprint(await daybit.coin_prices(), indent=2)
            await asyncio.sleep(1)


async def daybit_without_await():
    async with Daybit() as daybit:
        await daybit.coin_prices()
        for _ in range(5):
            pprint(daybit.channel('/subscription:coin_prices').data, indent=2)
            await asyncio.sleep(1)


asyncio.get_event_loop().run_until_complete(daybit_coin_prices())
# asyncio.get_event_loop().run_until_complete(daybit_without_await())
```

#### Subscription Args
Channel Arguments can be described with `/` operators.
```python
import asyncio
import time

from pydaybit import Daybit


async def get_candles(from_time, to_time, interval, quote, base):
    async with Daybit() as daybit:
        channel = daybit.price_histories / quote / base / interval
        candles = await channel(from_time=from_time,
                                to_time=to_time)
        print(candles)


asyncio.get_event_loop().run_until_complete(get_candles(from_time=int((time.time() - 1000) * 1000),
                                                        to_time=int(time.time() * 1000),
                                                        interval=60,
                                                        quote='USDT',
                                                        base='BTC'))
```

#### Reset Cached Data
A channel have local cached data in `channel.data`. If want to remove cached data, use `channel.reset_data()`. 
For example, see `examples/candles.py`.

```python
async def get_candles(start_time, end_time, interval, quote, base, max_size=100, candle_type=float):
...
    async with Daybit() as daybit:
    ...
        channel = daybit.price_histories / quote / base / interval
        for to_time in range(end_time, start_time, -(max_size * interval * 1000)):
            from_time = max(start_time, to_time - ((max_size - 1) * interval * 1000))

            channel.reset_data()
            candles = await channel(from_time=from_time,
                                    to_time=to_time)
...
```


## TEST

    $ python -m pytest
or  

    $ pytest


## License

Apache License 2.0
