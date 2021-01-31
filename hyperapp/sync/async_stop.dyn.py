import concurrent.futures
import logging
from collections import namedtuple

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class ThisModule(Module):

    _FailureReason = namedtuple('_FailureReason', 'reason exception')

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        self._services_stop = services.stop
        self._failure_reason_list = []
        self._thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=3)
        services.failed = self.failed
        services.is_failed = self.is_failed
        services.check_failures = self.check_failures
        services.get_failure_reason_list = self.get_failure_reason_list
        services.clear_failure_flag = self.clear_failure_flag

    def failed(self, reason, exception):
        log.error('Failed: %r (%s)', reason, exception)
        self._failure_reason_list.append(self._FailureReason(reason, exception))
        log.debug('Scheduling server stop...')
        self._thread_pool.submit(self._stop)

    def is_failed(self):
        return self._failure_reason_list != []

    def check_failures(self):
        for reason in self._failure_reason_list:
            if reason.exception:
                raise reason.exception
            else:
                raise RuntimeError(f"Services failed: {reason.reason}")

    def get_failure_reason_list(self):
        return self._failure_reason_list

    def clear_failure_flag(self):
        self._failure_reason_list.clear()
        
    def _stop(self):
        log.debug('Stopping thread pool...')
        self._thread_pool.shutdown(wait=False)
        self._services_stop()
