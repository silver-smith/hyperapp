from hyperapp.common.htypes import TList
from hyperapp.common.htypes.deduce_value_type import DeduceTypeError

from . import htypes
from .services import (
    deduce_t,
    pyobj_creg,
    )
from .code.marker_utils import (
    check_is_function,
    check_not_classmethod,
    is_cls_arg,
    fn_params,
    )
from .code.model_ctr import ModelCtr


class ModelProbe:

    def __init__(self, system_probe, ctr_collector, module_name, fn):
        self._system = system_probe
        self._ctr_collector = ctr_collector
        self._module_name = module_name
        self._fn = fn
        system_probe.add_global(self)

    def migrate_to(self, system_probe):
        self._system = system_probe
        self._ctr_collector = system_probe.resolve_service('ctr_collector')

    def __call__(self, *args, **kw):
        params = fn_params(self._fn)
        param_ofs = 0
        if args and is_cls_arg(self._fn, args[0]):
            # self._fn is a classmethod and args[0] is a 'cls' argument.
            param_ofs = 1
        param_values = {
            params[idx]: arg
            for idx, arg in enumerate(args)
            }
        param_values = {
            **param_values,
            **kw,
            }
        ctx_params = [
            *params[param_ofs:len(args)],
            *kw,
            ]
        service_params = [
            name for name in params[param_ofs:]
            if name not in ctx_params
            ]
        try:
            model = param_values['model']
        except KeyError:
            try:
                model = param_values['piece']
            except KeyError:
                self._raise_error(f"'model' or 'piece' argument is expected for model function: {list(param_values)}")
        model_t = deduce_t(model)
        service_kw = {
            name: self._system.resolve_service(name)
            for name in service_params
            }
        result = self._fn(*args, **kw, **service_kw)
        self._add_constructor(ctx_params, service_params, param_values, model_t, result)
        return result

    def _add_constructor(self, ctx_params, service_params, param_values, model_t, result):
        result_t = self._deduce_t(result, f"{self._fn}: Returned not a deducible data type: {result!r}")
        try:
            parent = param_values['parent']
        except KeyError:
            if isinstance(result_t, TList):
                ui_t = self._make_list_ui_t(result_t)
            else:
                assert 0, (result_t, model_t, ctx_params, service_params)  # not a tree or list model, TODO.
        else:
            ui_t = self._make_tree_ui_t(result_t, parent)
        ctr = ModelCtr(
            module_name=self._module_name,
            attr_qual_name=self._fn.__qualname__.split('.'),
            model_t=model_t,
            ui_t=ui_t,
            ctx_params=ctx_params,
            service_params=service_params,
            )
        self._ctr_collector.add_constructor(ctr)

    def _make_tree_ui_t(self, result_t, parent):
        if not isinstance(result_t, TList):
            self._raise_error(f"Tree model should return an item list: {result!r}")
        if parent is not None:
            parent_t = self._deduce_t(parent, f"{self._fn}: 'parent' parameter is not a deducible data type: {parent!r}")
            if parent_t is not result_t.element_t:
                self._raise_error(f"Parent type should match result list element type: parent: {parent_t}, result element: {result_t.element_t}")
        return htypes.model.tree_ui_t(
            element_t=pyobj_creg.actor_to_ref(result_t.element_t),
            )

    def _make_list_ui_t(self, result_t):
        return htypes.model.list_ui_t(
            element_t=pyobj_creg.actor_to_ref(result_t.element_t),
            )

    def _deduce_t(self, value, error_msg):
        try:
            return deduce_t(value)
        except DeduceTypeError:
            self._raise_error(error_msg)

    def _raise_error(self, error_msg):
        raise RuntimeError(f"{self._fn}: {error_msg}")


def model_marker(fn, module_name, system, ctr_collector):
    check_not_classmethod(fn)
    check_is_function(fn)
    return ModelProbe(system, ctr_collector, module_name, fn)
