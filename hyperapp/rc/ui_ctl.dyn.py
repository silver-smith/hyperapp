import logging
from collections import defaultdict

from hyperapp.common.htypes import TRecord
from hyperapp.common.association_registry import Association

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    types,
    ui_ctl_creg,
    ui_adapter_creg,
    )

log = logging.getLogger(__name__)


def _resolve_record_t(t_rec):
    if not isinstance(t_rec, htypes.inspect.data_t):
        return None
    t = types.resolve(t_rec.t)
    if not isinstance(t, TRecord):
        return None
    return t_rec.t


def construct_view_impl(ctx, module_name, resource_module, module_res, params, qname):
    piece_t_ref = _resolve_record_t(params['layout'])
    if piece_t_ref is None:
        log.warning("%s.%s: layout parameter type is not a data record", module_name, qname)
        return []
    log.info("Construct view implementation: %s: %s", resource_module.name, qname)
    class_name, method_name = qname.split('.')
    class_attribute = htypes.builtin.attribute(
        object=mosaic.put(module_res),
        attr_name=class_name,
    )
    ctr_attribute = htypes.builtin.attribute(
        object=mosaic.put(class_attribute),
        attr_name=method_name,
    )
    piece_t_res = htypes.builtin.legacy_type(piece_t_ref)
    ui_ctl = htypes.ui.ui_ctl(
        ctr_fn=mosaic.put(ctr_attribute),
        command_methods=(),
        )
    ui_ctl_creg_res = pyobj_creg.reverse_resolve(ui_ctl_creg)
    ctl_association = Association(
        bases=[piece_t_res],
        key=[ui_ctl_creg_res, piece_t_res],
        value=ui_ctl,
        )
    resource_module[class_name] = class_attribute
    resource_module[f'{class_name}.{method_name}'] = ctr_attribute
    resource_module[f'{class_name}.{method_name}.ctl'] = ui_ctl
    return [ctl_association]


def construct_adapter_impl(ctx, module_name, resource_module, module_res, params, qname):
    piece_t_ref = _resolve_record_t(params['piece'])
    if piece_t_ref is None:
        log.warning("%s.%s: layout parameter type is not a data record", module_name, qname)
        return []
    log.info("Construct adapter implementation: %s: %s", resource_module.name, qname)
    class_name, method_name = qname.split('.')
    class_attribute = htypes.builtin.attribute(
        object=mosaic.put(module_res),
        attr_name=class_name,
    )
    ctr_attribute = htypes.builtin.attribute(
        object=mosaic.put(class_attribute),
        attr_name=method_name,
    )
    piece_t_res = htypes.builtin.legacy_type(piece_t_ref)
    ui_adapter_creg_res = pyobj_creg.reverse_resolve(ui_adapter_creg)
    association = Association(
        bases=[ui_adapter_creg_res, piece_t_res],
        key=[ui_adapter_creg_res, piece_t_res],
        value=ctr_attribute,
        )
    resource_module[class_name] = class_attribute
    resource_module[f'{class_name}.{method_name}'] = ctr_attribute
    return [association]


def create_ui_resources(ctx, module_name, resource_module, module_res, call_list):
    qname_to_traces = defaultdict(list)
    for trace in call_list:
        log.debug("Trace for %s %s: %s", module_name, trace.fn_qual_name, trace)
        qname_to_traces[trace.fn_qual_name].append(trace)
    for trace_list in qname_to_traces.values():
        for trace in trace_list[1:]:
            if trace.params != trace_list[0].params:
                log.warning("Different traces for %s: %s and %s", trace.fn_qual_name, trace_list[0], trace)

    ass_list = []
    for qname, trace_list in qname_to_traces.items():
        trace = trace_list[0]
        params = {**trace.params}
        if trace.obj_type == 'classmethod':
            # Remove first, 'cls', parameter.
            params.pop(list(params)[0])
        if len(qname.split('.')) == 2 and trace.obj_type in ('classmethod', 'staticmethod'):
            if list(params) == ['layout']:
                ass_list += construct_view_impl(ctx, module_name, resource_module, module_res, params, qname)
            if list(params) == ['piece'] and 'Adapter' in qname:
                ass_list += construct_adapter_impl(ctx, module_name, resource_module, module_res, params, qname)
    return ass_list
