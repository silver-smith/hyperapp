from .services import (
    code_registry_ctr2,
    )


def rc_job_creg(config):
    return code_registry_ctr2('rc-job', config)
