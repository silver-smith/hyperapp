import logging

log = logging.getLogger(__name__)


def run_rc_job(job_piece):
    log.info("Run job: %r", job_piece)
