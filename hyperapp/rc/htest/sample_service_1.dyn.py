import logging
from dataclasses import dataclass

from .code.mark import mark

log = logging.getLogger(__name__)


@dataclass
class SampleService1:
    value: str


@mark.service
def sample_value_service_1():
    log.info("Sample value service 1")
    return SampleService1("sample_service_1 value")


@mark.service
def sample_fn_service_1(sample_value_service_1, param_1, param_2):
    log.info("Sample fn service 1: sample_value_service=%r param_1=%r param_2=%r", sample_value_service_1.value, param_1, param_2)
    return SampleService1("sample_service_1 value")
