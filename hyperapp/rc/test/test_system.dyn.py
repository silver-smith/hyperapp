import logging

from .services import (
    mark,
    )
from .tested.code import sample_service as sample_service_module

log = logging.getLogger(__name__)


@mark.fixture
def fixture_1():
    log.info("Fixture 1")
    return "fixture 1 value"


def test_sample_service(fixture_1):
    log.info("test_sample_service: fixture_1=%r", fixture_1)
