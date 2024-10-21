from .services import (
    cached_code_registry_ctr,
    mosaic,
    web,
    )
from .code.mark import mark


@mark.service2
def feed_creg(config):
    return cached_code_registry_ctr('feed_creg', config)
