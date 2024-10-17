import inspect

from .services import mosaic
from .code.config_ctl import DictConfigCtl
from .code.fixture_ctr import FixtureObjCtr, FixtureProbeCtr


class FixtureObjMarker:

    def __init__(self, module_name, cfg_item_creg, ctr_collector):
        self._module_name = module_name
        self._cfg_item_creg = cfg_item_creg
        self._ctr_collector = ctr_collector

    def __call__(self, fn):
        if '.' in fn.__qualname__:
            raise RuntimeError(f"Only free functions are suitable for fixtures: {fn!r}")
        ctl = DictConfigCtl(self._cfg_item_creg)
        ctr = FixtureObjCtr(
            module_name=self._module_name, 
            attr_name=fn.__name__,
            name=fn.__name__,
            ctl_ref=mosaic.put(ctl.piece),
            params=tuple(inspect.signature(fn).parameters),
            )
        self._ctr_collector.add_constructor(ctr)
        return fn


class FixtureMarker:

    def __init__(self, module_name, cfg_item_creg, ctr_collector):
        self._module_name = module_name
        self._cfg_item_creg = cfg_item_creg
        self._ctr_collector = ctr_collector

    def __call__(self, fn):
        if '.' in fn.__qualname__:
            raise RuntimeError(f"Only free functions are suitable for fixtures: {fn!r}")
        # TODO: Add parameterized case for fixture marker, with ability to specify custom ctl,
        # like for service marker.
        ctl = DictConfigCtl(self._cfg_item_creg)
        ctr = FixtureProbeCtr(
            module_name=self._module_name, 
            attr_name=fn.__name__,
            name=fn.__name__,
            ctl_ref=mosaic.put(ctl.piece),
            params=tuple(inspect.signature(fn).parameters),
            )
        self._ctr_collector.add_constructor(ctr)
        return fn

    @property
    def obj(self):
        return FixtureObjMarker(self._module_name, self._cfg_item_creg, self._ctr_collector)
