import logging
from dataclasses import dataclass

from .services import (
    mark,
    )
from .tested.code import sample_service as sample_service_module

log = logging.getLogger(__name__)


@dataclass
class SampleFixture:
    value: str


@mark.fixture
def simple_fixture():
    log.info("Simple fixture")
    return SampleFixture("simple")


@mark.fixture
def fn_fixture(simple_fixture, sample_service, param_1, param_2, param_3):
    log.info("Fn fixture: simple_fixture=%r sample_service=%r", simple_fixture.value, sample_service.value)
    return f"fn fixture: {param_1} / {param_2} / {param_3}"


@mark.fixture
def value_fixture(fn_fixture):
    log.info("Fixture 1: fn_fixture=%r", fn_fixture)
    result = fn_fixture("val-1", "val-2", param_3="val-3")
    return SampleFixture(f"value fixture: fn result={result}")


def test_sample_service(value_fixture):
    log.info("test_sample_service: value_fixture=%r", value_fixture.value)
