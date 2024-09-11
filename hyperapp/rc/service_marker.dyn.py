import inspect

from .code.config_ctl import ItemDictConfigCtl
from .code.service_ctr import ServiceProbeCtr
        

def add_service_ctr(module_name, ctr_collector, ctl, fn):
    if '.' in fn.__qualname__:
        raise RuntimeError(f"Only free functions are suitable for services: {fn!r}")
    ctr = ServiceProbeCtr(
        module_name=module_name, 
        attr_name=fn.__name__,
        name=fn.__name__,
        ctl=ctl,
        params=tuple(inspect.signature(fn).parameters),
        )
    ctr_collector.add_constructor(ctr)


class ServiceMarker:

    def __init__(self, module_name, cfg_item_creg, ctr_collector):
        self._module_name = module_name
        self._cfg_item_creg = cfg_item_creg
        self._ctr_collector = ctr_collector

    def __call__(self, fn=None, *, ctl=None):
        if ctl is None:
            ctl = ItemDictConfigCtl(self._cfg_item_creg)
        if fn is None:
            # Parameterized decorator case.
            assert 0, 'TODO'
            return ServiceDecorator(self._module_name, self._self._ctr_collector, ctl)
        add_service_ctr(self._module_name, self._ctr_collector, ctl, fn)
        return fn
