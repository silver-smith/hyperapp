import inspect

from .services import mosaic
from .code.config_ctl import DictConfigCtl
from .code.fixture_ctr import FixtureObjCtr, FixtureProbeCtr


def _add_fixture_ctr(ctr_collector, ctr_cls, module_name, ctl, fn):
    if '.' in fn.__qualname__:
        raise RuntimeError(f"Only free functions are suitable for fixtures: {fn!r}")
    ctr = ctr_cls(
        module_name=module_name, 
        attr_name=fn.__name__,
        name=fn.__name__,
        ctl_ref=mosaic.put(ctl.piece),
        params=tuple(inspect.signature(fn).parameters),
        )
    ctr_collector.add_constructor(ctr)


class FixtureObjMarker:

    def __init__(self, module_name, cfg_item_creg, ctr_collector):
        self._module_name = module_name
        self._cfg_item_creg = cfg_item_creg
        self._ctr_collector = ctr_collector

    def __call__(self, fn):
        ctl = DictConfigCtl(self._cfg_item_creg)
        _add_fixture_ctr(self._ctr_collector, FixtureObjCtr, self._module_name, ctl, fn)
        return fn


class FixtureDecorator:

    def __init__(self, ctr_collector, module_name, ctl):
        self._ctr_collector = ctr_collector
        self._module_name = module_name
        self._ctl = ctl

    def __call__(self, fn):
        _add_fixture_ctr(self._ctr_collector, FixtureProbeCtr, self._module_name, self._ctl, fn)
        return fn


class FixtureMarker:

    def __init__(self, module_name, cfg_item_creg, ctr_collector):
        self._module_name = module_name
        self._cfg_item_creg = cfg_item_creg
        self._ctr_collector = ctr_collector

    def __call__(self, fn=None, *, ctl=None):
        if ctl is None:
            ctl = DictConfigCtl(self._cfg_item_creg)
        if fn is None:
            # Parameterized decorator case (@mark.service(ctl=xx)).
            return FixtureDecorator(self._ctr_collector, self._module_name, ctl)
        _add_fixture_ctr(self._ctr_collector, FixtureProbeCtr, self._module_name, ctl, fn)
        return fn

    @property
    def obj(self):
        return FixtureObjMarker(self._module_name, self._cfg_item_creg, self._ctr_collector)
