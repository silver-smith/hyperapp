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

log = logging.getLogger(__name__)


def _make_d_instance_res(t):
    t_res = pyobj_creg.reverse_resolve(t)
    return htypes.builtin.call(
        function=mosaic.put(t_res),
        )


class CommandImplementationCtr(Constructor):

    def _make_command_d_res(self, fn_name):
        d_attr = fn_name + '_d'
        try:
            command_d_ref = self._ctx.types[self._module_res.module_name][d_attr]
        except KeyError:
            raise RuntimeError(f"Create directory type: {self._module_res.module_name}.{d_attr}")
        command_d_t = types.resolve(command_d_ref)
        return data_to_res(command_d_t())

    def check_applicable(self, fn_info):
        if len(fn_info.name) != 1:
            return f"Name has not 1 parts: {fn_info.name!r}"
        if fn_info.obj_type != 'function':
            return f"obj_type is not a 'function': {fn_info.obj_type!r}"
        if not fn_info.result.is_single:
            return "Result has not one, but {fn_info.result.count} type variants: {fn_info.result.cases}"
        if not fn_info.result.is_data:
            return "Result is not a data: {fn_info.result!r}"
        return None


class ModelCommandImplementationCtr(CommandImplementationCtr):

    @property
    def name(self):
        return "Model command"

    def check_applicable(self, fn_info):
        reason = super().check_applicable(fn_info)
        if reason:
            return reason
        result_is_accepted = (
            isinstance(fn_info.result.data_t, TRecord) or
            isinstance(fn_info.result.data_t, TList) and isinstance(fn_info.result.data_t.element_t, TRecord) or
            fn_info.result.data_t is tString or
            fn_info.result.data_t is tNone
            )
        if not result_is_accepted:
            return f"Result is not a record, list or records, string or None: {fn_info.result.data_t!r}"
        accepted_params = {'piece', 'model_state', 'current_idx', 'current_item', 'controller', 'ctx'}
        reason = self._check_accepted_params(fn_info, accepted_params)
        if reason:
            return reason
        if fn_info.param_names[:1] != ['piece']:
            return f"First param is not 'piece': {fn_info.param_names}"
        piece_t = fn_info.params['piece']
        if not piece_t.is_single:
            return "Piece param has not one, but {piece_t.count} type variants: {piece_t.cases}"
        if not piece_t.is_data:
            return "Piece param is not a data: {piece_t!r}"
        if not isinstance(piece_t.data_t, TRecord):
            return f"Piece param is not a record: {piece_t.data_t!r}"
        return None

    def construct(self, fn_info):
        fn_name = fn_info.name[0]
        fn_attribute = self._make_attribute(fn_name)
        command_d_res = self._make_command_d_res(fn_name)
        model_command_kind_d_res = _make_d_instance_res(htypes.ui.model_command_kind_d)
        d = (
            mosaic.put(command_d_res),
            mosaic.put(model_command_kind_d_res),
            )
        has_context = fn_info.params.keys() & {'model_state', 'current_idx', 'current_item'}
        if has_context:
            context_model_command_kind_d_res = _make_d_instance_res(htypes.ui.context_model_command_kind_d)
            d = (*d, mosaic.put(context_model_command_kind_d_res))
        command = htypes.ui.model_command(
            d=d,
            name=fn_name,
            function=mosaic.put(fn_attribute),
            params=tuple(fn_info.params),
            )
        model_command_d_res = _make_d_instance_res(htypes.ui.model_command_d)
        piece_t = fn_info.params['piece']
        piece_t_res = htypes.builtin.legacy_type(piece_t.data_t_ref)
        association = Association(
            bases=[piece_t_res],
            key=[model_command_d_res, piece_t_res],
            value=command,
            )
        self._resource_module[fn_name] = fn_attribute
        self._resource_module[f'{fn_name}.d'] = command_d_res
        if has_context:
            self._resource_module['context_model_command_kind_d'] = context_model_command_kind_d_res
        self._resource_module['model_command_kind_d'] = model_command_kind_d_res
        self._resource_module[f'{fn_name}.command'] = command
        self._resource_module['model_command_d'] = model_command_d_res
        return {association}


