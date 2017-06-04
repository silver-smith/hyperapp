import logging
from ..common import module_manager as common_module_manager

log = logging.getLogger(__name__)


class ModuleManager(common_module_manager.ModuleManager):

    def __init__(self, services, type_registry_registry, packet_types):
        common_module_manager.ModuleManager.__init__(self, services, type_registry_registry, packet_types)

    def add_code_module(self, module):
        log.info('loading server code module %r package=%r fpath=%r', module.id, module.package, module.fpath)
        self.load_code_module(module)
