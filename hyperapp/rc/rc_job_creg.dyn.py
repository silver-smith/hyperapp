from .services import (
    code_registry_ctr,
    )


def rc_job_creg(config):
    return code_registry_ctr('rc_job_creg', config)
