from hyperapp.common.code_registry import CodeRegistry

from .services import (
    mark,
    python_object_creg,
    resource_registry,
    types,
    web,
    )


def register_constructor(piece):
    t = python_object_creg.invite(piece.t)
    fn = python_object_creg.invite(piece.fn)

    constructor_creg_res = resource_registry['resource.constructor_creg', 'constructor_creg.service']
    constructor_creg = python_object_creg.animate(constructor_creg_res)

    constructor_creg.register_actor(t, fn)


@mark.service
def constructor_creg():
    return CodeRegistry('resource_ctr', web, types)
