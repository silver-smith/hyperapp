import inspect

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )


def fn_to_piece(obj):
    if inspect.isfunction(obj) or inspect.isclass(obj):
        module = inspect.getmodule(obj)
        try:
            module_ref = pyobj_creg.actor_to_ref(module, reconstruct=False)
        except KeyError:
            # Not a known dynamic module.
            return None
        return htypes.builtin.attribute(
            object=module_ref,
            attr_name=obj.__name__,
            )
    if inspect.ismethod(obj) and inspect.isclass(obj.__self__):
        cls = fn_to_piece(obj.__self__)
        return htypes.builtin.attribute(
            object=mosaic.put(cls),
            attr_name=obj.__name__,
            )
    return None
