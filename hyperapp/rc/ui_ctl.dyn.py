import logging
from collections import defaultdict

from hyperapp.common.htypes import TList, TRecord, tNone, tString
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


def construct_view_impl(ctx, module_name, resource_module, module_res, qname, params):
    piece_t_ref = _resolve_record_t(params['piece'])
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


def construct_adapter_impl(ctx, module_name, resource_module, module_res, qname, params):
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


def construct_fn_list_impl(ctx, module_name, resource_module, module_res, qname, params, result_t):
    piece_t_ref = _resolve_record_t(params['piece'])
    if piece_t_ref is None:
        log.warning("%s.%s: layout parameter type is not a data record", module_name, qname)
        return []
    log.info("Construct fn list implementation: %s: %s", resource_module.name, qname)
    fn_name = qname
    fn_attribute = htypes.builtin.attribute(
        object=mosaic.put(module_res),
        attr_name=fn_name,
    )
    piece_t_res = htypes.builtin.legacy_type(piece_t_ref)
    element_t_res = pyobj_creg.reverse_resolve(result_t.element_t)
    ui_t = htypes.ui.list_ui_t(
        element_t=mosaic.put(element_t_res),
        )
    impl = htypes.ui.fn_impl(
        function=mosaic.put(fn_attribute),
        want_feed='feed' in params,
        )
    model_d_res = pyobj_creg.reverse_resolve(htypes.ui.model_d)
    model_d = htypes.builtin.call(
        function=mosaic.put(model_d_res),
        )
    model = htypes.ui.model(
        ui_t=mosaic.put(ui_t),
        impl=mosaic.put(impl),
        )
    association = Association(
        bases=[piece_t_res],
        key=[model_d, piece_t_res],
        value=model,
        )
    resource_module[fn_name] = fn_attribute
    resource_module[f'{fn_name}.ui_t'] = ui_t
    resource_module[f'{fn_name}.impl'] = impl
    resource_module['model_d'] = model_d
    resource_module[f'{fn_name}.model'] = model
    return [association]


def construct_fn_tree_impl(ctx, module_name, resource_module, module_res, qname, params, result_t):
    piece_t_ref = _resolve_record_t(params['piece'])
    if piece_t_ref is None:
        log.warning("%s.%s: layout parameter type is not a data record", module_name, qname)
        return []
    key_t_rec = params['parent']
    if not isinstance(key_t_rec, htypes.inspect.data_t):
        log.warning("%s.%s: parent parameter type is not a data", module_name, qname)
        return []
    log.info("Construct fn tree implementation: %s: %s", resource_module.name, qname)
    fn_name = qname
    fn_attribute = htypes.builtin.attribute(
        object=mosaic.put(module_res),
        attr_name=fn_name,
    )
    piece_t_res = htypes.builtin.legacy_type(piece_t_ref)
    key_t_res = htypes.builtin.legacy_type(key_t_rec.t)
    element_t_res = pyobj_creg.reverse_resolve(result_t.element_t)
    ui_t = htypes.ui.tree_ui_t(
        key_t=mosaic.put(key_t_res),
        element_t=mosaic.put(element_t_res),
        )
    impl = htypes.ui.fn_impl(
        function=mosaic.put(fn_attribute),
        want_feed='feed' in params,
        )
    model_d_res = pyobj_creg.reverse_resolve(htypes.ui.model_d)
    model_d = htypes.builtin.call(
        function=mosaic.put(model_d_res),
        )
    model = htypes.ui.model(
        ui_t=mosaic.put(ui_t),
        impl=mosaic.put(impl),
        )
    association = Association(
        bases=[piece_t_res],
        key=[model_d, piece_t_res],
        value=model,
        )
    resource_module[fn_name] = fn_attribute
    resource_module[f'{fn_name}.ui_t'] = ui_t
    resource_module[f'{fn_name}.impl'] = impl
    resource_module['model_d'] = model_d
    resource_module[f'{fn_name}.model'] = model
    return [association]


def construct_global_model_command(ctx, module_name, resource_module, module_res, qname, params):
    log.info("Construct global model command: %s: %s", resource_module.name, qname)
    fn_name = qname
    fn_attribute = htypes.builtin.attribute(
        object=mosaic.put(module_res),
        attr_name=fn_name,
    )
    command = htypes.ui.model_command(
        name=fn_name,
        function=mosaic.put(fn_attribute),
        params=tuple(params),
        )
    global_model_command_d_res = pyobj_creg.reverse_resolve(htypes.ui.global_model_command_d)
    global_model_command_d = htypes.builtin.call(
        function=mosaic.put(global_model_command_d_res),
        )
    association = Association(
        bases=[global_model_command_d],
        key=[global_model_command_d],
        value=command,
        )
    resource_module[fn_name] = fn_attribute
    resource_module[f'{fn_name}.command'] = command
    resource_module['global_model_command_d'] = global_model_command_d
    return [association]


