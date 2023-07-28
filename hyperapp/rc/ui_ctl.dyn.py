import logging
from collections import defaultdict

log = logging.getLogger(__name__)


def create_ui_resources(module_name, resource_registry, call_list):
    qname_to_trace = {}
    for trace in call_list:
        log.debug("Trace for %s %s: %s", module_name, trace.fn_qual_name, trace)
        try:
            prev_trace = qname_to_trace[trace.fn_qual_name]
        except KeyError:
            qname_to_trace[trace.fn_qual_name] = trace
        else:
            if trace != prev_trace:
                raise RuntimeError(f"Different traces for {trace.fn_qual_name}: {prev_trace} and {trace}")
    for qname, trace in qname_to_trace.items():
        params = {**trace.params}
        if trace.obj_type == 'classmethod':
            # Remove first, 'cls', parameter.
            params.pop(list(params)[0])
        qname_l = qname.split('.')
        if len(qname_l) == 2 and trace.obj_type in ('classmethod', 'staticmethod'):
            if list(params) != ['layout']:
                continue
            # View constructor method.
            class_name, method_name = qname_l
            log.info("View constructor method: %s", qname)
    return []
