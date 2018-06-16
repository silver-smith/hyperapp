from pathlib import Path
import sys
from types import SimpleNamespace
import logging
import abc

from hyperapp.common.htypes import (
    make_root_type_namespace,
    )
from hyperapp.common.type_module_repository import TypeModuleRepository


log = logging.getLogger(__name__)


TYPE_MODULE_EXT = '.types'
HYPERAPP_DIR = Path(__file__).parent.joinpath('../..').resolve()


class ServicesBase(object, metaclass=abc.ABCMeta):

    def __init__(self):
        self.hyperapp_dir = HYPERAPP_DIR / 'hyperapp'
        self.interface_dir = HYPERAPP_DIR / 'hyperapp' / 'common' / 'interface'
        self.on_start = []
        self.on_stop = []
        self.config = {}
        self.failure_reason_list = []
        self._is_stopped = False

    def init_services(self, config=None):
        self.config.update(config or {})
        self.types = make_root_type_namespace()
        self.type_module_repository = TypeModuleRepository(self.types)

    def start(self):
        for start in self.on_start:
            start()

    def stop(self):
        if self._is_stopped:
            log.info('Already stopped.')
            return
        log.info('Stopping modules...')
        for stop in self.on_stop:
            stop()
        log.info('Stopping modules: done')
        self.on_stopped()
        self._is_stopped = True

    def failed(self, reason):
        log.error('Failed: %r', reason)
        self.failure_reason_list.append(reason)
        self.schedule_stopping()

    @abc.abstractmethod
    def schedule_stopping(self):
        pass

    @property
    def is_failed(self):
        return self.failure_reason_list != []

    def on_stopped(self):
        pass

    def _load_type_module(self, module_name):
        fpath = self.interface_dir.joinpath(module_name + TYPE_MODULE_EXT)
        self.type_module_repository.load_type_module(module_name, fpath)
        
    def _load_type_modules(self, module_name_list):
        for module_name in module_name_list:
            self._load_type_module(module_name)
