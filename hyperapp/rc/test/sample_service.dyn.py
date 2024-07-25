import logging
from dataclasses import dataclass

from .services import (
    mark,
    )

log = logging.getLogger(__name__)


@dataclass
class SampleService:
    value: str


@mark.service2
def sample_value_service():
    log.info("Sample value service")
    return SampleService("sample_service value")


@mark.service2
def sample_fn_service(sample_value_service, param_1, param_2):
    log.info("Sample fn service: sample_value_service=%r param_1=%r param_2=%r", sample_value_service.value, param_1, param_2)
    return SampleService("sample_service value")
