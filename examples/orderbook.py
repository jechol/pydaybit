import asyncio
from decimal import Decimal
from pprint import pprint

from pydaybit import Daybit


async def daybit_order_books():
    async with Daybit() as daybit:
        quote = 'BTC'
        base = 'ETH'
        price_intvl = Decimal((await daybit.markets())['{}-{}'.format(quote, base)]['tick_price'])
        orderbook = await (daybit.order_books / quote / base / price_intvl)()
        bid = []
        ask = []

        price_intvl = Decimal(price_intvl)
        for key in sorted(orderbook.keys()):
            range = orderbook[key]
            buy_vol = Decimal(range['buy_vol'])
            sell_vol = Decimal(range['sell_vol'])
            min_price = Decimal(range['min_price']).quantize(price_intvl)
            max_price = Decimal(range['max_price']).quantize(price_intvl)

            if buy_vol > 0:
                bid.append([min_price, buy_vol])
            if sell_vol > 0:
                ask.append([max_price, sell_vol])
        bid = list(reversed(bid))
        spread = str(ask[0][0] - bid[0][0])
        ret = {'bids': bid,
               'asks': ask,
               'spread': spread
               }
        pprint(ret)
        return ret


asyncio.get_event_loop().run_until_complete(daybit_order_books())
