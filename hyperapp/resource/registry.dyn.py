import inspect
import logging
from functools import partial

from hyperapp.common.htypes.meta_association import meta_association
from hyperapp.common.meta_association_type import MetaAssociationResourceType
from hyperapp.common.meta_registry_association import register_meta_association
from hyperapp.common.module import Module

from . import htypes
from .cached_code_registry import CachedCodeRegistry

_log = logging.getLogger(__name__)


def resource_type_producer(resource_type_factory, resource_type_reg, resource_t):
    try:
        return resource_type_reg[resource_t]
    except KeyError:
        return resource_type_factory(resource_t)


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

        services.resource_type_reg = {}  # resource_t -> ResourceType instance
        services.python_object_creg = CachedCodeRegistry('python_object', services.web, services.types)
        register_meta_association(services.meta_registry, services.python_object_creg)
        services.fn_to_ref = partial(fn_to_ref, services.mosaic, services.python_object_creg)
        services.resource_type_producer = partial(resource_type_producer, services.resource_type_factory, services.resource_type_reg)
        services.meta_registry.register_actor(
            htypes.impl.python_object_association, register_python_object, services.python_object_creg)
        services.resource_type_reg[meta_association] = MetaAssociationResourceType()
