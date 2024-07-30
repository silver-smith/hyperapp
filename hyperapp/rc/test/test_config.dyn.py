import logging
from dataclasses import dataclass

from . import htypes
from .services import (
    mark,
    )
from .tested.code import sample_config

log = logging.getLogger(__name__)


@dataclass
class SampleFixture:
    value: str


@mark.fixture
def simple_fixture():
    log.info("Simple fixture")
    return SampleFixture("simple")


@mark.config_item_fixture('sample_config_service')
def config_item_1(simple_fixture):
    return {
        htypes.sample_config.sample_key: htypes.sample_config.sample_item(12345),
        }


def test_service(sample_config_service):
    log.info("test_service: sample_config_service=%r", sample_config_service.value)
