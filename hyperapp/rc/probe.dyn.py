def real_fn(fn):
    if isinstance(fn, ProbeBase):
        # Multiple wrappers.
        return fn.real_fn
    else:
        return fn


class ProbeBase:

    def __init__(self, system_probe, ctr_collector, module_name, fn):
        self._system = system_probe
        self._ctr_collector = ctr_collector
        self._module_name = module_name
        self._fn = fn

    @property
    def real_fn(self):
        return real_fn(self._fn)
