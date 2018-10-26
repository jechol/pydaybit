import os
name = "pydaybit"
DAYBIT_API_DEFAULT_URL = 'wss://api.daybit.com/v1/user_api_socket/websocket'
DAYBIT_API_KEY_VARIABLE = 'DAYBIT_API_KEY'
DAYBIT_API_SECRET_VARIABLE = 'DAYBIT_API_SECRET'

PARAM_API_KEY = 'api_key'
PARAM_API_SECRET = 'api_secret'


def daybit_url():
    return os.environ.get('DAYBIT_URL', DAYBIT_API_DEFAULT_URL)


def daybit_api_key():
    return os.environ.get(DAYBIT_API_KEY_VARIABLE, 'API_KEY_IS_NEEDED.')


def daybit_api_secret():
    return os.environ.get(DAYBIT_API_SECRET_VARIABLE, 'API_SECRET_IS_NEEDED.')


from pydaybit.daybit import Daybit
