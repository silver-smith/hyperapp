import inspect
import logging
import sys
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType

from hyperapp.common.htypes import HException, TList, TRecord
from hyperapp.common.htypes.deduce_value_type import DeduceTypeError, deduce_complex_value_type, safe_repr

from . import htypes
from .services import (
    association_reg,
    hyperapp_dir,
    mosaic,
    types,
    python_object_creg,
    )
from .constants import RESOURCE_NAMES_ATTR, RESOURCE_CTR_ATTR

log = logging.getLogger(__name__)


def collect_attributes(object_ref):
    log.info("Collect attributes: %s", object_ref)
    try:
        object = python_object_creg.invite(object_ref)
    except HException as x:
        raise
    except RuntimeError as x:
        original_error = x
        while True:
            if not original_error.__context__:
                if (isinstance(original_error, TypeError)
                    and str(original_error) == '__init__() takes 3 positional arguments but 4 were given'):
                    # Class based on one imported from .code, which is DiscovererObject?
                    raise htypes.import_discoverer.using_incomplete_object(
                        "Suspected usage of incomplete base class for deriving from it")
                else:
                    raise
            original_error = original_error.__context__
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
        args = (name, value.__module__, resource_name, constructors, param_list)
        if inspect.isgeneratorfunction(value):
            yield htypes.inspect.generator_fn_attr(*args)
        else:
            yield htypes.inspect.fn_attr(*args)


def _value_type(value):
    if value is None:
        return htypes.inspect.none_t()

    if inspect.iscoroutine(value):
        return htypes.inspect.coroutine_t()

    log.debug("Get type for value: %s", safe_repr(value))
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
            if not isinstance(field_t, TRecord):
                # TODO: Just return meta type.
                log.warning("Non-record list element fields are not supported (field %r): %s", name, field_t)
                return None
            type_name = htypes.inspect.type_name(field_t.module_name, field_t.name)
            element = htypes.inspect.item_element(name, type_name)
            element_list.append(element)
        return htypes.inspect.list_t(
            element_list=element_list,
            )


class Tracer:

    def __init__(self, wanted_modules):
        self._wanted_paths = {
            str(hyperapp_dir.joinpath(name.replace('.', '/') + '.dyn.py'))
            for name in wanted_modules
            }
        self._original_tracer = None

    def trace(self, frame, event, arg):
        if self._original_tracer is not None:
            # Used by debugger (but still does not work).
            # See also: pydevd.GetGlobalDebugger().
            self._original_tracer(frame, event, arg)
        if event != 'call':
            return
        path = frame.f_code.co_filename
        if not path in self._wanted_paths:
            return
        code = frame.f_code
        args = inspect.getargvalues(frame)
        args_dict = {
            name: safe_repr(args.locals[name])
            for name in args.args
            }
        log.debug("Trace call: %s: %s", frame, repr(args_dict))
        args_types = {
            name: _value_type(args.locals[name])
            for name in args.args
            }
        log.debug("Trace call: types: %s", repr(args_types))

    @contextmanager
    def tracing(self):
        self._original_tracer = sys.gettrace()
        sys.settrace(self.trace)
        try:
            yield
        finally:
            sys.settrace(self._original_tracer)
            self._original_tracer = None


def get_resource_type(resource_ref, use_associations, tested_modules):
    log.info("Get type for resource ref: %s, tested modules: %s", resource_ref, tested_modules)

    with association_reg.associations_registered(use_associations):

        tracer = Tracer(tested_modules)
        with tracer.tracing():
            value = python_object_creg.invite(resource_ref)
            log.info("Resource value: %s", repr(value))

        if inspect.isgenerator(value):
            log.info("Expanding generator: %r", value)
            value = list(value)

        return _value_type(value)
