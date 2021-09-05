from hyperapp.common.module import Module

from . import htypes
from .ui_object import Object


class NoneObject(Object):

    @classmethod
    def from_state(cls, state):
        return cls()

    def __init__(self):
        super().__init__()

    @property
    def title(self):
        return 'None'

    @property
    def piece(self):
        return None

    @property
    def value(self):
        return '<None>'


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.object_registry.register_actor(None, NoneObject.from_state)
