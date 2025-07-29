import inspect

from .code.init_hook_ctr import InitHookCtr


def init_hook_marker(fn, module_name, ctr_collector):
    ctr = InitHookCtr(
        module_name=module_name,
        attr_qual_name=fn.__qualname__.split('.'),
        service_params=tuple(inspect.signature(fn).parameters),
        )
    ctr_collector.add_constructor(ctr)
    return fn
