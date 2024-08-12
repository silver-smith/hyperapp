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
