import logging
import sys
import threading
from collections import namedtuple

log = logging.getLogger(__name__)


_FailureReason = namedtuple('_FailureReason', 'reason exception')


def stop_signal():
    return threading.Event()


def system_failed(stop_signal):
    _failure_reason_list = []

    def failed(reason, exception):
        log.error('Failed: %r (%s)', reason, exception)
        _failure_reason_list.append(_FailureReason(reason, exception))
        log.debug('Signaling system to stop...')
        stop_signal.set()

    yield failed

    for reason in _failure_reason_list:
        log.error("System failure reason: %s", reason)
    if sys.exception() is not None:
        return  # Do not hide main exception if we have one.
    for reason in _failure_reason_list:
        if reason.exception:
            raise reason.exception
        else:
            raise RuntimeError(f"System failed: {reason.reason}")
