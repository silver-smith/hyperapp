import logging
from collections import namedtuple

from .services import (
    mark,
    on_stop,
    stop_signal,
    )

log = logging.getLogger(__name__)


_FailureReason = namedtuple('_FailureReason', 'reason exception')

_failure_reason_list = []


def _on_stop():
    for reason in _failure_reason_list:
        log.error("Services failure reason: %s", reason)
    for reason in _failure_reason_list:
        if reason.exception:
            raise reason.exception
        else:
            raise RuntimeError(f"Services failed: {reason.reason}")


@mark.service
def failed():
    def _failed(reason, exception):
        log.error('Failed: %r (%s)', reason, exception)
        _failure_reason_list.append(_FailureReason(reason, exception))
        log.debug('Signaling server to stop...')
        stop_signal.set()
    return _failed


on_stop.append(_on_stop)
