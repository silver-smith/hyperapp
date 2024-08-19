import inspect

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )


def _fn_to_res(fn):
    module = inspect.getmodule(fn)
    module_ref = pyobj_creg.actor_to_ref(module)
    return htypes.builtin.attribute(
        object=module_ref,
        attr_name=fn.__name__,
        )


def fn_to_res():
    return _fn_to_res


def fn_to_ref():
    def _fn_to_ref(fn):
        return mosaic.put(_fn_to_res(fn))
    return _fn_to_ref
