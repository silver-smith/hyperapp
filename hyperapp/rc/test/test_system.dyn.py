import logging
from dataclasses import dataclass

from .services import (
    mark,
    )
from .tested.code import sample_service as sample_service_module

log = logging.getLogger(__name__)


@dataclass
class SampleService:
    value: str


@mark.fixture
def simple_fixture():
    log.info("Simple fixture")
    return SampleService("simple")


@mark.fixture
def fn_fixture(simple_fixture, param_1, param_2, param_3):
    log.info("Fn fixture: simple_fixture=%r", simple_fixture.value)
    return f"fn fixture: {param_1} / {param_2} / {param_3}"


@mark.fixture
def value_fixture(fn_fixture):
    log.info("Fixture 1: fn_fixture=%r", fn_fixture)
    result = fn_fixture("val-1", "val-2", param_3="val-3")
    return SampleService(f"value fixture: fn result={result}")


def test_sample_service(value_fixture):
    log.info("test_sample_service: value_fixture=%r", value_fixture.value)
