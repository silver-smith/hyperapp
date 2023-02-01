import inspect
import logging
from types import ModuleType

from hyperapp.common.htypes import TList, TRecord
from hyperapp.common.htypes.deduce_value_type import DeduceTypeError, deduce_complex_value_type

from . import htypes
from .services import (
    mosaic,
    types,
    python_object_creg,
    )
from .constants import RESOURCE_NAMES_ATTR, RESOURCE_CTR_ATTR

log = logging.getLogger(__name__)


def collect_attributes(object_ref):
    log.info("Collect attributes: %s", object_ref)
    object = python_object_creg.invite(object_ref)
    attr_list = [
        mosaic.put(attr) for attr
        in _iter_attributes(object)
        ]
    if isinstance(object, ModuleType):
        object_module = object.__name__
    else:
        object_module = object.__module__
    return htypes.inspect.object_attributes(object_module, attr_list)


def _iter_attributes(object):
    name_to_res_name = getattr(object, RESOURCE_NAMES_ATTR, {})
    name_to_ctr_list = getattr(object, RESOURCE_CTR_ATTR, {})
    for name in dir(object):
        if name.startswith('_'):
            continue
        resource_name = name_to_res_name.get(name)
        constructors = name_to_ctr_list.get(name, [])
        value = getattr(object, name)
        if not resource_name:
            if not hasattr(value, '__module__'):
                continue  # 'partial' does not have it; may be others too.
            if type(object) is ModuleType and value.__module__ != object.__name__:
                continue  # Skip functions imported from other modules.
        if not callable(value):
            yield htypes.inspect.attr(name, getattr(value, '__module__', None), resource_name, constructors)
            continue
        try:
            signature = inspect.signature(value)
        except ValueError as x:
            if 'no signature found for builtin type' in str(x):
                continue
            raise
        param_list = list(signature.parameters.keys())
        yield htypes.inspect.fn_attr(name, value.__module__, resource_name, constructors, param_list)


def get_resource_type(resource_ref):
    log.info("Get type for resource ref: %s", resource_ref)
    value = python_object_creg.invite(resource_ref)
    log.info("Resource value: %s", resource_ref)

    if value is None:
        return htypes.inspect.none_t()

    if inspect.iscoroutine(value):
        return htypes.inspect.coroutine_t()

    log.info("Get type for value: %r", value)
    try:
        t = deduce_complex_value_type(mosaic, types, value)
    except DeduceTypeError:
        log.info("Non-data type: %r", value.__class__.__name__)
        return htypes.inspect.object_t(
            class_name=value.__class__.__name__,
            class_module=value.__class__.__module__,
            )

    log.info("Type is: %r", t)

    if isinstance(t, TRecord):
        type_name = htypes.inspect.type_name(t.module_name, t.name)
        return htypes.inspect.record_t(
            type=type_name,
        )

    if isinstance(t, TList) and not value:
        return htypes.inspect.empty_list_t()

    if isinstance(t, TList) and isinstance(t.element_t, TRecord):
        element_list = []
        for name, field_t in t.element_t.fields.items():
            type_name = htypes.inspect.type_name(field_t.module_name, field_t.name)
            element = htypes.inspect.item_element(name, type_name)
            element_list.append(element)
        return htypes.inspect.list_t(
            element_list=element_list,
            )
