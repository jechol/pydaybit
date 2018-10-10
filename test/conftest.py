import pytest

from pydaybit import daybit_url, daybit_api_key, daybit_api_secret


@pytest.fixture
def daybit_params():
    return {'url': daybit_url(),
            'params': {
                'api_key': daybit_api_key(),
                'api_secret': daybit_api_secret()}
            }
