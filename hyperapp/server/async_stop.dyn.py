import concurrent.futures
import logging

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        self._services_stop = services.stop
        self._failure_reason_list = []
        self._thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=3)
        services.failed = self.failed
        services.is_failed = self.is_failed
        services.get_failure_reason_list = self.get_failure_reason_list
        services.clear_failure_flag = self.clear_failure_flag

    def failed(self, reason):
        log.error('Failed: %r', reason)
        self._failure_reason_list.append(reason)
        log.debug('Scheduling server stop...')
        self._thread_pool.submit(self._stop)

    def is_failed(self):
        return self._failure_reason_list != []

    def get_failure_reason_list(self):
        return self._failure_reason_list

    def clear_failure_flag(self):
        self._failure_reason_list.clear()
        
    def _stop(self):
        log.debug('Stopping thread pool...')
        self._thread_pool.shutdown(wait=False)
        self._services_stop()
