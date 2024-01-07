from .services import (
    code_registry_ctr,
    mark,
    )


@mark.service
def constructor_creg():
    return code_registry_ctr('resource_ctr')
