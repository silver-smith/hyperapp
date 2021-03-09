import pytest

from hyperapp.client.async_application import AsyncApplication


# Required to exist when creating gui objects.
@pytest.fixture
def application():
    app = AsyncApplication()
    yield app
    app.shutdown()
