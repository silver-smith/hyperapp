from . import htypes
from .services import (
  mosaic,
  types,
  resource_registry,
  )
from .marker import param


@param.register_constructor
def piece():
    return htypes.constructor_creg.constructor_creg_association(
        t=types.reverse_resolve(htypes.constructor_creg_fixtures.sample_type),
        fn=mosaic.put(resource_registry['resource.constructor_creg.fixtures.aux', 'sample_function']),
        )
