import asyncio
import logging
import time
from contextlib import suppress
from decimal import Decimal
from pprint import pprint

from pydaybit import Daybit
from pydaybit.exceptions import OrderAlreadyClosed

logger = logging.getLogger('pydaybit')
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(stream_handler)


async def daybit_get_server_time():
    async with Daybit() as daybit:
        pprint(await daybit.get_server_time())


async def current_price(daybit, quote, base):
    summary_intvl = sorted((await daybit.market_summary_intvls()).keys())[0]
    price = (await (daybit.market_summaries / summary_intvl)())['{}-{}'.format(quote, base)]['close']
    return Decimal(price)


async def daybit_create_order_sell():
    async with Daybit() as daybit:
        quote = 'USDT'
        base = 'BTC'

        tick_price = Decimal((await daybit.markets())['{}-{}'.format(quote, base)]['tick_price'])
        tick_amount = Decimal((await daybit.coins())[base]['tick_amount'])

        # amount * price should be greater than 10 USDT.
        price = ((await current_price(daybit, quote, base)) * Decimal(1.2)).quantize(tick_price)
        amount = (Decimal(10.5) / price).quantize(tick_amount)

        response = await daybit.create_order(
            sell=True,
            role='both',
            quote=quote,
            base=base,
            price=price,
            amount=amount,
            cond_type='none',
        )
        pprint(response)

        with suppress(OrderAlreadyClosed):
            await daybit.cancel_order(response['id'])


async def daybit_create_order_buy():
    async with Daybit() as daybit:
        quote = 'USDT'
        base = 'BTC'

        tick_price = Decimal((await daybit.markets())['{}-{}'.format(quote, base)]['tick_price'])
        tick_amount = Decimal((await daybit.coins())[base]['tick_amount'])

        # amount * price should be greater than 10 USDT.
        price = (await current_price(daybit, quote, base)).quantize(tick_price)
        amount = (Decimal(10.5) / price).quantize(tick_amount)

        response = await daybit.create_order(
            sell=False,
            role='both',
            quote=quote,
            base=base,
            price=price,
            amount=amount,
            cond_type='none',
        )
        pprint(response)
        with suppress(OrderAlreadyClosed):
            print(await daybit.cancel_order(response['id']))


async def daybit_cancel_orders():
    async with Daybit() as daybit:
        my_orders = await daybit.my_orders()
        open_orders = ([my_orders[key]['id'] for key in my_orders if my_orders[key]['status'] == 'placed'])
        pprint(open_orders)
        pprint(await daybit.cancel_orders(open_orders))


async def daybit_cancel_all_my_orders():
    async with Daybit() as daybit:
        quote = 'USDT'
        base = 'BTC'

        tick_price = Decimal((await daybit.markets())['{}-{}'.format(quote, base)]['tick_price'])
        tick_amount = Decimal((await daybit.coins())[base]['tick_amount'])
        price_1 = ((await current_price(daybit, quote, base)) * Decimal(1.2)).quantize(tick_price)
        amount_1 = (Decimal(10.5) / price_1).quantize(tick_amount)

        price_2 = ((await current_price(daybit, quote, base)) * Decimal(1.4)).quantize(tick_price)
        amount_2 = (Decimal(10.5) / price_2).quantize(tick_amount)

        await daybit.create_order(
            sell=True,
            role='both',
            quote=quote,
            base=base,
            price=price_1 * 2,
            amount=amount_1,
            cond_type='none',
        )

        await daybit.create_order(
            sell=True,
            role='both',
            quote=quote,
            base=base,
            price=price_2,
            amount=amount_2,
            cond_type='none',
        )

        response = await daybit.cancel_all_my_orders()
        pprint(response)


async def daybit_create_wdrl():
    async with Daybit() as daybit:
        pprint(await daybit.create_wdrl(coin='BTC', to_addr='fake_address', amount='1'))


async def daybit_coins():
    async with Daybit() as daybit:
        pprint(await daybit.coins())


async def daybit_coin_prices():
    async with Daybit() as daybit:
        pprint(await daybit.coin_prices())


async def daybit_coin_prices_with_sym(sym='ETH'):
    async with Daybit() as daybit:
        pprint(await (daybit.coin_prices / sym)())


async def daybit_quote_coins():
    async with Daybit() as daybit:
        pprint(await daybit.quote_coins())


async def daybit_markets():
    async with Daybit() as daybit:
        pprint(await daybit.markets())


async def daybit_market_summary_intvls():
    async with Daybit() as daybit:
        pprint(await daybit.market_summary_intvls())


async def daybit_market_summaries():
    async with Daybit() as daybit:
        intvls = sorted((await daybit.market_summary_intvls()).keys())
        pprint(await (daybit.market_summaries / intvls[0])())


async def daybit_order_books():
    async with Daybit() as daybit:
        quote = 'USDT'
        base = 'BTC'
        price_intvl = Decimal((await daybit.markets())['{}-{}'.format(quote, base)]['tick_price']) * 10
        pprint(await (daybit.order_books / quote / base / price_intvl)())


async def daybit_price_history_intvls():
    async with Daybit() as daybit:
        pprint(await daybit.price_history_intvls())


async def daybit_price_histories():
    async with Daybit() as daybit:
        quote = 'USDT'
        base = 'BTC'
        intvl = sorted((await daybit.price_history_intvls()).keys())[0]
        pprint(
            await (daybit.price_histories / quote / base / intvl)(from_time=int(time.time() * 1000 - intvl * 10 * 1000),
                                                                  to_time=int(time.time() * 1000)))


async def daybit_trades():
    async with Daybit() as daybit:
        quote = 'USDT'
        base = 'BTC'
        pprint(await (daybit.trades / quote / base)(size=10))


async def daybit_my_users():
    async with Daybit() as daybit:
        pprint(await daybit.my_users())


async def daybit_my_assets():
    async with Daybit() as daybit:
        pprint(await daybit.my_assets())


async def daybit_my_orders():
    async with Daybit() as daybit:
        pprint(await daybit.my_orders(closed=True))


async def daybit_my_trades():
    async with Daybit() as daybit:
        pprint(await daybit.my_trades(sell=True))


async def daybit_my_tx_summaries():
    async with Daybit() as daybit:
        pprint(await daybit.my_tx_summaries(type='deposit'))
        pprint(await daybit.my_tx_summaries(type='wdrl'))


async def daybit_my_my_airdrop_histories():
    async with Daybit() as daybit:
        pprint(await daybit.my_airdrop_histories())


async def daybit_trade_vols():
    async with Daybit() as daybit:
        pprint(await daybit.trade_vols(size=10))


async def daybit_day_avgs():
    async with Daybit() as daybit:
        pprint(await daybit.day_avgs())


async def daybit_div_plans():
    async with Daybit() as daybit:
        pprint(await daybit.div_plans())


async def daybit_my_day_avgs():
    async with Daybit() as daybit:
        pprint(await daybit.my_day_avgs())


async def daybit_my_trade_vols():
    async with Daybit() as daybit:
        pprint(await daybit.my_trade_vols())


async def daybit_my_divs():
    async with Daybit() as daybit:
        pprint(await daybit.my_divs())


asyncio.get_event_loop().run_until_complete(daybit_trade_vols())
