import collections
import json
import time
from pydaybit.phoenix.exceptions import InvalidMessage

PHOENIX_EVENT = {
    'CLOSE': 'phx_close',
    'ERROR': 'phx_error',
    'JOIN': 'phx_join',
    'REPLY': 'phx_reply',
    'LEAVE': 'phx_leave',
}


class Message(collections.namedtuple('Message', ['join_ref', 'ref', 'topic', 'event', 'payload'])):
    pass


class OutMessage(
    collections.namedtuple('Message', ['join_ref', 'ref', 'topic', 'event', 'payload', 'timeout'])):
    def asdict(self):
        return self._asdict()


def str_to_msg(str):
    resp = json.loads(str)
    try:
        message = Message(resp.get('join_ref', None),
                          resp.get('ref', None),
                          resp.get('topic', None),
                          resp.get('event', None),
                          resp.get('payload', None))
    except json.decoder.JSONDecodeError:
        raise InvalidMessage
    return message


def msg_to_str(ref, join_ref, topic, event, payload, timeout=3000):
    if payload is None:
        payload = {}
    payload['timestamp'] = int(time.time() * 1000)
    msg = json.dumps(OutMessage(topic=topic,
                                event=event,
                                payload=payload,
                                ref=ref,
                                join_ref=join_ref,
                                timeout=timeout).asdict())
    return msg
