import pytest

from hyperapp.client.async_application import AsyncApplication


# required to exist when creating gui objects
@pytest.fixture(scope='session')
def application():
    return AsyncApplication()
