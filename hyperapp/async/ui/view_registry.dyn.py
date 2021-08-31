import logging

from hyperapp.common.module import Module

from .code_registry import CodeRegistry

_log = logging.getLogger(__name__)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.view_registry = CodeRegistry('view', services.async_web, services.types)
