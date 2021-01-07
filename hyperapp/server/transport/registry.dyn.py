import logging

from hyperapp.common.module import Module
from hyperapp.common.code_registry import CodeRegistry

log = logging.getLogger(__name__)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
        services.transport_registry = CodeRegistry('transport', services.web, services.types)
        services.local_transport_ref_set = set()
