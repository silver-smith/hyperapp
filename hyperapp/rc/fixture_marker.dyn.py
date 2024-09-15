import inspect

from .services import mosaic
from .code.config_ctl import ItemDictConfigCtl
from .code.fixture_ctr import FixtureCtr


def fixture_marker(fn, module_name, cfg_item_creg, ctr_collector):
    if '.' in fn.__qualname__:
        raise RuntimeError(f"Only free functions are suitable for fixtures: {fn!r}")
    # TODO: Add parameterized case for fixture marker, with ability to specify custom ctl,
    # like for service marker.
    ctl = ItemDictConfigCtl(cfg_item_creg)
    ctr = FixtureCtr(
        module_name=module_name, 
        attr_name=fn.__name__,
        name=fn.__name__,
        ctl_ref=mosaic.put(ctl.piece),
        params=tuple(inspect.signature(fn).parameters),
        )
    ctr_collector.add_constructor(ctr)
    return fn
