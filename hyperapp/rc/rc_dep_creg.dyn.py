from .services import (
    code_registry_ctr,
    mark,
    )


@mark.service
def rc_dep_creg():
    return code_registry_ctr('rc-dep')
