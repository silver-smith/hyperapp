import inspect

from hyperapp.boot.htypes import TList, TRecord
from hyperapp.boot.htypes.deduce_value_type import DeduceTypeError

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
from .code.model_ctr import ModelCtr


class ModelProbe:

    def __init__(self, system_probe, ctr_collector, module_name, key, fn):
        self._system = system_probe
        self._ctr_collector = ctr_collector
        self._module_name = module_name
        self._key_field = key
        self._fn = fn
        system_probe.add_global(self)

    def migrate_to(self, system_probe):
        self._system = system_probe
        self._ctr_collector = system_probe.resolve_service('ctr_collector')

    def __call__(self, *args, **kw):
        params = split_params(self._fn, args, kw)
        try:
            model = params.values['model']
        except KeyError:
            try:
                model = params.values['piece']
            except KeyError:
                self._raise_error(f"'model' or 'piece' argument is expected for model function: {list(params.values)}")
        model_t = deduce_t(model)
        service_kw = {
            name: self._system.resolve_service(name)
            for name in params.service_names
            }
        result = self._fn(*args, **kw, **service_kw)
        if inspect.iscoroutine(result):
            async def await_result():
                real_result = await result
                self._add_constructor(params, model_t, real_result)
                return real_result
            return await_result()
        self._add_constructor(params, model_t, result)
        return result

    def _add_constructor(self, params, model_t, result):
        result_t = self._deduce_t(result, f"{self._fn}: Returned not a deducible data type: {result!r}")
        tree_params = {'parent'}
        if self._key_field:
            tree_params |= {'path'}
        if tree_params & set(params.ctx_names):
            ui_t = self._make_tree_ui_t(params, result_t)
        elif isinstance(result_t, TList):
            ui_t = self._make_list_ui_t(result_t)
        elif isinstance(result_t, TRecord):
            ui_t = self._make_record_ui_t(result_t)
        else:
            raise RuntimeError(f"Unknown model {model_t} type: {result_t!r}")
        ctr = ModelCtr(
            module_name=self._module_name,
            attr_qual_name=params.real_qual_name(self._fn),
            model_t=model_t,
            ui_t=ui_t,
            ctx_params=params.ctx_names,
            service_params=params.service_names,
            )
        self._ctr_collector.add_constructor(ctr)

    def _make_tree_ui_t(self, params, result_t):
        if not isinstance(result_t, TList):
            self._raise_error(f"Tree model should return an item list: {result!r}")
        self._check_parent_param(params, result_t)
        self._check_path_param(params, result_t)
        item_t = result_t.element_t
        if self._key_field:
            key_field_t = self._key_field_t(item_t)
            return htypes.model.key_tree_ui_t(
                item_t=pyobj_creg.actor_to_ref(item_t),
                key_field=self._key_field,
                key_field_t=pyobj_creg.actor_to_ref(key_field_t),
                )
        else:
            return htypes.model.index_tree_ui_t(
                item_t=pyobj_creg.actor_to_ref(item_t),
                )

    def _check_parent_param(self, params, result_t):
        try:
            parent = params.values['parent']
        except KeyError:
            return
        if parent is None:
            return
        parent_t = self._deduce_t(parent, f"{self._fn}: 'parent' parameter is not a deducible data type: {parent!r}")
        if parent_t is not result_t.element_t:
            self._raise_error(f"Parent type should match result list element type: parent: {parent_t}, result element: {result_t.element_t}")

    def _check_path_param(self, params, result_t):
        if not self._key_field:
            return
        try:
            path = params.values['path']
        except KeyError:
            return
        if type(path) not in (tuple, list):
            self._raise_error(f"Path parameter should have list type: {path!r}")
        if not path:
            return
        path_t = self._deduce_t(path, f"{self._fn}: 'path' parameter is not a deducible data type: {path!r}")
        if path_t.element_t is not self._key_field_t:
            self._raise_error(
                f"Path element type should match key field type:"
                f" path element type: {path_t.element_t}, key field type: {self.key_field_t}"
                )

    def _make_list_ui_t(self, result_t):
        item_t = result_t.element_t
        if self._key_field:
            key_field_t = self._key_field_t(item_t)
            return htypes.model.key_list_ui_t(
                item_t=pyobj_creg.actor_to_ref(item_t),
                key_field=self._key_field,
                key_field_t=pyobj_creg.actor_to_ref(key_field_t),
                )
        else:
            return htypes.model.index_list_ui_t(
                item_t=pyobj_creg.actor_to_ref(item_t),
                )

    def _key_field_t(self, item_t):
        try:
            return item_t.fields[self._key_field]
        except KeyError:
            item_fields = ", ".join(item_t.fields)
            raise RuntimeError(f"Key field {self._key_field!r} is not among item fields: {item_fields}")

    def _make_record_ui_t(self, result_t):
        return htypes.model.record_ui_t(
            record_t=pyobj_creg.actor_to_ref(result_t),
            )

    def _deduce_t(self, value, error_msg):
        try:
            return deduce_t(value)
        except DeduceTypeError:
            self._raise_error(error_msg)

    def _raise_error(self, error_msg):
        raise RuntimeError(f"{self._fn}: {error_msg}")


class ModelDecorator:

    def __init__(self, system, ctr_collector, module_name, key):
        self._system = system
        self._ctr_collector = ctr_collector
        self._module_name = module_name
        self._key = key

    def __call__(self, fn):
        check_not_classmethod(fn)
        check_is_function(fn)
        return ModelProbe(self._system, self._ctr_collector, self._module_name, self._key, fn)


class ModelMarker:

    def __init__(self, module_name, system, ctr_collector):
        self._module_name = module_name
        self._system = system
        self._ctr_collector = ctr_collector

    def __call__(self, fn=None, *, key=None):
        if fn is None:
            return ModelDecorator(self._system, self._ctr_collector, self._module_name, key)
        if key is not None:
            raise RuntimeError(f"Model decorator does not support positional arguments")
        check_not_classmethod(fn)
        check_is_function(fn)
        return ModelProbe(self._system, self._ctr_collector, self._module_name, key=None, fn=fn)
