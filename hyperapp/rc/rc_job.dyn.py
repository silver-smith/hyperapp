import logging

from . import htypes
from .services import (
    mosaic,
    )

log = logging.getLogger(__name__)


def rc_job_submit_factory(rpc_submit_target_factory, receiver_peer, sender_identity):
    submit_factory = rpc_submit_target_factory(receiver_peer, sender_identity)

    def submit(job):
        target = htypes.rc_job.job_target(
            job=mosaic.put(job.piece),
            )
        log.info("Submit rc job: receiver=%s: %s; target: %s", receiver_peer, job, target)
        return submit_factory(target)

    return submit


def run_job_target(target, rpc_request, rc_job_creg):
    log.debug("Resolve rc job: %s", target.job)
    job = rc_job_creg.invite(target.job)
    log.info("Run job: %s", job)
    result = job.run()
    log.info("Job completed: %r; result: %s", job, result)
    return result