def construct_model_command_enumerator(ctx, module_name, resource_module, module_res, qname, piece_t_ref, params):
    log.info("Construct model command enumerator: %s: %s", resource_module.name, qname)
    fn_name = qname
    fn_attribute = htypes.builtin.attribute(
        object=mosaic.put(module_res),
        attr_name=fn_name,
    )
    enumerator = htypes.ui.model_command_enumerator(
        function=mosaic.put(fn_attribute),
        params=tuple(params),
        )
    enumerator_d_res = pyobj_creg.reverse_resolve(htypes.ui.model_command_enumerator_d)
    enumerator_d = htypes.builtin.call(
        function=mosaic.put(enumerator_d_res),
        )
    piece_t_res = htypes.builtin.legacy_type(piece_t_ref)
    association = Association(
        bases=[piece_t_res],
        key=[enumerator_d, piece_t_res],
        value=enumerator,
        )
    resource_module[fn_name] = fn_attribute
    resource_module[f'{fn_name}.enumerator'] = enumerator
    resource_module['model_command_enumerator_d'] = enumerator_d
    return [association]


def construct_model_command(ctx, module_name, resource_module, module_res, qname, piece_t_ref, params):
    log.info("Construct model command: %s: %s", resource_module.name, qname)
    fn_name = qname
    fn_attribute = htypes.builtin.attribute(
        object=mosaic.put(module_res),
        attr_name=fn_name,
    )
    command = htypes.ui.model_command(
        name=fn_name,
        function=mosaic.put(fn_attribute),
        params=tuple(params),
        )
    model_command_d_res = pyobj_creg.reverse_resolve(htypes.ui.model_command_d)
    model_command_d = htypes.builtin.call(
        function=mosaic.put(model_command_d_res),
        )
    piece_t_res = htypes.builtin.legacy_type(piece_t_ref)
    association = Association(
        bases=[piece_t_res],
        key=[model_command_d, piece_t_res],
        value=command,
        )
    resource_module[fn_name] = fn_attribute
    resource_module[f'{fn_name}.command'] = command
    resource_module['model_command_d'] = model_command_d
    return [association]


def _create_trace_resources(ctx, module_name, resource_module, module_res, qname, trace):
    ass_list = []
    params = {**trace.params}
    if trace.obj_type == 'classmethod':
        # Remove first, 'cls', parameter.
        params.pop(list(params)[0])
    param_names = list(params)
    if len(qname.split('.')) == 2 and trace.obj_type in ('classmethod', 'staticmethod'):
        if param_names == ['piece'] and 'View' in qname:
            ass_list += construct_view_impl(ctx, module_name, resource_module, module_res, qname, params)
        if param_names == ['piece', 'ctx'] and 'Adapter' in qname:
            ass_list += construct_adapter_impl(ctx, module_name, resource_module, module_res, qname, params)
    if len(qname.split('.')) == 1 and trace.obj_type == 'function':
        if (trace.result_t == htypes.inspect.object_t('list', 'builtins')
                and param_names[:1] == ['piece'] and set(param_names[1:]) <= {'current_item'}):
            piece_t_ref = _resolve_record_t(params['piece'])
            if piece_t_ref is None:
                log.warning("%s.%s: layout parameter type is not a data record", module_name, qname)
                return ass_list
            ass_list += construct_model_command_enumerator(ctx, module_name, resource_module, module_res, qname, piece_t_ref, param_names)
        if not isinstance(trace.result_t, htypes.inspect.data_t):
            return ass_list
        result_t = types.resolve(trace.result_t.t)
        if param_names in [['piece'], ['piece', 'feed']] and isinstance(result_t, TList):
            ass_list += construct_fn_list_impl(ctx, module_name, resource_module, module_res, qname, params, result_t)
        if param_names in [['piece', 'parent'], ['piece', 'parent', 'feed']] and isinstance(result_t, TList):
            ass_list += construct_fn_tree_impl(ctx, module_name, resource_module, module_res, qname, params, result_t)
        if (isinstance(result_t, TRecord)
                or result_t is tString
                or isinstance(result_t, TList) and isinstance(result_t.element_t, TRecord)):
            # Return type suggests it can be a command.
            if params.keys() <= {'state'}:
                ass_list += construct_global_model_command(ctx, module_name, resource_module, module_res, qname, params)
        if (isinstance(result_t, TRecord)
                or result_t is tString
                or isinstance(result_t, TList) and isinstance(result_t.element_t, TRecord)
                or result_t is tNone):
            if param_names[:1] == ['piece'] and set(param_names[1:]) <= {'state', 'current_idx', 'current_item'}:
                piece_t_ref = _resolve_record_t(params['piece'])
                if piece_t_ref is None:
                    log.warning("%s.%s: layout parameter type is not a data record", module_name, qname)
                    return ass_list
                ass_list += construct_model_command(ctx, module_name, resource_module, module_res, qname, piece_t_ref, param_names)
    return ass_list


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
        ass_list += _create_trace_resources(ctx, module_name, resource_module, module_res, qname, trace)
    return ass_list
