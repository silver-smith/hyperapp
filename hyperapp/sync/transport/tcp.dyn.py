import logging
from selectors import DefaultSelector

from hyperapp.common.module import Module

log = logging.getLogger(__name__)


class Selector:

    def __init__(self):
        self._selector = DefaultSelector()


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name)
