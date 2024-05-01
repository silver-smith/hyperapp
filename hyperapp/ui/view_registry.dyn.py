from .services import (
    code_registry_ctr,
    mark,
    )


@mark.service
def view_creg():
    return code_registry_ctr('view')


@mark.service
def model_view_creg():
    return code_registry_ctr('model_view')
