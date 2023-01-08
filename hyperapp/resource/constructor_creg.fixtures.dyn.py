from . import htypes
from .services import (
    mark,
    mosaic,
    types,
    resource_registry,
    )


@mark.param.register_constructor
def piece():
    module_res = resource_registry['resource.constructor_creg.fixtures.aux', 'constructor_creg.fixtures.aux.module']
    fn_res = htypes.attribute.attribute(
        object=mosaic.put(module_res),
        attr_name='sample_function',
        )
    return htypes.constructor_creg.constructor_creg_association(
        t=types.reverse_resolve(htypes.constructor_creg_fixtures.sample_type),
        fn=mosaic.put(fn_res),
        )
