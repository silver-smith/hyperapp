from .services import (
    cached_code_registry_ctr,
    )
from .code.mark import mark


@mark.service
def feed_type_creg(config):
    return cached_code_registry_ctr('feed_type_creg', config)
