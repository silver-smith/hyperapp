import inspect

from hyperapp.common.resource_ctr import add_fn_module_constructor

from . import htypes
from .services import mosaic


def service_marker(fn):
    ctr = htypes.rc_constructors.service_probe(
        attr_name=fn.__name__,
        name=fn.__name__,
        params=tuple(inspect.signature(fn).parameters),
        )
    add_fn_module_constructor(fn, mosaic.put(ctr))
    return fn