class GlobalCommandImplementationCtr(CommandImplementationCtr):

    @property
    def name(self):
        return "Global command"

    def check_applicable(self, fn_info):
        reason = super().check_applicable(fn_info)
        if reason:
            return reason
        result_is_accepted = (
            isinstance(fn_info.result.data_t, TRecord) or
            isinstance(fn_info.result.data_t, TList) and isinstance(fn_info.result.data_t.element_t, TRecord) or
            fn_info.result.data_t is tString
            )
        if not result_is_accepted:
            return f"Result is not a record, list or records, string or None: {fn_info.result.data_t!r}"
        if 'piece' in fn_info.params:
            piece_t = fn_info.params['piece']
            if piece_t.is_single:
                return f"Function has 'piece' param, and it do not has multiple type cases: {piece_t!r}"
            for case in piece_t.cases:
                if not case.is_data:
                    return "Piece param case is not a data: {case!r}"
                if not isinstance(case.data_t, TRecord):
                    return f"Piece param case is not a record: {case.data_t!r}"
        accepted_params = {'piece', 'model_state', 'ctx'}
        reason = self._check_accepted_params(fn_info, accepted_params)
        if reason:
            return reason
        return None

    def construct(self, fn_info):
        fn_name = fn_info.name[0]
        fn_attribute = self._make_attribute(fn_name)
        command_d_res = self._make_command_d_res(fn_name)
        model_command_kind_d_res = _make_d_instance_res(htypes.ui.model_command_kind_d)
        global_model_command_kind_d_res = _make_d_instance_res(htypes.ui.global_model_command_kind_d)
        d = (
            mosaic.put(command_d_res),
            mosaic.put(model_command_kind_d_res),
            mosaic.put(global_model_command_kind_d_res),
            )
        has_context = fn_info.params.keys() & {'model_state'}
        if has_context:
            context_model_command_kind_d_res = _make_d_instance_res(htypes.ui.context_model_command_kind_d)
            d = (*d, mosaic.put(context_model_command_kind_d_res))
        command = htypes.ui.model_command(
            d=d,
            name=fn_name,
            function=mosaic.put(fn_attribute),
            params=tuple(fn_info.params),
            )
        global_model_command_d_res = _make_d_instance_res(htypes.ui.global_model_command_d)
        association = Association(
            bases=[global_model_command_d_res],
            key=[global_model_command_d_res],
            value=command,
            )
        self._resource_module[fn_name] = fn_attribute
        self._resource_module[f'{fn_name}.d'] = command_d_res
        if has_context:
            self._resource_module['context_model_command_kind_d'] = context_model_command_kind_d_res
        self._resource_module['model_command_kind_d'] = model_command_kind_d_res
        self._resource_module['global_model_command_kind_d'] = global_model_command_kind_d_res
        self._resource_module[f'{fn_name}.command'] = command
        self._resource_module['global_model_command_d'] = global_model_command_d_res
        return {association}


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
        if not issubclass(result.data_t.element_t, (htypes.ui.ui_command, htypes.ui.ui_model_command)):
            return f"Result element type is not a command: {result.data_t.element_t}"
        if fn_info.param_names[:1] != ['piece']:
            return f"First param is not 'piece': {fn_info.param_names}"
        accepted_params = {'piece', 'current_item', 'controller'}
        reason = self._check_accepted_params(fn_info, accepted_params)
        if reason:
            return reason
        piece_t = fn_info.params['piece']
        if not piece_t.is_single:
            return "Piece param has not one, but {piece_t.count} type variants: {piece_t.cases}"
        if not piece_t.is_data:
            return "Piece param is not a data: {piece_t!r}"
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
        enumerator_d_res = _make_d_instance_res(htypes.ui.model_command_enumerator_d)
        piece_t = fn_info.params['piece']
        piece_t_res = htypes.builtin.legacy_type(piece_t.data_t_ref)
        association = Association(
            bases=[piece_t_res],
            key=[enumerator_d_res, piece_t_res],
            value=enumerator,
            )
        self._resource_module[fn_name] = fn_attribute
        self._resource_module[f'{fn_name}.enumerator'] = enumerator
        self._resource_module['model_command_enumerator_d'] = enumerator_d_res
        return {association}


command_constructors = [
    ModelCommandImplementationCtr,
    GlobalCommandImplementationCtr,
    CommandEnumeratorImplementationCtr,
    ]
