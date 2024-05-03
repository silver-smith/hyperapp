import logging
from collections import defaultdict
from dataclasses import dataclass
from functools import cached_property
from typing import Any

from hyperapp.common.htypes import TRecord

from . import htypes
from .services import (
    types,
    web,
    )

log = logging.getLogger(__name__)


class TypeCaseBase:

    def is_builtin_type(self, type_name):
        return self._t == htypes.inspect.object_t('builtins', type_name)

    @cached_property
    def is_data(self):
        return isinstance(self._t, htypes.inspect.data_t)

    @cached_property
    def data_t(self):
        assert self.is_data
        return types.resolve(self._t.t)

    @cached_property
    def data_t_ref(self):
        assert self.is_data
        return self._t.t


class TypeCase(TypeCaseBase):

    def __init__(self, t):
        self._t = t

    def __repr__(self):
        desc = f"{self._t} is_data={self.is_data}"
        if self.is_data:
            if self._t.t.hash_algorithm == 'phony':
                # Do not try to resolve phony refs in repr.
                desc += f" data_t={self._t.t}"
            else:
                desc += f" data_t={self.data_t!r}"
        return desc


class Type(TypeCaseBase):

    def __init__(self):
        self._t_set = set()

    def __repr__(self):
        desc = ", ".join(repr(case) for case in self.cases)
        return f"Type<{desc}>"

    @property
    def is_single(self):
        return len(self._t_set) == 1

    @property
    def count(self):
        return len(self._t_set)

    @cached_property
    def cases(self):
        return [TypeCase(t) for t in self._t_set]

    @cached_property
    def _t(self):
        try:
            [t] = self._t_set
            return t
        except ValueError:
            raise RuntimeError(f"Parameter has multiple types: {self.cases}")

    def add_type(self, t):
        if t in self._t_set:
            return
        self._t_set.add(t)
        for attr in ['is_data', 'data_t', 'data_t_ref', 'cases', '_t']:
            try:
                delattr(self, attr)
            except AttributeError:
                pass  # Cached property is not called yet.


class FnInfo:

    def __init__(self, trace):
        self.name = trace.fn_qual_name.split('.')
        self.module_name = trace.module
        self.line_no = trace.line_no
        self.obj_type = trace.obj_type
        self.result = Type()
        self.params = {}  # name -> Type
        self._traces = []
        self.add_trace(trace)

    def __repr__(self):
        return f"<FnInfo {self.module_name!r}:{self.name!r} obj_type={self.obj_type!r} result={self.result!r} params={dict(self.params)!r}>"

    @property
    def param_names(self):
        return list(self.params)

    def add_trace(self, trace):
        params = {
            p.name: web.summon(p.t)
            for p in trace.params
            }
        result_t = web.summon(trace.result_t)
        log.info("Call trace: %s:%d: %s %s (%s) -> %s",
                 trace.module, trace.line_no, trace.fn_qual_name, trace.obj_type or '-', params, result_t)
        assert self.line_no == trace.line_no
        assert self.module_name == trace.module
        assert self.obj_type == trace.obj_type
        for idx, (name, t) in enumerate(params.items()):
            if self.obj_type == 'classmethod' and idx == 0:
                continue  # Omit first, 'cls', parameter.
            try:
                param_type = self.params[name]
            except KeyError:
                param_type = Type()
                self.params[name] = param_type
            param_type.add_type(t)
        self.result.add_type(result_t)
        self._traces.append(trace)
