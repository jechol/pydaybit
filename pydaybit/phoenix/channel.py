import asyncio
import enum

from pydaybit.phoenix.exceptions import NotAllowedEventName, CommunicationError
from pydaybit.phoenix.message import PHOENIX_EVENT


class State(enum.IntEnum):
    CONNECTING, OPEN, CLOSING, CLOSED = range(4)


class Channel:
    def __init__(self, socket, topic, params=None, max_queue=2 ** 5, timeout_secs=3, num_retry=3):
        self.socket = socket
        self.topic = topic
        self.params = params
        self.join_ref = None
        self.status = State.CLOSED
        self.messages = asyncio.queues.Queue(max_queue, loop=self.socket.loop)
        self.timeout_secs = timeout_secs
        self.num_retry = num_retry

    async def join(self, payload=None, wait_response=True):
        def failed_to_connect(reason=''):
            self.status = State.CLOSED
            raise CommunicationError('{} JOIN FAILED: {}'.format(self.topic, reason))

        if self.status == State.CLOSED:
            self.status = State.CONNECTING

            try:
                msg = await self._push(PHOENIX_EVENT['JOIN'], payload, timeout=self.timeout_secs, retry=self.num_retry,
                                       wait_response=wait_response, _internal_use=True)
            except CommunicationError:
                failed_to_connect('No Response')
            else:
                if msg['status'].lower() == 'ok':
                    self.status = State.OPEN
                else:
                    if 'response' in msg:
                        if 'message' in msg['response'] and 'error_code' in msg['response']:
                            failed_to_connect(reason=msg['response']['message'])
                        elif 'reason' in msg['response']:
                            failed_to_connect(reason=msg['response']['reason'])
                    else:
                        failed_to_connect()
            return msg

    async def leave(self, wait_response=True):
        if self.status == State.OPEN:
            self.status = State.CLOSING

            try:
                msg = await self._push(PHOENIX_EVENT['LEAVE'], timeout=self.timeout_secs, retry=self.num_retry,
                                       wait_response=wait_response, _internal_use=True)
            except CommunicationError:
                pass

            self.join_ref = None
            self.status = State.CLOSED
            return msg

    async def push(self, event, payload={}, timeout=3, retry=3, wait_response=True):
        return await self._push(event=event,
                                payload=payload,
                                timeout=timeout,
                                retry=retry,
                                wait_response=wait_response)

    async def _push(self, event, payload=None, timeout=3, retry=3, wait_response=True, _internal_use=False):
        if not _internal_use:
            if event in PHOENIX_EVENT.values():
                raise NotAllowedEventName(event)

        ret = await self.socket.push(self,
                                     event=event,
                                     payload=payload,
                                     wait_response=wait_response,
                                     timeout=timeout,
                                     retry=retry)
        return ret

    async def receive(self):
        return await self.messages.get()

    async def __aenter__(self):
        await self.join()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.leave()
