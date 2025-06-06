import logging
from dataclasses import dataclass

from .code.mark import mark

log = logging.getLogger(__name__)


@dataclass
class SampleService:
    value: str


@mark.service
def sample_value_service_2(sample_fn_service_1):
    value = sample_fn_service_1('val-1-1', 'val-1-2')
    log.info("Sample value service 2: sample_fn_service_1=%r", value)
    return SampleService("sample_service_2 value")


@mark.service
def sample_fn_service_2(sample_value_service_2, param_1, param_2):
    log.info("Sample fn service 2: sample_value_service=%r param_1=%r param_2=%r", sample_value_service_2.value, param_1, param_2)
    return SampleService("sample_service_2 value")
