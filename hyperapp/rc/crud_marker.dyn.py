from hyperapp.common.htypes import TRecord

from . import htypes
from .services import (
    deduce_t,
    pyobj_creg,
    )
from .code.marker_utils import (
    check_is_function,
    check_not_classmethod,
    split_params,
    )
from .code.crud_ctr import CrudInitTemplateCtr, CrudCommitTemplateCtr


class CrudProbe:

    def __init__(self, system_probe, ctr_collector, module_name, action, fn, commit_action):
        self._system = system_probe
        self._ctr_collector = ctr_collector
        self._module_name = module_name
        self._action = action
        self._fn = fn
        self._commit_action = commit_action
        system_probe.add_global(self)

    def migrate_to(self, system_probe):
        self._system = system_probe
        self._ctr_collector = system_probe.resolve_service('ctr_collector')

    def __call__(self, *args, **kw):
        params = split_params(self._fn, args, kw)
        service_kw = {
            name: self._system.resolve_service(name)
            for name in params.service_names
            }
        result = self._fn(*args, **kw, **service_kw)
        self._add_constructor(params, result)
        return result

    def _deduce_piece_t(self, params, name_list):
        for name in name_list:
            try:
                piece = params.values[name]
                break
            except KeyError:
                pass
        else:
            names_str = " or ".join(name_list)
            self._raise_error(f"{names_str} argument is expected for CRUD function: {list(params.values)}")
        return (name, deduce_t(piece))

    def _pick_model_ui_t(self, model_t):
        visualizer_reg = self._system['visualizer_reg']
        ui_t, fn_ref = visualizer_reg(model_t)
        return ui_t

    @staticmethod
    def _get_item_t(ui_t):
        if (isinstance(ui_t, htypes.model.list_ui_t)
            or isinstance(ui_t, htypes.model.tree_ui_t)):
            item_t = pyobj_creg.invite(ui_t.item_t)
        else:
            raise RuntimeError(f"Not supported model UI type: {ui_t}. Only list and tree are supported")
        if not isinstance(item_t, TRecord):
            raise RuntimeError(f"Model item type is expected to be a record: {item_t}")
        return item_t

    def _pick_key_fields(self, item_t, params):
        fields = []
        for name in params.ctx_names:
            if name in {'piece', 'model', 'value'}:
                continue
            if name in item_t.fields:
                fields.append(name)
        if not fields:
            expected_fields = ", ".join(item_t.fields)
            raise RuntimeError(f"Expected at least one key parameter, one of: {expected_fields}")
        return fields

    def _template_ctr_kw(self, params):
        model_field, model_t = self._deduce_piece_t(params, ['piece', 'model'])
        ui_t = self._pick_model_ui_t(model_t)
        item_t = self._get_item_t(ui_t)
        key_fields = self._pick_key_fields(item_t, params)
        return dict(
            module_name=self._module_name,
            attr_qual_name=self._fn.__qualname__.split('.'),
            model_t=model_t,
            action=self._action,
            key_fields=tuple(key_fields),
            ctx_params=params.ctx_names,
            service_params=params.service_names,
            )

    def _add_constructor(self, params, result):
        if self._action == 'get' or self._commit_action:
            ctr = self._init_constructor(params, result)
        else:
            # Note: All actions which is not 'get' and does not have commit_action defined treated as commit actions.
            ctr = self._commit_constructor(params)
        self._ctr_collector.add_constructor(ctr)

    def _init_constructor(self, params, result):
        result_t = deduce_t(result)
        if not isinstance(result_t, TRecord):
            raise RuntimeError(f"Result of {self._action} action should be a record, but is: {result_t}")
        return CrudInitTemplateCtr(
            **self._template_ctr_kw(params),
            commit_action=self._commit_action,
            value_t=result_t,
            )

    def _commit_constructor(self, params):
        return CrudCommitTemplateCtr(
            **self._template_ctr_kw(params),
            )


class CrudDecorator:

    def __init__(self, system_probe, ctr_collector, module_name, action, commit_action=None):
        self._system = system_probe
        self._ctr_collector = ctr_collector
        self._module_name = module_name
        self._action = action
        self._commit_action = commit_action

    def __call__(self, fn=None, *, commit_action=None):
        if fn is None:
            if self._commit_action:
                raise RuntimeError(f"Single argument, function is expected for CRUD decorator")
            return CrudDecorator(self._system, self._ctr_collector, self._module_name, self._action, commit_action)
        check_not_classmethod(fn)
        check_is_function(fn)
        return CrudProbe(self._system, self._ctr_collector, self._module_name, self._action, fn, self._commit_action)


class CrudMarker:

    def __init__(self, module_name, system, ctr_collector):
        self._module_name = module_name
        self._system = system
        self._ctr_collector = ctr_collector

    def __getattr__(self, action):
        return CrudDecorator(self._system, self._ctr_collector, self._module_name, action)
