from hyperapp.common.htypes import tString
from hyperapp.common.module import Module

from . import htypes
from .object import Object


class StringObject(Object):

    dir_list = [
        *Object.dir_list,
        [htypes.string_object.string_object_d()],
        ]

    @classmethod
    def from_state(cls, state):
        return cls(state)

    def __init__(self, value):
        self._value = value
        super().__init__()

    @property
    def title(self):
        return 'String'

    @property
    def piece(self):
        return self._value

    def get_value(self):
        return self._value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self._notify_object_changed()

    def value_changed(self, new_value, emitter_view=None):
        log.debug('string_object.value_changed: %r', new_value)
        self._value = new_value
        self._notify_object_changed(emitter_view)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.object_registry.register_actor(tString, StringObject.from_state)
