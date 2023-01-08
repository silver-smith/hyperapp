from . import htypes
from .services import (
    mark,
    mosaic,
    python_object_creg,
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
    t_res = python_object_creg.reverse_resolve(htypes.constructor_creg_fixtures.sample_type)
    return htypes.constructor_creg.constructor_creg_association(
        t=mosaic.put(t_res),
        fn=mosaic.put(fn_res),
        )
