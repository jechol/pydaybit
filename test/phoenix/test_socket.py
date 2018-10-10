import asyncio
import logging

import pytest
import websockets
from async_timeout import timeout as atimeout

from pydaybit.phoenix import Phoenix, PHOENIX_EVENT
from pydaybit.phoenix.exceptions import ConnectionClosed, NotAllowedEventName, CommunicationError
from pydaybit.phoenix.message import str_to_msg, msg_to_str

logger = logging.getLogger('pydaybit')
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(stream_handler)


async def handle(ws, _, responses):
    for r in responses:
        event, payload = r
        recv_msg = str_to_msg(await ws.recv())
        send_msg = msg_to_str(recv_msg.ref,
                              recv_msg.join_ref,
                              recv_msg.topic,
                              event,
                              payload)
        await ws.send(send_msg)


def test_connection(unused_tcp_port):
    event_loop = asyncio.get_event_loop()
    async def handler_ok(ws, _):
        try:
            while True:
                recv_msg = str_to_msg(await ws.recv())
                send_msg = msg_to_str(recv_msg.ref,
                                      recv_msg.join_ref,
                                      recv_msg.topic,
                                      PHOENIX_EVENT['REPLY'],
                                      {'status': 'ok', 'response': {}})
                await ws.send(send_msg)
        except websockets.exceptions.ConnectionClosed:
            pass
    async def run_client():
        async with Phoenix('ws://127.0.0.1:{}'.format(unused_tcp_port), loop=event_loop) as socket:
            async with socket.channel('/channel'):
                pass

    start_server = websockets.serve(handler_ok, '127.0.0.1', unused_tcp_port, loop=event_loop)
    server = event_loop.run_until_complete(start_server)

    event_loop.run_until_complete(run_client())
    server.close()
    event_loop.run_until_complete(server.wait_closed())

