import inspect
import logging
import sys
from contextlib import contextmanager
from functools import partial

from hyperapp.common.htypes import TPrimitive, TList, TRecord
from hyperapp.common.htypes.deduce_value_type import DeduceTypeError, safe_repr

from . import htypes
from .services import (
    deduce_t,
    hyperapp_dir,
    mosaic,
    types,
    )
log = logging.getLogger(__name__)


def value_type(value):
    log.debug("Get type for value: %s", safe_repr(value))
    try:
        t = deduce_t(value)
    except DeduceTypeError:
        log.info("Non-data type: %r", value.__class__.__name__)
        if inspect.iscoroutine(value):
            t = htypes.inspect.coroutine_t()
        else:
            t = htypes.inspect.object_t(
                class_module=value.__class__.__module__,
                class_name=value.__class__.__name__,
                )
        log.info("Type for %s is non-data: %r", safe_repr(value), t)
        return t
    t_ref = types.reverse_resolve(t)
    return htypes.inspect.data_t(t_ref)


class Tracer:

    def __init__(self, wanted_modules):
        self._path_to_module = {
            str(hyperapp_dir.joinpath(name.replace('.', '/') + '.dyn.py')) : name
            for name in wanted_modules
            }
        # Used by debugger. See also: pydevd.GetGlobalDebugger().
        self._original_tracer = None
        self._traces = []

    @property
    def traces(self):
        return tuple(self._traces)

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

    def trace_return(self, module_name, arg_types, frame, event, arg):
        if self._original_tracer is not None:
            self._original_tracer(frame, event, arg)
        if event != 'return':
            return
        code = frame.f_code
        result_t = value_type(arg)
        obj = self._pick_object(frame)
        log.info("Trace call: %s:%d %r: %s -> [%s] %s",
                 module_name, code.co_firstlineno, code.co_qualname, repr(arg_types), result_t, repr(arg))
        params = tuple(
            htypes.inspect.call_param(name, mosaic.put(t))
            for name, t in arg_types.items()
            )
        self._traces.append(
            htypes.inspect.call_trace(
                module=module_name,
                line_no=code.co_firstlineno,
                fn_qual_name=code.co_qualname,
                obj_type=type(obj).__name__ if obj is not None else '',
                params=params,
                result_t=mosaic.put(result_t),
                )
            )

    def _fn_arg_types(self, frame):
        code = frame.f_code
        args = inspect.getargvalues(frame)
        return {
            name: value_type(args.locals[name])
            for name in args.args
            }

    def trace(self, frame, event, arg):
        if self._original_tracer is not None:
            self._original_tracer(frame, event, arg)
        if event != 'call':
            return self._original_tracer
        code = frame.f_code
        if '<locals>' in code.co_qualname or '<genexpr>' in code.co_qualname:
            return self._original_tracer
        path = code.co_filename
        module_name = self._path_to_module.get(path)
        if not module_name:
            return self._original_tracer
        arg_types = self._fn_arg_types(frame)
        return partial(self.trace_return, module_name, arg_types)

    @contextmanager
    def tracing(self):
        self._original_tracer = sys.gettrace()
        sys.settrace(self.trace)
        try:
            yield
        finally:
            sys.settrace(self._original_tracer)
            self._original_tracer = None
