import logging

from hyperapp.common.htypes import TList, TRecord, tNone, tString
from hyperapp.common.association_registry import Association

from . import htypes
from .services import (
    data_to_res,
    mosaic,
    pyobj_creg,
    types,
    )
from .code.ui_ctr_constructor import Constructor
from .code.command_params import STATE_PARAMS, LOCAL_PARAMS

log = logging.getLogger(__name__)


class CommandImplementationCtr(Constructor):

    def check_applicable(self, fn_info):
        if len(fn_info.name) != 1:
            return f"Name has not 1 parts: {fn_info.name!r}"
        if fn_info.obj_type != 'function':
            return f"obj_type is not a 'function': {fn_info.obj_type!r}"
        if fn_info.constructors:
            # @mark.model decorator prevents a function from being a command.
            return f"Has constructors: {fn_info.constructors!r}"
        return None

    def _make_command_d_res(self, fn_name):
        d_attr = fn_name + '_d'
        try:
            command_d_ref = self._ctx.types[self._module_res.module_name][d_attr]
        except KeyError:
            raise RuntimeError(f"Create directory type: {self._module_res.module_name}.{d_attr}")
        command_d_t = types.resolve(command_d_ref)
        return data_to_res(command_d_t())

    def _make_properties(self, impl, is_global=False, uses_state=False, remotable=False):
        command_properties_d_res = data_to_res(htypes.ui.command_properties_d())
        properties = htypes.ui.command_properties(
            is_global=is_global,
            uses_state=uses_state,
            remotable=remotable,
            )
        association = Association(
            bases=[command_properties_d_res, impl],
            key=[command_properties_d_res, impl],
            value=properties,
            )
        return command_properties_d_res, properties, association


    def _make_fn_impl_properties(self, impl, is_global=False):
        return self._make_properties(
            impl, is_global,
            uses_state=bool(set(impl.params) & STATE_PARAMS),
            remotable=not set(impl.params) & LOCAL_PARAMS,
            )

    def _make_command(self, fn_info, fn_attribute, command_d_res):
        impl = htypes.ui.model_command_impl(
            function=mosaic.put(fn_attribute),
            params=tuple(fn_info.params),
            )
        command = htypes.ui.model_command(
            d=mosaic.put(command_d_res),
            impl=mosaic.put(impl),
            )
        return (impl, command)


class ModelCommandImplementationCtr(CommandImplementationCtr):

    @property
    def name(self):
        return "Model command"

    def check_applicable(self, fn_info):
        reason = super().check_applicable(fn_info)
        if reason:
            return reason
        for result in fn_info.result.cases:
            if not result.is_data:
                return f"Result case is not a data: {result!r}"
            result_is_accepted = (
                isinstance(result.data_t, TRecord) or
                isinstance(result.data_t, TList) and isinstance(result.data_t.element_t, TRecord) or
                result.data_t is tString or
                result.data_t is tNone
                )
            if not result_is_accepted:
                return f"Result is not a record, list of records, string or None: {result.data_t!r}"
        accepted_params = {'piece', 'model_state', 'current_idx', 'current_item', 'controller', 'ctx', 'lcs'}
        reason = self._check_accepted_params(fn_info, accepted_params)
        if reason:
            return reason
        if fn_info.param_names[:1] != ['piece']:
            return f"First param is not 'piece': {fn_info.param_names}"
        piece_t = fn_info.params['piece']
        if not piece_t.is_single:
            return f"Piece param has not one, but {piece_t.count} type variants: {piece_t.cases}"
        if not piece_t.is_data:
            return f"Piece param is not a data: {piece_t!r}"
        if not isinstance(piece_t.data_t, TRecord):
            return f"Piece param is not a record: {piece_t.data_t!r}"
        return None

    def construct(self, fn_info):
        fn_name = fn_info.name[0]
        fn_attribute = self._make_attribute(fn_name)
        command_d_res = self._make_command_d_res(fn_name)
        impl, command = self._make_command(fn_info, fn_attribute, command_d_res)
        command_properties_d_res, props, props_association = self._make_fn_impl_properties(impl)
        model_command_d_res = data_to_res(htypes.ui.model_command_d())
        piece_t = fn_info.params['piece']
        piece_t_res = htypes.builtin.legacy_type(piece_t.data_t_ref)
        association = Association(
            bases=[piece_t_res],
            key=[model_command_d_res, piece_t_res],
            value=command,
            )
        self._resource_module['model_command_d'] = model_command_d_res
        self._resource_module['command_properties_d'] = command_properties_d_res
        self._resource_module[fn_name] = fn_attribute
        self._resource_module[f'{fn_name}.d'] = command_d_res
        self._resource_module[f'{fn_name}.command_impl'] = impl
        self._resource_module[f'{fn_name}.command'] = command
        self._resource_module[f'{fn_name}.command_properties'] = props
        return {association, props_association}


