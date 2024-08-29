from hyperapp.common.cached_code_registry import CachedCodeRegistry

from .services import (
    mosaic,
    web,
    )
from .code.mark import mark


@mark.service2
def feed_creg(config):
    return CachedCodeRegistry(mosaic, web, 'feed', config)
