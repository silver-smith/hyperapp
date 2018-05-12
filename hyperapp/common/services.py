from pathlib import Path
import sys
from types import SimpleNamespace

from hyperapp.common.htypes import (
    make_root_type_namespace,
    )
from hyperapp.common.type_module_repository import TypeModuleRepository


TYPE_MODULE_EXT = '.types'
HYPERAPP_DIR = Path(__file__).parent.joinpath('../..').resolve()


class ServicesBase(object):

    def __init__(self):
        self.hyperapp_dir = HYPERAPP_DIR / 'hyperapp'
        self.interface_dir = HYPERAPP_DIR / 'hyperapp' / 'common' / 'interface'
        self.on_start = []
        self.on_stop = []
        self.config = {}

    def init_services(self, config=None):
        self.config.update(config or {})
        self.types = make_root_type_namespace()
        self.type_module_repository = TypeModuleRepository(self.types)

    def start(self):
        for start in self.on_start:
            start()

    def stop(self):
        for stop in self.on_stop:
            stop()

    def _load_type_module(self, module_name):
        fpath = self.interface_dir.joinpath(module_name + TYPE_MODULE_EXT)
        self.type_module_repository.load_type_module(module_name, fpath)
        
    def _load_type_modules(self, module_name_list):
        for module_name in module_name_list:
            self._load_type_module(module_name)
