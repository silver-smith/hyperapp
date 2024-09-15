import inspect

from .services import mosaic
from .code.config_ctl import ItemDictConfigCtl
from .code.service_probe_resource import ServiceProbeCtr
        

def add_service_ctr(config_ctl_reg, ctr_collector, module_name, ctl, fn):
    if '.' in fn.__qualname__:
        raise RuntimeError(f"Only free functions are suitable for services: {fn!r}")
    ctr = ServiceProbeCtr(
        config_ctl=config_ctl_reg,
        module_name=module_name, 
        attr_name=fn.__name__,
        name=fn.__name__,
        ctl_ref=mosaic.put(ctl.piece),
        params=tuple(inspect.signature(fn).parameters),
        )
    ctr_collector.add_constructor(ctr)


class ServiceDecorator:

    def __init__(self, config_ctl_reg, ctr_collector, module_name, ctl):
        self._config_ctl_reg = config_ctl_reg
        self._ctr_collector = ctr_collector
        self._module_name = module_name
        self._ctl = ctl

    def __call__(self, fn):
        add_service_ctr(self._config_ctl_reg, self._ctr_collector, self._module_name, self._ctl, fn)
        return fn


class ServiceMarker:

    def __init__(self, module_name, config_ctl, cfg_item_creg, ctr_collector):
        self._module_name = module_name
        self._config_ctl_reg = config_ctl
        self._cfg_item_creg = cfg_item_creg
        self._ctr_collector = ctr_collector

    def __call__(self, fn=None, *, ctl=None):
        if ctl is None:
            ctl = ItemDictConfigCtl(self._cfg_item_creg)
        if fn is None:
            # Parameterized decorator case (@mark.service(ctl=xx)).
            return ServiceDecorator(self._config_ctl_reg, self._ctr_collector, self._module_name, ctl)
        # Non-parameterized decorator case (@mark.service).
        add_service_ctr(self._config_ctl_reg, self._ctr_collector, self._module_name, ctl, fn)
        return fn
