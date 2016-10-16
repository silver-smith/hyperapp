import logging
from ..common import module_manager as common_module_manager

log = logging.getLogger(__name__)


class ModuleManager(common_module_manager.ModuleManager):

    def __init__( self, services, type_module_registry ):
        common_module_manager.ModuleManager.__init__(self, services, type_module_registry)

    def add_code_module( self, module ):
        log.info('loading server code module %r package=%r fpath=%r', module.id, module.package, module.fpath)
        self._load_module(module)

    def _register_provided_services( self, module, module_dict ):
        this_module_class = module_dict.get('ThisModule')
        if this_module_class:
            module_dict['this_module'] = this_module_class(self._services)  # todo: remove auto-registation

