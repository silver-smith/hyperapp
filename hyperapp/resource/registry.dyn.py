import inspect
import logging
from functools import partial

from hyperapp.common.htypes.meta_association import meta_association
from hyperapp.common.meta_association_type import MetaAssociationResourceType
from hyperapp.common.module import Module

from . import htypes

_log = logging.getLogger(__name__)


def register_python_object(piece, python_object_creg):
    t = python_object_creg.invite(piece.t)
    function = python_object_creg.invite(piece.function)
    _log.info("Register python object: %s -> %s", t, function)
    python_object_creg.register_actor(t, function)


def fn_to_ref(mosaic, python_object_creg, fn):
    module = inspect.getmodule(fn)
    module_res = python_object_creg.reverse_resolve(module)
    fn_res = htypes.attribute.attribute(
        object=mosaic.put(module_res),
        attr_name=fn.__name__,
        )
    return mosaic.put(fn_res)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.fn_to_ref = partial(fn_to_ref, services.mosaic, services.python_object_creg)
        services.meta_registry.register_actor(
            htypes.impl.python_object_association, register_python_object, services.python_object_creg)
        services.resource_type_reg[meta_association] = MetaAssociationResourceType()
