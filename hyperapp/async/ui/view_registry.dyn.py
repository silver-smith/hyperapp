import logging
import weakref
from collections import defaultdict, namedtuple

from .async_registry import run_awaitable_factory
from .code_registry import CodeRegistry
from .module import ClientModule

_log = logging.getLogger(__name__)


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        # todo: rename view to layout
        services.available_view_registry = {}  # id -> view ref, views available to add to layout
        services.view_registry = CodeRegistry('view', services.async_web, services.types)
        services.object_layout_registry = CodeRegistry('object_layout', services.async_web, services.types)
