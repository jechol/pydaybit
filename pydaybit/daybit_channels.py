import asyncio
import logging
from decimal import Decimal

from pydaybit.exceptions import UnexpectedFormat, find_error_types
from pydaybit.phoenix import Channel
from pydaybit.utility import optional

logger = logging.getLogger(__name__)


class DaybitChannel(Channel):
    def __init__(self, socket, topic, params=None, max_queue=2 ** 5, timeout_secs=3):
        self.data = {}
        self.callback_future = None
        super().__init__(socket, topic, params, max_queue, timeout_secs=timeout_secs)

    async def push(self, event, payload={}, timeout=None, retry=3, wait_response=True, with_timestamp=True):
        if timeout is None:
            timeout = self.timeout_secs
        if with_timestamp:
            payload.update({'timestamp': self.socket.estimated_timestamp()})

        try:
            response = await super().push(event=event,
                                          payload=payload,
                                          timeout=timeout,
                                          retry=retry,
                                          wait_response=wait_response)
            if response['status'] == 'ok':
                self.update(response['response'].get('data', {}))
                return response['response'].get('data', {})
            error_code = response['response'].get('error_code', '')
            reason = response['response'].get('message', '')

            if error_code == '':
                reason = response['response'].get('reason', '')

            raise find_error_types(error_code)(self.topic, error_code)
        except KeyError:
            raise UnexpectedFormat

    async def receive(self):
        try:
            message = await self.messages.get()
            assert message.event == 'notification'

            response = message.payload.get('data', {})
            if self.callback_future:
                self.callback_future.set_result(response)
                self.callback_future = None
            self.update(response)

            return response
        except KeyError:
            raise UnexpectedFormat

    async def request(self, payload={}, **kwargs):
        payload.update(kwargs)
        msg = await self.push('request', payload)
        if self.callback_future:
            self.callback_future.set_result(self.data)
            self.callback_future = None
        return msg

    def wait(self):
        if self.callback_future is None:
            self.callback_future = asyncio.Future(loop=self.socket.loop)
        return self.callback_future

    def update(self, response):
        pass


class API(DaybitChannel):
    def __init__(self, socket, topic, params=None, max_queue=2 ** 5, timeout_secs=3):
        super().__init__(socket, topic, params, max_queue, timeout_secs=timeout_secs)

    async def get_server_time(self):
        server_time = (await self.push('get_server_time',
                                       payload={},
                                       timeout=60 * 60 * 24 * 7,
                                       with_timestamp=True))['server_time']
        return server_time

    async def create_order(self,
                           sell: bool,
                           quote: str,
                           base: str,
                           amount: Decimal,
                           role: str,
                           price: Decimal = Decimal('0'),
                           cond_type: str = 'none',
                           cond_arg1: Decimal = Decimal('0'),
                           cond_arg2: Decimal = Decimal('0'),
                           **payload):
        assert role in ['both', 'maker_only', 'taker_only']
        if role == 'both':
            assert cond_type in ['none', 'le', 'ge', 'down_from_high', 'up_from_low']
        else:
            assert cond_type == 'none'

        payload.update({
            'sell': sell,
            'quote': quote,
            'base': base,
            'amount': str(amount),
            'role': role,
            'cond_type': cond_type,
        })

        if cond_type != 'none':
            payload.update({'cond_arg1': str(cond_arg1)})

        if cond_type in ['down_from_high', 'up_from_low']:
            payload.update({'cond_arg2': str(cond_arg2)})
        else:
            payload.update({'price': str(price)})

        return await self.push('create_order',
                               payload=payload)

    async def cancel_order(self, order_id: int):
        return await self.push('cancel_order',
                               payload={'order_id': order_id})

    async def cancel_orders(self, order_ids):
        return await self.push('cancel_orders',
                               payload={'order_ids': order_ids})

    async def cancel_all_my_orders(self):
        return await self.push('cancel_all_my_orders')

    @optional('to_tag', 'to_org')
    async def create_wdrl(self,
                          coin: str,
                          to_addr: str,
                          amount: Decimal,
                          **payload):
        amount = Decimal(amount)
        payload.update({'coin': coin,
                        'to_addr': to_addr,
                        'amount': str(amount)})

        return await self.push('create_wdrl',
                               payload=payload)
