from hyperapp.common.cached_code_registry import CachedCodeRegistry

from .services import (
    association_reg,
    mark,
    mosaic,
    pyobj_creg,
    types,
    web,
    )


@mark.service
def feed_creg():
    return CachedCodeRegistry(mosaic, web, types, association_reg, pyobj_creg, 'feed')
