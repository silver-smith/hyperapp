from hyperapp.common.htypes import tString
from hyperapp.common.module import Module

from . import htypes


class StringAdapter:

    @classmethod
    async def from_piece(cls, impl, object, python_object_creg):
        return cls(text=piece)

    def __init__(self, text):
        self._text = text

    @property
    def dir_list(self):
        return [
            [htypes.text.text_d()],
            ]

    @property
    def text(self):
        return self._text

    @property
    def title(self):
        return 'todo: string adapter title'


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.adapter_registry.register_actor(
            htypes.impl.string_spec, StringAdapter.from_piece, services.python_object_creg)
        services.impl_registry[tString] = (None, htypes.impl.string_spec())
