import inspect

from .code.service_ctr import ServiceProbeCtr


def service_marker(fn, module_name, ctr_collector):
    if '.' in fn.__qualname__:
        raise RuntimeError(f"Only free functions are suitable for services: {fn!r}")
    ctr = ServiceProbeCtr(
        module_name=module_name, 
        attr_name=fn.__name__,
        name=fn.__name__,
        params=tuple(inspect.signature(fn).parameters),
        )
    ctr_collector.add_constructor(ctr)
