import asyncio
import json
import logging
import re
import sys

import websockets
from async_timeout import timeout as atimeout
from furl import furl

from pydaybit.phoenix.channel import Channel
from pydaybit.phoenix.exceptions import ConnectionClosed, CommunicationError
from pydaybit.phoenix.message import OutMessage, PHOENIX_EVENT, str_to_msg

logger = logging.getLogger(__name__)


class Phoenix:
    def __init__(self, url, params=None, loop=None, heartbeat_secs=30, timeout_secs=3, ssl=None):
        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop
        self.url = url
        self.params = params
        self._socket = None
        self._ref = 0
        self._channels = {}
        self._waited_messages = {}
        self._heartbeat_secs = heartbeat_secs
        self._coroutines = []
        self._reconnect_tries = 0
        self.connected = False
        self._phoenix = Channel(self, 'phoenix')
        self._connection_lost = False
        self._timeout_secs = timeout_secs
        self._ssl = ssl

    async def connect(self):
        if self.connected:
            return
        try:
            logger.info("connect to %s.", furl(self.url).add(self.params).url)
            self.connected = True
            async with atimeout(10, loop=self.loop):
                self._socket = await websockets.connect(furl(self.url).add(self.params).url,
                                                        ssl=self._ssl,
                                                        loop=self.loop)
            self._coroutines = [asyncio.ensure_future(self.recv(), loop=self.loop),
                                asyncio.ensure_future(self.heartbeat(), loop=self.loop),
                                asyncio.ensure_future(self.wait_for_disconnection(), loop=self.loop)]
        except OSError as e:
            if re.compile(r'.*Errno 61.*').match(str(e)):
                raise ConnectionRefusedError('Server is not responding.')
            raise e
        except asyncio.TimeoutError:
            raise TimeoutError('Timeout in opening a websocket.')

    async def disconnect(self):
        if not self.connected:
            return

        for ch in self._channels:
            await self._channels[ch].leave()
        self._remove_all_channels()
        self._connection_lost = self._socket.connection_lost_waiter.done()
        self.connected = False
        await self._socket.close()
        logger.info("disconnected. (%d) %s", self._socket.close_code, self._socket.close_reason)
        for co in self._coroutines:
            co.cancel()
        self._coroutines = []

    def channel(self, topic, params=None, channel_t=Channel, **kwargs):
        try:
            if 'timeout_secs' not in kwargs:
                kwargs['timeout_secs'] = self._timeout_secs
            channel = self._channels[topic]
        except KeyError:
            channel = channel_t(self, topic, params, **kwargs)
            self._channels[topic] = channel
        return channel

    def remove_channel(self, topic):
        self._channels.pop(topic, None)

    def _remove_all_channels(self):
        self._channels.clear()

    async def push(self, channel, event, payload, timeout=None, retry=3, wait_response=True):
        if not self.connected:
            raise CommunicationError("sent a message before connection.")
        if timeout is None:
            timeout = self._timeout_secs

        msg_response = None
        ref = None
        if retry <= 0:
            retry = 0
        retry += 1

        for i in range(retry):
            try:
                async with atimeout(timeout, loop=self.loop):
                    ref = self.make_ref()
                    if PHOENIX_EVENT['JOIN'] == event:
                        channel.join_ref = ref
                    if payload is None:
                        payload = {}
                    msg = json.dumps(OutMessage(topic=channel.topic,
                                                event=event,
                                                payload=payload,
                                                ref=ref,
                                                join_ref=channel.join_ref,
                                                timeout=timeout * 1000,
                                                ).asdict())
                    logger.debug("> %s", msg)
                    await self._send(msg)

                    if wait_response:
                        msg_response = asyncio.Future(loop=self.loop)
                        if ref in self._waited_messages:
                            self._waited_messages[ref].cancel()
                        self._waited_messages[ref] = msg_response

                        try:
                            await msg_response
                        except asyncio.CancelledError:
                            raise asyncio.TimeoutError

            except asyncio.TimeoutError:
                retry_str = ''
                if i > 0:
                    retry_str = ' retry {}/{}'.format(i, retry - 1)
                logger.warning(('{}:{} - failed to get a response.' + retry_str).format(channel.topic, event))

                if wait_response and ref is not None:
                    self._waited_messages.pop(ref, None)
            else:
                if msg_response is None:
                    return
                return msg_response.result()
        raise CommunicationError("failed to send a message.")

    def make_ref(self):
        if self._ref == sys.maxsize:
            new_ref = self._ref = 0
        else:
            new_ref = self._ref = self._ref + 1
        return str(new_ref)

    async def _send(self, message):
        await self._socket.send(message)

    async def heartbeat(self):
        while True:
            await asyncio.sleep(self._heartbeat_secs, loop=self.loop)
            await self.push(self._phoenix, 'heartbeat', {})

    async def recv(self):
        try:
            while True:
                try:
                    recv_msg = await self._socket.recv()
                    logger.debug("< %s", recv_msg)
                    message = str_to_msg(recv_msg)
                except json.decoder.JSONDecodeError:
                    logger.warning('ignore a invalid message: {}.'.format(recv_msg))
                else:
                    if message.event == PHOENIX_EVENT['REPLY']:
                        if message.ref in self._waited_messages:
                            future = self._waited_messages.pop(message.ref)
                            future.set_result(message.payload)
                        else:
                            logger.warning('received not waiting message. {}'.format(recv_msg))
                    else:
                        if message.topic in self._channels:
                            await self._channels[message.topic].messages.put(message)
        except ConnectionClosed:
            pass
        except Exception:
            logger.error("Error in data transfer", exc_info=True)
            await asyncio.shield(self.disconnect(), loop=self.loop)

    async def wait_for_disconnection(self):
        await self._socket.connection_lost_waiter
        await self.disconnect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._do_exit(exc_type)

    async def __aenter__(self):
        await self.__await__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
        self._do_exit()

    def _do_exit(self):
        if self._connection_lost:
            raise ConnectionClosed(self._socket.close_code, self._socket.close_reason)

    def __await__(self):
        return self.__await_impl__()

    async def __await_impl__(self):
        await self.connect()
        return self
