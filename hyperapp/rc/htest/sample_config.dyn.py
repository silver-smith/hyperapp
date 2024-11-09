import logging
from dataclasses import dataclass

from . import htypes
from .code.mark import mark

log = logging.getLogger(__name__)


@dataclass
class SampleService:
    value: int


@mark.service
def sample_config_service(config):
    log.info("Sample config service: config=%r", config)
    value = config[htypes.sample_config.sample_key].value
    return SampleService(value)
