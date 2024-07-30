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
def sample_config_service(config):
    log.info("Sample config service: config=%r", config)
    return SampleService("sample_service value")
