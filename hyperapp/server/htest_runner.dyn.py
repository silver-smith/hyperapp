import inspect
import logging

from . import htypes

log = logging.getLogger(__name__)


class Runner:

    def __init__(self, python_object_creg):
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
            yield htypes.htest.global_fn(name, param_list)
