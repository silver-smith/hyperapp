import logging

from hyperapp.common.htypes import TRecord
from hyperapp.common.association_registry import Association

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    view_creg,
    model_view_creg,
    ui_adapter_creg,
    )
from .code.ui_ctr_constructor import Constructor

log = logging.getLogger(__name__)


class ViewImplementationCtrBase(Constructor):

    def check_applicable(self, fn_info):
        if len(fn_info.name) != 2:
            return f"Name has not 2 parts: {fn_info.name!r}"
        if fn_info.obj_type not in {'classmethod', 'staticmethod'}:
            return f"obj_type is not 'classmethod' nor 'staticmethod': {fn_info.obj_type!r}"
        if 'View' not in fn_info.name[0]:
            return f"Name has no 'View' in it: {fn_info.name[0]!r}"
        piece_t = fn_info.params['piece']
        if not piece_t.is_single:
            return f"Piece param has not one, but {piece_t.count} type variants: {piece_t.cases}"
        if not piece_t.is_data:
            return f"Piece param is not a data: {piece_t!r}"
        if not isinstance(piece_t.data_t, TRecord):
            return f"Piece param is not a record: {piece_t.data_t!r}"
        return None

    def construct(self, fn_info):
        class_name, method_name = fn_info.name
        class_attribute = self._make_attribute(class_name)
        ctr_attribute = self._make_attribute(method_name, class_attribute)
        piece_t = fn_info.params['piece']
        piece_t_res = htypes.builtin.legacy_type(piece_t.data_t_ref)
        view_creg_res = pyobj_creg.reverse_resolve(self.view_creg_service)
        ctl_association = Association(
            bases=[view_creg_res, piece_t_res],
            key=[view_creg_res, piece_t_res],
            value=ctr_attribute,
            )
        self._resource_module[class_name] = class_attribute
        self._resource_module[f'{class_name}.{method_name}'] = ctr_attribute
        return {ctl_association}


class ViewImplementationCtr(ViewImplementationCtrBase):

    view_creg_service = view_creg

    @property
    def name(self):
        return "View"

    def check_applicable(self, fn_info):
        if fn_info.param_names != ['piece', 'ctx']:
            return f"Param names are not 'piece' and 'ctx': {fn_info.param_names}"
        reason = super().check_applicable(fn_info)
        if reason:
            return reason
        return None


class ModelViewImplementationCtr(ViewImplementationCtrBase):

    view_creg_service = model_view_creg

    @property
    def name(self):
        return "Model view"

    def check_applicable(self, fn_info):
        if fn_info.param_names != ['piece', 'model', 'ctx']:
            return f"Param names are not 'piece', 'model' and 'ctx': {fn_info.param_names}"
        reason = super().check_applicable(fn_info)
        if reason:
            return reason
        return None


class ViewAdapterImplementationCtr(Constructor):

    @property
    def name(self):
        return "Adapter"

    def check_applicable(self, fn_info):
        if len(fn_info.name) != 2:
            return f"name has not 2 parts: {fn_info.name!r}"
        if fn_info.obj_type not in {'classmethod', 'staticmethod'}:
            return f"obj_type is not 'classmethod' nor 'staticmethod': {fn_info.obj_type!r}"
        if 'Adapter' not in fn_info.name[0]:
            return f"name has no 'Adapter' in it: {fn_info.name[0]!r}"
        if fn_info.param_names != ['piece', 'model', 'ctx']:
            return f"Param names are not 'piece', 'model' and 'ctx': {fn_info.param_names}"
        piece_t = fn_info.params['piece']
        if not piece_t.is_single:
            return "Piece param has not one, but {piece_t.count} type variants: {piece_t.cases}"
        if not piece_t.is_data:
            return "Piece param is not a data: {piece_t!r}"
        if not isinstance(piece_t.data_t, TRecord):
            return f"Piece param is not a record: {piece_t.data_t!r}"
        return None

    def construct(self, fn_info):
        class_name, method_name = fn_info.name
        class_attribute = self._make_attribute(class_name)
        ctr_attribute = self._make_attribute(method_name, class_attribute)
        piece_t = fn_info.params['piece']
        piece_t_res = htypes.builtin.legacy_type(piece_t.data_t_ref)
        ui_adapter_creg_res = pyobj_creg.reverse_resolve(ui_adapter_creg)
        association = Association(
            bases=[ui_adapter_creg_res, piece_t_res],
            key=[ui_adapter_creg_res, piece_t_res],
            value=ctr_attribute,
            )
        self._resource_module[class_name] = class_attribute
        self._resource_module[f'{class_name}.{method_name}'] = ctr_attribute
        return {association}


view_impl_constructors = [
    ViewImplementationCtr,
    ModelViewImplementationCtr,
    ViewAdapterImplementationCtr,
    ]
