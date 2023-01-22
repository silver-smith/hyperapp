from .services import (
    mark,
    types,
    web,
    )
from .code.dyn_code_registry import DynCodeRegistry


@mark.service
def constructor_creg():
    return DynCodeRegistry('resource_ctr', web, types)
