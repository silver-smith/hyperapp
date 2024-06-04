import inspect

from . import htypes
from .services import (
    mark,
    mosaic,
    pyobj_creg,
    )


def _fn_to_res(fn):
    module = inspect.getmodule(fn)
    module_res = pyobj_creg.actor_to_piece(module)
    return htypes.builtin.attribute(
        object=mosaic.put(module_res),
        attr_name=fn.__name__,
        )


@mark.service
def fn_to_res():
    return _fn_to_res


@mark.service
def fn_to_ref():
    def _fn_to_ref(fn):
        return mosaic.put(_fn_to_res(fn))
    return _fn_to_ref
