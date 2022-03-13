import inspect
import logging

from hyperapp.common.htypes import TList, TRecord
from hyperapp.common.htypes.deduce_value_type import deduce_complex_value_type

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
            try:
                signature = inspect.signature(value)
            except ValueError as x:
                if 'no signature found for builtin type' in str(x):
                    continue
                raise
            param_list = list(signature.parameters.keys())
            yield htypes.htest.attr(name, param_list)


    def get_function_result_type(self, request, function_ref, *args):
        log.info("Get function result type: %s", function_ref)
        fn = self._python_object_creg.invite(function_ref)
        result = fn(*args)
        log.info("Get function result type result: %r", result)
        t = deduce_complex_value_type(self._mosaic, self._types, result)
        log.info("Get function result type result t: %r", t)
        if isinstance(t, TList) and isinstance(t.element_t, TRecord):
            return htypes.htest.list_t(
                attr_name_list=list(t.element_t.fields),
                )
