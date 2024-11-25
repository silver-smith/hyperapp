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

    def __init__(self, system_probe, ctr_collector, data_to_res, module_name, action, fn):
        self._system = system_probe
        self._ctr_collector = ctr_collector
        self._data_to_res = data_to_res
        self._module_name = module_name
        self._action = action
        self._fn = fn
        system_probe.add_global(self)

    def migrate_to(self, system_probe):
        self._system = system_probe
        self._ctr_collector = system_probe.resolve_service('ctr_collector')
        self._data_to_res = system_probe.resolve_service('data_to_res')

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

    def _pick_key_field(self, item_t, params):
        fields = []
        expected_fields = ", ".join(item_t.fields)
        for name in params.other_names:
            if name in {'piece', 'model', 'value'}:
                continue
            if name not in item_t.fields:
                raise RuntimeError(f"Unexpected parameter: {name!r}. Expected key field, one of {expected_fields}")
            fields.append(name)
        if not fields:
            raise RuntimeError(f"Expected one key parameter. One of {expected_fields}")
        if len(fields) > 1:
            fields_str = ", ".join(fields)
            raise RuntimeError(f"Only one key parameter is expected, but got: {fields_str}")
        return fields[0]

    def _template_ctr_kw(self, params):
        model_field, model_t = self._deduce_piece_t(params, ['piece', 'model'])
        ui_t = self._pick_model_ui_t(model_t)
        item_t = self._get_item_t(ui_t)
        key_field = self._pick_key_field(item_t, params)
        return dict(
            data_to_res=self._data_to_res,
            module_name=self._module_name,
            attr_qual_name=self._fn.__qualname__.split('.'),
            model_t=model_t,
            action=self._action,
            key_field=key_field,
            crud_params=params.other_names,
            service_params=params.service_names,
            )

    def _add_constructor(self, params, result):
        if self._action == 'get':
            ctr = self._init_constructor(params, result)
        elif self._action == 'update':
            ctr = self._commit_constructor(params)
        else:
            raise RuntimeError(f"Action {self._action!r} is not yet supported")
        self._ctr_collector.add_constructor(ctr)

    def _init_constructor(self, params, result):
        result_t = deduce_t(result)
        if not isinstance(result_t, TRecord):
            raise RuntimeError(f"Result of {self._action} action should be a record, but is: {result_t}")
        return CrudInitTemplateCtr(
            **self._template_ctr_kw(params),
            record_t=result_t,
            )

    def _commit_constructor(self, params):
        return CrudCommitTemplateCtr(
            **self._template_ctr_kw(params),
            )


class CrudDecorator:

    def __init__(self, system_probe, ctr_collector, data_to_res, module_name, action):
        self._system = system_probe
        self._ctr_collector = ctr_collector
        self._data_to_res = data_to_res
        self._module_name = module_name
        self._action = action

    def __call__(self, fn):
        check_not_classmethod(fn)
        check_is_function(fn)
        return CrudProbe(self._system, self._ctr_collector, self._data_to_res, self._module_name, self._action, fn)


class CrudMarker:

    def __init__(self, module_name, system, ctr_collector, data_to_res):
        self._module_name = module_name
        self._system = system
        self._ctr_collector = ctr_collector
        self._data_to_res = data_to_res

    def __getattr__(self, action):
        return CrudDecorator(self._system, self._ctr_collector, self._data_to_res, self._module_name, action)
