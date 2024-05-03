import logging

from .code.ui_ctr_view import view_impl_constructors
from .code.ui_ctr_model import model_constructors
from .code.ui_ctr_command import command_constructors

log = logging.getLogger(__name__)


def create_ui_resources(ctx, module_name, resource_module, module_res, qname_to_fn_info):
    constructor_classes = [
        *view_impl_constructors,
        *model_constructors,
        *command_constructors,
        ]
    constructors = [
        cls(ctx, resource_module, module_res)
        for cls in constructor_classes
        ]
    ass_set = set()
    for qname, fn_info in qname_to_fn_info.items():
        for ctr in constructors:
            reason = ctr.check_applicable(fn_info)
            if reason:
                log.debug("%s: %s is not applicable: %s (%r)", ctr.name, qname, reason, fn_info)
            else:
                log.info("%s: Construct: %s", ctr.name, qname)
                ass_set |= ctr.construct(fn_info)
    return ass_set
