from hyperapp.common.cached_code_registry import CachedCodeRegistry

from .services import (
    association_reg,
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark


@mark.service
def feed_creg():
    return CachedCodeRegistry(mosaic, web, association_reg, pyobj_creg, 'feed')
