from .services import (
    code_registry_ctr,
    mark,
    )


@mark.service
def view_creg():
    return code_registry_ctr('view')
