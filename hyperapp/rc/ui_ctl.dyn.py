import logging
from collections import defaultdict

from hyperapp.common.association_registry import Association

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    ui_ctl_creg,
    )

log = logging.getLogger(__name__)


def construct_view_impl(custom_types, resource_module, module_res, piece_t, qname):
    class_name, method_name = qname.split('.')
    class_attribute = htypes.builtin.attribute(
        object=mosaic.put(module_res),
        attr_name=class_name,
    )
    ctr_attribute = htypes.builtin.attribute(
        object=mosaic.put(class_attribute),
        attr_name=method_name,
    )
    piece_t_ref = custom_types[piece_t.type.module][piece_t.type.name]
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
    # TODO: Reverse resolve for ui_ctl_creg at custom resource registry.
    # return [ctl_association]
    return []


def create_ui_resources(custom_types, module_name, resource_module, module_res, call_list):
    qname_to_trace = {}
    for trace in call_list:
        log.debug("Trace for %s %s: %s", module_name, trace.fn_qual_name, trace)
        try:
            prev_trace = qname_to_trace[trace.fn_qual_name]
        except KeyError:
            qname_to_trace[trace.fn_qual_name] = trace
        else:
            if trace != prev_trace:
                qname_to_trace[trace.fn_qual_name] = None
                log.warning("Different traces for %s: %s and %s", trace.fn_qual_name, prev_trace, trace)

    ass_list = []
    for qname, trace in qname_to_trace.items():
        if trace is None:
            continue  # Multiple trace variants found - do not consider.
        params = {**trace.params}
        if trace.obj_type == 'classmethod':
            # Remove first, 'cls', parameter.
            params.pop(list(params)[0])
        if len(qname.split('.')) == 2 and trace.obj_type in ('classmethod', 'staticmethod'):
            if list(params) != ['layout']:
                continue
            piece_t = params['layout']
            if not isinstance(piece_t, htypes.inspect.record_t):
                log.warning("%s.%s: layout parameter type is not a data record", module_name, qname)
                continue
            # View constructor method.
            log.info("View constructor method: %s", qname)
            ass_list += construct_view_impl(custom_types, resource_module, module_res, piece_t, qname)
    return ass_list
