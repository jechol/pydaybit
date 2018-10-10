import asyncio
import time
from collections import deque


class RateLimit:
    def __init__(self, loop=None, tick=None):
        self._time_logs = {}
        self._limit = {}
        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop
        self.latest = 0
        if tick is None:
            tick = 0.0
        self.tick = tick

    def add_limit(self, key, limit):
        self._time_logs[key] = deque()
        self._limit[key] = limit

    async def wait(self, key):
        try:
            q = self._time_logs[key]
            limit = self._limit[key]
            current = time.time()

            if len(q) == limit:
                if current - q[0] <= 1:
                    await asyncio.sleep(q[0] + 1 - current, loop=self.loop)
                else:
                    q.popleft()
            else:
                delta = current - self.latest
                if delta < self.tick:
                    await asyncio.sleep(self.tick - delta, loop=self.loop)
            self.latest = time.time()
            q.append(self.latest)
        except KeyError:
            pass

    def get_limit(self, key):
        return self._limit[key]
