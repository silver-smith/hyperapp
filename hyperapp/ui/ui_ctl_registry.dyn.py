from .services import (
    mark,
    types,
    web,
    )
from .code.dyn_code_registry import DynCodeRegistry


@mark.service
def ui_ctl_creg():
    return DynCodeRegistry('ui_ctl', web, types)