#
# def test_connection_refused(event_loop, unused_tcp_port):
#     with pytest.raises(ConnectionRefusedError):
#         async def run_client():
#             async with Socket('ws://localhost:{}'.format(unused_tcp_port), loop=event_loop) as socket:
#                 async with socket.channel('/channel'):
#                     pass
#
#         event_loop.run_until_complete(run_client())
#
#
# def test_connection_closed_from_server(event_loop, unused_tcp_port):
#     async def handler(_):
#         asyncio.sleep(0.5, loop=event_loop)
#
#     start_server = websockets.serve(handler, 'localhost', unused_tcp_port, loop=event_loop)
#     server = event_loop.run_until_complete(start_server)
#
#     async def run_client():
#         async with Socket('ws://localhost:{}'.format(unused_tcp_port), loop=event_loop) as socket:
#             async with socket.channel('/channel') as ch:
#                 await ch.push('event')
#
#     with pytest.raises(ConnectionClosed):
#         event_loop.run_until_complete(run_client())
#     server.close()
#     event_loop.run_until_complete(server.wait_closed())
#
#
# def test_first_message_become_lost(event_loop, unused_tcp_port):
#     async def handler_ignore_first_message(ws, _):
#         for i in range(3):
#             recv_msg = str_to_msg(await ws.recv())
#             if i == 0:
#                 continue
#
#             send_msg = msg_to_str(recv_msg.ref,
#                                   recv_msg.join_ref,
#                                   recv_msg.topic,
#                                   PHOENIX_EVENT['REPLY'],
#                                   {'status': 'ok', 'response': {}})
#             await ws.send(send_msg)
#
#     start_server = websockets.serve(handler_ignore_first_message, 'localhost', unused_tcp_port, loop=event_loop)
#     server = event_loop.run_until_complete(start_server)
#
#     async def run_client():
#         async with Socket('ws://localhost:{}'.format(unused_tcp_port), loop=event_loop) as socket:
#             async with socket.channel('/channel'):
#                 pass
#
#     event_loop.run_until_complete(run_client())
#     server.close()
#     event_loop.run_until_complete(server.wait_closed())
#
#
# def test_server_is_too_busy_1(event_loop, unused_tcp_port):
#     wait_forever = asyncio.Future(loop=event_loop)
#
#     async def handler_wait_forever(*_):
#         await wait_forever
#
#     async def run_client():
#         async with Socket('ws://localhost:{}'.format(unused_tcp_port), loop=event_loop) as socket:
#             async with socket.channel('/channel'):
#                 pass
#
#     with pytest.raises(CommunicationError):
#         start_server = websockets.serve(handler_wait_forever, 'localhost', unused_tcp_port, loop=event_loop)
#         server = event_loop.run_until_complete(start_server)
#         event_loop.run_until_complete(run_client())
#     server.close()
#     event_loop.run_until_complete(server.wait_closed())
#
#
# def test_server_is_too_busy_2(event_loop, unused_tcp_port):
#     wait_forever = asyncio.Future(loop=event_loop)
#
#     async def handler_wait_forever(*_):
#         await wait_forever
#
#     async def run_client():
#         async with Socket('ws://localhost:{}'.format(unused_tcp_port), loop=event_loop) as socket:
#             async with socket.channel('/channel'):
#                 asyncio.wait(0.5, loop=event_loop)
#
#     with pytest.raises(CommunicationError):
#         start_server = websockets.serve(handler_wait_forever, 'localhost', unused_tcp_port, loop=event_loop)
#         server = event_loop.run_until_complete(start_server)
#         event_loop.run_until_complete(run_client())
#     server.close()
#     event_loop.run_until_complete(server.wait_closed())
#
#
# def test_bad_response_1(event_loop, unused_tcp_port):
#     async def handler_ok(ws, _):
#         recv_msg = str_to_msg(await ws.recv())
#         send_msg = msg_to_str(recv_msg.ref,
#                               recv_msg.join_ref,
#                               recv_msg.topic,
#                               PHOENIX_EVENT['REPLY'],
#                               {'status': 'ok', 'response': {}})
#         await ws.send(send_msg)
#         await ws.send('[][][123123')
#
#         while True:
#             recv_msg = str_to_msg(await ws.recv())
#             send_msg = msg_to_str(recv_msg.ref,
#                                   recv_msg.join_ref,
#                                   recv_msg.topic,
#                                   PHOENIX_EVENT['REPLY'],
#                                   {'status': 'ok', 'response': {}})
#             await ws.send(send_msg)
#
#     start_server = websockets.serve(handler_ok, 'localhost', unused_tcp_port, loop=event_loop)
#     server = event_loop.run_until_complete(start_server)
#
#     async def run_client():
#         async with Socket('ws://localhost:{}'.format(unused_tcp_port), loop=event_loop) as socket:
#             async with socket.channel('/channel'):
#                 pass
#
#     event_loop.run_until_complete(run_client())
#     server.close()
#     event_loop.run_until_complete(server.wait_closed())
#
#
# def test_bad_response_2(event_loop, unused_tcp_port):
#     async def handler_ok(ws, _):
#         recv_msg = str_to_msg(await ws.recv())
#         send_msg = msg_to_str(recv_msg.ref,
#                               recv_msg.join_ref,
#                               recv_msg.topic,
#                               PHOENIX_EVENT['REPLY'],
#                               {'status': 'ok', 'response': {}})
#         await ws.send(send_msg)
#
#         await ws.recv()
#         await ws.send('[][][123123')
#
#         while True:
#             recv_msg = str_to_msg(await ws.recv())
#             send_msg = msg_to_str(recv_msg.ref,
#                                   recv_msg.join_ref,
#                                   recv_msg.topic,
#                                   PHOENIX_EVENT['REPLY'],
#                                   {'status': 'ok', 'response': {}})
#             await ws.send(send_msg)
#
#     start_server = websockets.serve(handler_ok, 'localhost', unused_tcp_port, loop=event_loop)
#     server = event_loop.run_until_complete(start_server)
#
#     async def run_client():
#         async with Socket('ws://localhost:{}'.format(unused_tcp_port), loop=event_loop) as socket:
#             async with socket.channel('/channel'):
#                 pass
#
#     event_loop.run_until_complete(run_client())
#     server.close()
#     event_loop.run_until_complete(server.wait_closed())
#
#
# def test_bad_payload(event_loop, unused_tcp_port):
#     async def handler_ok(ws, _):
#         await ws.recv()
#         breaked_msg = '{"join_ref": "1", "ref": "2", "topic": "/channel", "event": "phx_reply",' \
#                       '"payload": {"breaked" : "json", "timestamp": 1533884684264, "timeout": 10000}'
#         await ws.send(breaked_msg)
#
#         while True:
#             recv_msg = str_to_msg(await ws.recv())
#             send_msg = msg_to_str(recv_msg.ref,
#                                   recv_msg.join_ref,
#                                   recv_msg.topic,
#                                   PHOENIX_EVENT['REPLY'],
#                                   {'status': 'ok', 'response': {}})
#             await ws.send(send_msg)
#
#     start_server = websockets.serve(handler_ok, 'localhost', unused_tcp_port, loop=event_loop)
#     server = event_loop.run_until_complete(start_server)
#
#     async def run_client():
#         async with Socket('ws://localhost:{}'.format(unused_tcp_port), loop=event_loop) as socket:
#             async with socket.channel('/channel'):
#                 pass
#
#     event_loop.run_until_complete(run_client())
#     server.close()
#     event_loop.run_until_complete(server.wait_closed())
#
#
# def test_invalid_ref(event_loop, unused_tcp_port):
#     async def handler_ok(ws, _):
#         recv_msg = str_to_msg(await ws.recv())
#         send_msg = msg_to_str(100,
#                               recv_msg.join_ref,
#                               recv_msg.topic,
#                               PHOENIX_EVENT['REPLY'],
#                               {'status': 'ok', 'response': {}})
#         await ws.send(send_msg)
#
#         while True:
#             recv_msg = str_to_msg(await ws.recv())
#             send_msg = msg_to_str(recv_msg.ref,
#                                   recv_msg.join_ref,
#                                   recv_msg.topic,
#                                   PHOENIX_EVENT['REPLY'],
#                                   {'status': 'ok', 'response': {}})
#             await ws.send(send_msg)
#
#     start_server = websockets.serve(handler_ok, 'localhost', unused_tcp_port, loop=event_loop)
#     server = event_loop.run_until_complete(start_server)
#
#     async def run_client():
#         async with Socket('ws://localhost:{}'.format(unused_tcp_port), loop=event_loop) as socket:
#             async with socket.channel('/channel'):
#                 pass
#
#     event_loop.run_until_complete(run_client())
#     server.close()
#     event_loop.run_until_complete(server.wait_closed())
#
#
# def test_not_allowed_event(event_loop, unused_tcp_port):
#     async def handler_ok(ws, _):
#         while True:
#             recv_msg = str_to_msg(await ws.recv())
#             send_msg = msg_to_str(recv_msg.ref,
#                                   recv_msg.join_ref,
#                                   recv_msg.topic,
#                                   PHOENIX_EVENT['REPLY'],
#                                   {'status': 'ok', 'response': {}})
#             await ws.send(send_msg)
#
#     start_server = websockets.serve(handler_ok, 'localhost', unused_tcp_port, loop=event_loop)
#     server = event_loop.run_until_complete(start_server)
#
#     for key in PHOENIX_EVENT:
#         with pytest.raises(NotAllowedEventName):
#             async def run_client():
#                 async with Socket('ws://localhost:{}'.format(unused_tcp_port), loop=event_loop) as socket:
#                     async with socket.channel('/channel') as ch:
#                         await ch.push(PHOENIX_EVENT[key])
#
#             event_loop.run_until_complete(run_client())
#
#     server.close()
#     event_loop.run_until_complete(server.wait_closed())
#
#
# def test_channel_to_5_notification(event_loop, unused_tcp_port):
#     notice_cnt = 5
#
#     async def handler_ok(ws, _):
#         notice_coro = None
#         try:
#             while True:
#                 recv_msg = str_to_msg(await ws.recv())
#                 if recv_msg.event == PHOENIX_EVENT['JOIN']:
#                     async def notice():
#                         for i in range(notice_cnt):
#                             await ws.send(msg_to_str(None,
#                                                      None,
#                                                      '/channel',
#                                                      'notification',
#                                                      {"data": [{"data": [], "action": "init"}]}))
#                             await asyncio.sleep(0.01, loop=event_loop)
#
#                     notice_coro = asyncio.ensure_future(notice(), loop=event_loop)
#
#                 send_msg = msg_to_str(recv_msg.ref,
#                                       recv_msg.join_ref,
#                                       recv_msg.topic,
#                                       PHOENIX_EVENT['REPLY'],
#                                       {'status': 'ok', 'response': {}})
#                 await ws.send(send_msg)
#         except websockets.exceptions.ConnectionClosed:
#             if notice_coro:
#                 notice_coro.cancel()
#             pass
#
#     a_future = asyncio.Future(loop=event_loop)
#     a_future.done()
#     start_server = websockets.serve(handler_ok, 'localhost', unused_tcp_port, loop=event_loop)
#     server = event_loop.run_until_complete(start_server)
#
#     async def run_client():
#         cnt = 0
#         async with Socket('ws://localhost:{}'.format(unused_tcp_port), loop=event_loop) as socket:
#             async with socket.channel('/channel') as ch:
#                 while True:
#                     try:
#                         async with atimeout(0.5, loop=event_loop):
#                             await ch.receive()
#                             cnt += 1
#                     except asyncio.TimeoutError:
#                         break
#         assert cnt == notice_cnt
#
#     event_loop.run_until_complete(run_client())
#     server.close()
#     event_loop.run_until_complete(server.wait_closed())
#
#
# def test_notification(event_loop, unused_tcp_port):
#     num_topics = 10
#     num_notice = 5
#
#     async def handler_ok(ws, _):
#         notice_coro = []
#         topic = {}
#
#         try:
#             while True:
#                 recv_msg = str_to_msg(await ws.recv())
#                 if recv_msg.event == PHOENIX_EVENT['JOIN']:
#                     if recv_msg.topic not in topic:
#                         async def notice(topic):
#                             for i in range(num_notice):
#                                 await ws.send(msg_to_str(None,
#                                                          None,
#                                                          topic,
#                                                          'notification',
#                                                          {"data": [{"data": [], "action": "init"}]}))
#                                 await asyncio.sleep(0.01, loop=event_loop)
#
#                         notice_coro.append(asyncio.ensure_future(notice(recv_msg.topic), loop=event_loop))
#                 send_msg = msg_to_str(recv_msg.ref,
#                                       recv_msg.join_ref,
#                                       recv_msg.topic,
#                                       PHOENIX_EVENT['REPLY'],
#                                       {'status': 'ok', 'response': {}})
#                 await ws.send(send_msg)
#         except websockets.exceptions.ConnectionClosed:
#             for n in notice_coro:
#                 n.cancel()
#
#     a_future = asyncio.Future(loop=event_loop)
#     a_future.done()
#     start_server = websockets.serve(handler_ok, 'localhost', unused_tcp_port, loop=event_loop)
#     server = event_loop.run_until_complete(start_server)
#     cnt_q = asyncio.queues.Queue(num_topics * num_notice, loop=event_loop)
#
#     async def run_client():
#         joined = []
#         async with Socket('ws://localhost:{}'.format(unused_tcp_port), loop=event_loop) as socket:
#             for i in range(num_topics):
#                 async def joins(topic):
#                     async with socket.channel(topic) as ch:
#                         while True:
#                             try:
#                                 async with atimeout(0.5, loop=event_loop):
#                                     await ch.receive()
#                                     await cnt_q.put(1)
#                             except asyncio.TimeoutError:
#                                 break
#
#                 joined.append(asyncio.ensure_future(joins('/channel_{}'.format(i)), loop=event_loop))
#
#             await asyncio.wait(joined,
#                                loop=event_loop,
#                                return_when=asyncio.ALL_COMPLETED)
#
#     event_loop.run_until_complete(run_client())
#     server.close()
#     event_loop.run_until_complete(server.wait_closed())
#     assert cnt_q.qsize() == num_topics * num_notice
#
#
# @pytest.mark.parametrize('num_heartbeat, heartbeat_secs', [(10, 0.1), (20, 0.05)])
# def test_socket_heartbeat(num_heartbeat, heartbeat_secs, event_loop, unused_tcp_port):
#     import multiprocessing
#     m = multiprocessing.Manager()
#     variable = m.Value('i', 0)
#
#     async def handler_ok(ws, _):
#         while True:
#             recv_msg = str_to_msg(await ws.recv())
#             send_msg = msg_to_str(recv_msg.ref,
#                                   recv_msg.join_ref,
#                                   recv_msg.topic,
#                                   PHOENIX_EVENT['REPLY'],
#                                   {'status': 'ok', 'response': {}})
#             variable.value += 1
#             await ws.send(send_msg)
#
#     start_server = websockets.serve(handler_ok, 'localhost', unused_tcp_port, loop=event_loop)
#     server = event_loop.run_until_complete(start_server)
#
#     async def run_client():
#         async with Socket('ws://localhost:{}'.format(unused_tcp_port), loop=event_loop,
#                           heartbeat_secs=heartbeat_secs) as socket:
#             try:
#                 async with atimeout(heartbeat_secs * (1.5 * num_heartbeat), loop=socket.loop):
#                     run_forever = asyncio.Future(loop=socket.loop)
#                     await run_forever
#             except asyncio.TimeoutError:
#                 pass
#
#     event_loop.run_until_complete(run_client())
#     server.close()
#     event_loop.run_until_complete(server.wait_closed())
#
#     assert variable.value >= num_heartbeat
#
#
# def test_socket_disconnected(event_loop, unused_tcp_port):
#     async def handler_ok(ws, _):
#         while True:
#             try:
#                 async with atimeout(0.5, loop=ws.loop):
#                     recv_msg = str_to_msg(await ws.recv())
#                     send_msg = msg_to_str(recv_msg.ref,
#                                           recv_msg.join_ref,
#                                           recv_msg.topic,
#                                           PHOENIX_EVENT['REPLY'],
#                                           {'status': 'ok', 'response': {}})
#                     await ws.send(send_msg)
#             except asyncio.TimeoutError:
#                 break
#
#     start_server = websockets.serve(handler_ok, 'localhost', unused_tcp_port, loop=event_loop)
#     server = event_loop.run_until_complete(start_server)
#
#     async def run_client():
#         with pytest.raises(ConnectionClosed):
#             try:
#                 async with atimeout(1, loop=event_loop):
#                     async with Socket('ws://localhost:{}'.format(unused_tcp_port), loop=event_loop) as socket:
#                         async with socket.channel('/channel') as ch:
#                             await asyncio.sleep(10, loop=socket.loop)
#             except asyncio.TimeoutError:
#                 pass
#
#     event_loop.run_until_complete(run_client())
#     server.close()
#     event_loop.run_until_complete(server.wait_closed())
#
#
# def test_channel_join_before_connection(event_loop):
#     async def run_client():
#         with pytest.raises(CommunicationError):
#             socket = Socket('ws://localhost', loop=event_loop)
#             await socket.channel('api').join()
#
#     event_loop.run_until_complete(run_client())
#
#
# @pytest.mark.skip(reason="Not implemented")
# def test_channel_payload():
#     NotImplemented
#
#
# @pytest.mark.skip(reason="Not implemented")
# def test_channel_queue_size():
#     NotImplemented
#
#
# def test_channel_join_ref_when_failed_to_get_response(event_loop, unused_tcp_port):
#     async def handler_never_accept_to_join(ws, _):
#         try:
#             while True:
#                 try:
#                     recv_msg = str_to_msg(await ws.recv())
#                     send_msg = msg_to_str(recv_msg.ref,
#                                           recv_msg.join_ref,
#                                           recv_msg.topic,
#                                           PHOENIX_EVENT['REPLY'],
#                                           {'status': 'ok', 'response': {}})
#                     if recv_msg.event != PHOENIX_EVENT['JOIN']:
#                         await ws.send(send_msg)
#                 except asyncio.TimeoutError:
#                     break
#         except websockets.ConnectionClosed:
#             pass
#
#     start_server = websockets.serve(handler_never_accept_to_join, 'localhost', unused_tcp_port, loop=event_loop)
#     server = event_loop.run_until_complete(start_server)
#
#     async def run_client():
#         num_retry = 5
#         async with Socket('ws://localhost:{}'.format(unused_tcp_port), loop=event_loop) as socket:
#             with pytest.raises(CommunicationError):
#                 ch = socket.channel('channel', timeout_secs=1, num_retry=num_retry)
#                 await ch.join()
#             assert socket._ref == num_retry + 1
#
#     event_loop.run_until_complete(run_client())
#     server.close()
#     event_loop.run_until_complete(server.wait_closed())
#
#
# @pytest.mark.skip(reason="Not implemented")
# def test_socket_ref_round():
#     NotImplemented
#
#
# @pytest.mark.skip(reason="Not implemented")
# def test_socket_push_and_response():
#     NotImplemented
#
#
# @pytest.mark.skip(reason="Not implemented")
# def test_channel_double_join():
#     NotImplemented
#
#
# @pytest.mark.skip(reason="Not implemented")
# def test_channel_double_leave():
#     NotImplemented
