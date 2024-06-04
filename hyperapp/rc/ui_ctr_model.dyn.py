import logging
from abc import ABCMeta, abstractmethod

from hyperapp.common.htypes import TList, TRecord, tNone
from hyperapp.common.association_registry import Association

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.ui_ctr_constructor import Constructor

log = logging.getLogger(__name__)


class ModelImplementationCtr(Constructor, metaclass=ABCMeta):

    def check_applicable(self, fn_info):
        if len(fn_info.name) != 1:
            return f"Name has not 1 parts: {fn_info.name!r}"
        if fn_info.obj_type != 'function':
            return f"obj_type is not a 'function': {fn_info.obj_type!r}"
        if not fn_info.result.is_single:
            return f"Result has not one, but {fn_info.result.count} type variants: {fn_info.result.cases}"
        if not fn_info.result.is_data:
            return f"Result is not a data: {fn_info.result}"
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
        ui_t = self._construct_ui_t(fn_info)
        impl = htypes.ui.fn_impl(
            function=mosaic.put(fn_attribute),
            params=tuple(fn_info.params),
            )
        model_d_res = pyobj_creg.actor_to_piece(htypes.ui.model_d)
        model_d = htypes.builtin.call(
            function=mosaic.put(model_d_res),
            )
        model = htypes.ui.model(
            ui_t=mosaic.put(ui_t),
            impl=mosaic.put(impl),
            )
        piece_t = fn_info.params['piece']
        piece_t_res = web.summon(piece_t.data_t_ref)
        association = Association(
            bases=[piece_t_res],
            key=[model_d, piece_t_res],
            value=model,
            )
        self._resource_module[fn_name] = fn_attribute
        self._resource_module[f'{fn_name}.ui_t'] = ui_t
        self._resource_module[f'{fn_name}.impl'] = impl
        self._resource_module['model_d'] = model_d
        self._resource_module[f'{fn_name}.model'] = model
        return {association}

    @abstractmethod
    def _construct_ui_t(self, fn_info):
        pass


class EnumerableImplementationCtr(ModelImplementationCtr):

    def check_applicable(self, fn_info):
        reason = super().check_applicable(fn_info)
        if reason:
            return reason
        if not isinstance(fn_info.result.data_t, TList):
            return f"Result is not a list: {fn_info.result.data_t!r}"
        return None


class ListImplementationCtr(EnumerableImplementationCtr):

    @property
    def name(self):
        return "List model"

    def check_applicable(self, fn_info):
        if fn_info.param_names[:1] != ['piece']:
            return f"First param is not 'piece': {fn_info.param_names}"
        reason = self._check_accepted_params(fn_info, {'piece', 'feed', 'controller', 'ctx', 'lcs'})
        if reason:
            return reason
        reason = super().check_applicable(fn_info)
        if reason:
            return reason
        return None

    def _construct_ui_t(self, fn_info):
        element_t_res = pyobj_creg.actor_to_piece(fn_info.result.data_t.element_t)
        return htypes.ui.list_ui_t(
            element_t=mosaic.put(element_t_res),
            )


class TreeImplementationCtr(EnumerableImplementationCtr):

    @property
    def name(self):
        return "Tree model"

    def _non_none_cases(self, t):
        for case in t.cases:
            if case.is_data and case.data_t is tNone:
                continue
            yield case

    def check_applicable(self, fn_info):
        if fn_info.param_names[:2] != ['piece', 'parent']:
            return f"First and second params are not 'piece' and 'parent': {fn_info.param_names}"
        reason = self._check_accepted_params(fn_info, {'piece', 'parent', 'feed', 'controller', 'ctx', 'lcs'})
        if reason:
            return reason
        reason = super().check_applicable(fn_info)
        if reason:
            return reason
        parent_t = fn_info.params['parent']
        non_none_cases = list(self._non_none_cases(parent_t))
        non_none_count = len(non_none_cases)
        if non_none_count != 1:
            return f"Parent param type do not has single non-none case, but {non_none_count}: {parent_t!r}"
        [parent_t_case] = non_none_cases
        if not parent_t_case.is_data:
            return f"Parent param non-none case is not a data: {t!r}"
        return None

    def _construct_ui_t(self, fn_info):
        parent_t = fn_info.params['parent']
        [parent_t_case] = list(self._non_none_cases(parent_t))
        parent_t_ref = parent_t_case.data_t_ref
        element_t_res = pyobj_creg.actor_to_piece(fn_info.result.data_t.element_t)
        return htypes.ui.tree_ui_t(
            key_t=parent_t_ref,
            element_t=mosaic.put(element_t_res),
            )


class RecordImplementationCtr(ModelImplementationCtr):

    @property
    def name(self):
        return "List model"

    def check_applicable(self, fn_info):
        if fn_info.param_names[:1] != ['piece']:
            return f"First param is not 'piece': {fn_info.param_names}"
        reason = self._check_accepted_params(fn_info, {'piece', 'feed', 'controller', 'ctx', 'lcs'})
        if reason:
            return reason
        reason = super().check_applicable(fn_info)
        if reason:
            return reason
        if not isinstance(fn_info.result.data_t, TRecord):
            return f"Result is not a record: {fn_info.result.data_t!r}"
        return None

    def _construct_ui_t(self, fn_info):
        record_t_res = pyobj_creg.actor_to_piece(fn_info.result.data_t)
        return htypes.ui.record_ui_t(
            record_t=mosaic.put(record_t_res),
            )


model_constructors = [
    ListImplementationCtr,
    TreeImplementationCtr,
    RecordImplementationCtr,
    ]
