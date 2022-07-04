import inspect
import logging
import types

from hyperapp.common.htypes import TList, TRecord
from hyperapp.common.htypes.deduce_value_type import DeduceTypeError, deduce_complex_value_type

from . import htypes

log = logging.getLogger(__name__)


class Runner:

    def __init__(self, mosaic, types, python_object_creg):
        self._mosaic = mosaic
        self._types = types
        self._python_object_creg = python_object_creg

    def collect_attributes(self, request, object_ref):
        log.info("Collect attributes: %s", object_ref)
        object = self._python_object_creg.invite(object_ref)
        return list(self._iter_callables(object))

    def _iter_callables(self, object):
        for name in dir(object):
            if name.startswith('_'):
                continue
            value = getattr(object, name)
            if not callable(value):
                continue
            if not hasattr(value, '__module__'):
                continue  # 'partial' does not have it; may be others too.
            if type(object) is types.ModuleType and value.__module__ != object.__name__:
                continue  # Skip functions imported from other modules.
            try:
                signature = inspect.signature(value)
            except ValueError as x:
                if 'no signature found for builtin type' in str(x):
                    continue
                raise
            param_list = list(signature.parameters.keys())
            yield htypes.inspect.attr(name, param_list)


    def get_resource_type(self, request, resource_ref):
        log.info("Get type for resource: %s", resource_ref)
        value = self._python_object_creg.invite(resource_ref)

        if value is None:
            return htypes.inspect.none_t()

        log.info("Get type for value: %r", value)
        try:
            t = deduce_complex_value_type(self._mosaic, self._types, value)
        except DeduceTypeError:
            log.info("Non-data type: %r", value.__class__.__name__)
            return htypes.inspect.object_t(
                class_name=value.__class__.__name__,
                )

        log.info("Type is: %r", t)

        if isinstance(t, TRecord):
            type_name = htypes.inspect.type_name(t.module_name, t.name)
            return htypes.inspect.record_t(
                type=type_name,
            )

        if isinstance(t, TList) and isinstance(t.element_t, TRecord):
            element_list = []
            for name, field_t in t.element_t.fields.items():
                type_name = htypes.inspect.type_name(field_t.module_name, field_t.name)
                element = htypes.inspect.item_element(name, type_name)
                element_list.append(element)
            return htypes.inspect.list_t(
                element_list=element_list,
                )
