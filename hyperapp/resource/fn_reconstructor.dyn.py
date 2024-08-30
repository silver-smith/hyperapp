import inspect

from . import htypes
from .services import (
    pyobj_creg,
    )


def fn_to_piece(fn):
    module = inspect.getmodule(fn)
    try:
        module_ref = pyobj_creg.actor_to_ref(module, reconstruct=False)
    except KeyError:
        # Not a known dynamic module.
        return None
    return htypes.builtin.attribute(
        object=module_ref,
        attr_name=fn.__name__,
        )
