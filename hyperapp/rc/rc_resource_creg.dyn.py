from .services import (
    code_registry_ctr,
    mark,
    )


@mark.service
def rc_resource_creg():
    return code_registry_ctr('rc-resource')
