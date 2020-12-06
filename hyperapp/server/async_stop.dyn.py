import concurrent.futures
import logging

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class ThisModule(Module):

    def __init__(self, module_name, services):
        super().__init__(module_name)
        self._services_stop = services.stop
        self._failure_reason_list = []
        self._thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=3)
        services.failed = self.failed
        services.is_failed = self.is_failed

    def failed(self, reason):
        _log.error('Failed: %r', reason)
        self._failure_reason_list.append(reason)
        log.debug('Scheduling server stop...')
        self._thread_pool.submit(self._stop)

    def is_failed(self):
        return self._failure_reason_list != []

    def _stop(self):
        log.debug('Stopping thread pool...')
        self._thread_pool.shutdown(wait=False)
        self._services_stop()
