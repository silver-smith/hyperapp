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
def sample_service():
    log.info("Sample service")
    return SampleService("sample_service value")
