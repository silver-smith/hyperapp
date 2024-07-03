from .services import (
    code_registry_ctr,
    mark,
    )


@mark.service
def rc_job_creg():
    return code_registry_ctr('rc-job')
