from hyperapp.common.htypes import ref_t
from hyperapp.common.module import Module

from . import htypes
from .object import Object


class RefObject(Object):

    type = htypes.ref_ot.ref_ot(command_list=())

    @classmethod
    def from_state(cls, state):
        return cls(state)

    def __init__(self, ref):
        self._ref = ref
        super().__init__()

    @property
    def title(self):
        return 'Ref'

    @property
    def piece(self):
        return self._ref

    @property
    def value(self):
        return str(self._ref)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)
        services.object_registry.register_actor(ref_t, RefObject.from_state)