class GlobalCommandImplementationCtr(CommandImplementationCtr):

    @property
    def name(self):
        return "Global command"

    def _check_is_record_list_or_str(self, case, name):
        if not case.is_data:
            return f"{name} case is not a data: {case!r}"
        is_accepted = (
            isinstance(case.data_t, TRecord) or
            isinstance(case.data_t, TList) and isinstance(case.data_t.element_t, TRecord) or
            case.data_t is tString
            )
        if not is_accepted:
            return f"{name} case is not a record, list of records or string: {case.data_t!r}"
        return None

    def check_applicable(self, fn_info):
        reason = super().check_applicable(fn_info)
        if reason:
            return reason
        for result in fn_info.result.cases:
            reason = self._check_is_record_list_or_str(result, "Result")
            if reason:
                return reason
        if 'piece' in fn_info.params:
            piece_t = fn_info.params['piece']
            if piece_t.is_single:
                return f"Function has 'piece' param, and it do not has multiple type cases: {piece_t!r}"
            for case in piece_t.cases:
                reason = self._check_is_record_list_or_str(case, "Piece param")
        accepted_params = {'piece', 'model_state', 'ctx', 'lcs'}
        reason = self._check_accepted_params(fn_info, accepted_params)
        if reason:
            return reason
        return None

    def construct(self, fn_info):
        fn_name = fn_info.name[0]
        fn_attribute = self._make_attribute(fn_name)
        command_d_res = self._make_command_d_res(fn_name)
        impl, command = self._make_command(fn_info, fn_attribute, command_d_res)
        command_properties_d_res, props, props_association = self._make_fn_impl_properties(impl)
        global_model_command_d_res = data_to_res(htypes.ui.global_model_command_d())
        association = Association(
            bases=[global_model_command_d_res],
            key=[global_model_command_d_res],
            value=command,
            )
        self._resource_module['global_model_command_d'] = global_model_command_d_res
        self._resource_module['command_properties_d'] = command_properties_d_res
        self._resource_module[fn_name] = fn_attribute
        self._resource_module[f'{fn_name}.d'] = command_d_res
        self._resource_module[f'{fn_name}.command_impl'] = impl
        self._resource_module[f'{fn_name}.command'] = command
        self._resource_module[f'{fn_name}.command_properties'] = props
        return {association, props_association}


class CommandEnumeratorImplementationCtr(Constructor):

    @property
    def name(self):
        return "Command enumerator"

    def check_applicable(self, fn_info):
        result = fn_info.result
        if not result.is_single:
            return f"Result has not one, but {result.count} type variants: {result.cases}"
        if not result.is_data:
            return f"Result is not a data: {result!r}"
        if not isinstance(result.data_t, TList):
            return f"Result is not a list: {result.data_t!r}"
        if not issubclass(result.data_t.element_t, htypes.ui.command):
            return f"Result element type is not a command: {result.data_t.element_t}"
        if fn_info.param_names[:1] != ['piece']:
            return f"First param is not 'piece': {fn_info.param_names}"
        accepted_params = {'piece', 'current_item', 'controller', 'lcs'}
        reason = self._check_accepted_params(fn_info, accepted_params)
        if reason:
            return reason
        piece_t = fn_info.params['piece']
        if not piece_t.is_single:
            return f"Piece param has not one, but {piece_t.count} type variants: {piece_t.cases}"
        if not piece_t.is_data:
            return f"Piece param is not a data: {piece_t!r}"
        if not isinstance(piece_t.data_t, TRecord):
            return f"Piece param is not a record: {piece_t.data_t!r}"
        return None

    def construct(self, fn_info):
        fn_name = fn_info.name[0]
        fn_attribute = self._make_attribute(fn_name)
        enumerator = htypes.ui.model_command_enumerator(
            function=mosaic.put(fn_attribute),
            params=tuple(fn_info.params),
            )
        enumerator_d_res = data_to_res(htypes.ui.model_command_enumerator_d())
        piece_t = fn_info.params['piece']
        piece_t_res = htypes.builtin.legacy_type(piece_t.data_t_ref)
        association = Association(
            bases=[piece_t_res],
            key=[enumerator_d_res, piece_t_res],
            value=enumerator,
            )
        self._resource_module['model_command_enumerator_d'] = enumerator_d_res
        self._resource_module[fn_name] = fn_attribute
        self._resource_module[f'{fn_name}.enumerator'] = enumerator
        return {association}


command_constructors = [
    ModelCommandImplementationCtr,
    GlobalCommandImplementationCtr,
    CommandEnumeratorImplementationCtr,
    ]
