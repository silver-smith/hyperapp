import logging

from hyperapp.common.module import Module

from . import htypes
from .command import command
from .object import Object

log = logging.getLogger(__name__)


class Selector(Object):

    dir_list = [
        *Object.dir_list,
        [htypes.selector.selector_d()],
        ]
    view_state_fields = ['list_view_state_ref']

    @classmethod
    async def from_piece(cls, piece, mosaic, web, object_animator):
        list = await object_animator.invite(piece.list_ref)
        return cls(mosaic, web, list)

    def __init__(self, mosaic, web, list):
        super().__init__()
        self._mosaic = mosaic
        self._web = web
        self._list = list
        
    @property
    def piece(self):
        list_ref = self._mosaic.put(self._list.piece)
        return htypes.selector.selector(list_ref)

    @property
    def title(self):
        return f"Selector: {self._list.title}"

    @property
    def command_list(self):
        return [
            *self._list.command_list,
            *super().command_list,
            ]

    @property
    def list_object(self):
        return self._list

    @command
    async def select(self, list_view_state_ref):
        list_state = self._web.summon(list_view_state_ref)
        log.info("Selector: select: %r", list_state.current_key)


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.object_registry.register_actor(
            htypes.selector.selector,
            Selector.from_piece,
            services.mosaic,
            services.web,
            services.object_animator,
            )
