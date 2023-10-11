import inspect
import logging
import sys
from contextlib import contextmanager

from hyperapp.common.htypes import TPrimitive, TList, TRecord
from hyperapp.common.htypes.deduce_value_type import DeduceTypeError, deduce_complex_value_type, safe_repr

from . import htypes
from .services import (
    hyperapp_dir,
    mosaic,
    types,
    )
log = logging.getLogger(__name__)


def value_type(value):
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

    log.info("Type for %s is: %r", safe_repr(value), t)

    if isinstance(t, TPrimitive):
        return htypes.inspect.primitive_t(t.name)

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
        self._path_to_module = {
            str(hyperapp_dir.joinpath(name.replace('.', '/') + '.dyn.py')) : name
            for name in wanted_modules
            }
        self._original_tracer = None
        self._calls = []

    @property
    def calls(self):
        return self._calls

    @staticmethod
    def _pick_object(frame):
        code = frame.f_code
        if code.co_qualname.startswith(('<', '_')):
            return None
        l = code.co_qualname.split('.')
        obj = frame.f_globals.get(l[0])
        if obj is None:
            return None  # It is a class and it is not yet created?
        for n in l[1:]:
            if n.startswith(('<', '_')):
                return None
            obj = inspect.getattr_static(obj, n)
        return obj

    def trace(self, frame, event, arg):
        if self._original_tracer is not None:
            # Used by debugger (but still does not work).
            # See also: pydevd.GetGlobalDebugger().
            self._original_tracer(frame, event, arg)
        if event != 'call':
            return
        path = frame.f_code.co_filename
        module_name = self._path_to_module.get(path)
        if not module_name:
            return
        code = frame.f_code
        obj = self._pick_object(frame)
        args = inspect.getargvalues(frame)
        args_dict = {
            name: safe_repr(args.locals[name])
            for name in args.args
            }
        log.debug("Trace call: %s:%d %r: %s", module_name, code.co_firstlineno, code.co_qualname, repr(args_dict))
        args_types = {
            name: value_type(args.locals[name])
            for name in args.args
            }
        log.info("Trace call types: %s:%d %r: %s", module_name, code.co_firstlineno, code.co_qualname, repr(args_types))
        params = [
            htypes.inspect.call_param(name, mosaic.put(t))
            for name, t in args_types.items()
            ]
        self._calls.append(
            htypes.inspect.call_trace(
                module=module_name,
                line_no=code.co_firstlineno,
                fn_qual_name=code.co_qualname,
                obj_type=type(obj).__name__ if obj is not None else '',
                params=params,
                )
            )

    @contextmanager
    def tracing(self):
        self._original_tracer = sys.gettrace()
        sys.settrace(self.trace)
        try:
            yield
        finally:
            sys.settrace(self._original_tracer)
            self._original_tracer = None
