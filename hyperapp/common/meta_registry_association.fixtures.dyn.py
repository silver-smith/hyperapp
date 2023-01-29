from hyperapp.common.code_registry import CodeRegistry

from . import htypes
from .services import (
    mark,
    mosaic,
    python_object_creg,
    resource_registry,
    types,
    web,
    )


def _sample_fn():
    pass


@mark.param.register_meta
def piece():
    t = htypes.meta_registry_association_fixtures.sample
    t_res = python_object_creg.reverse_resolve(t)
    this_module_res = resource_registry['common.meta_registry_association.fixtures', 'meta_registry_association.fixtures.module']
    fn_res = htypes.attribute.attribute(
        object=mosaic.put(this_module_res),
        attr_name='_sample_fn',
        )
    return htypes.meta_registry.meta_association(
        t=mosaic.put(t_res),
        fn=mosaic.put(fn_res),
        )


@mark.service
def meta_registry():
    return CodeRegistry('phony-meta', web, types)
