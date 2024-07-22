from .services import (
    mark,
    )
from .tested.code import sample_service as sample_service_module


@mark.fixture
def fixture_1():
    pass


def test_sample_service(fixture_1):
    pass
