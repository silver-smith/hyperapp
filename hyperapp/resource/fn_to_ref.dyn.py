import inspect

from . import htypes
from .services import (
    mark,
    mosaic,
    pyobj_creg,
    )


@mark.service
def fn_to_ref():

    def _fn_to_ref(fn):
        module = inspect.getmodule(fn)
        module_res = pyobj_creg.reverse_resolve(module)
        fn_res = htypes.builtin.attribute(
            object=mosaic.put(module_res),
            attr_name=fn.__name__,
            )
        return mosaic.put(fn_res)

    return _fn_to_ref
