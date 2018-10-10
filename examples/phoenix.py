import asyncio
import ssl
from datetime import datetime

import pytz

from pydaybit import Daybit, daybit_url, daybit_api_key, daybit_api_secret, PARAM_API_KEY, PARAM_API_SECRET
from pydaybit.phoenix import Phoenix

url = daybit_url()
params = {PARAM_API_KEY: daybit_api_key(),
          PARAM_API_SECRET: daybit_api_secret()}

print('url:', url)
print('params:', params)
print('')


def timestamp_to_datetime(timestamp_ms, tz=pytz.timezone('Asia/Seoul')):
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=tz)


async def phoenix_get_server_time():
    if url[:3] == 'wss':
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    else:
        ssl_context = None

    async with Phoenix(url, params, ssl=ssl_context) as socket:
        async with socket.channel('/api') as channel:
            msg = await channel.push('get_server_time', payload={})
            try:
                server_timestamp = msg['response']['data']['server_time']
                print('Socket: {} {}'.format(server_timestamp, timestamp_to_datetime(server_timestamp)))
            except KeyError:
                print('ParsingError: {}'.format(msg))


async def daybit_get_server_time():
    async with Daybit(url, params) as daybit:
        server_timestamp = await daybit.get_server_time()
        print('Daybit: {} {}'.format(server_timestamp, timestamp_to_datetime(server_timestamp)))


asyncio.get_event_loop().run_until_complete(phoenix_get_server_time())
asyncio.get_event_loop().run_until_complete(daybit_get_server_time())
