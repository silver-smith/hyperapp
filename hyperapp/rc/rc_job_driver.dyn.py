import logging

from .services import (
    rc_job_creg,
    )

log = logging.getLogger(__name__)


def run_rc_job(job_piece):
    job = rc_job_creg.animate(job_piece)
    log.info("Run job: %r", job)
