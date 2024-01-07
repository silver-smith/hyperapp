import logging

from . import htypes
from .services import (
    association_reg,
    data_to_res,
    pyobj_creg,
    )

log = logging.getLogger(__name__)


class ModelCommand:

    def __init__(self, fn, wrapper):
        self._fn = fn
        self._wrapper = wrapper

    @property
    def name(self):
        return self._fn.__name__

    async def run(self):
        log.info("Run: %s", self._fn)
        result = await self._fn()
        log.info("Run result: %s -> %r", self._fn, result)
        return self._wrapper(result)


@pyobj_creg.actor(htypes.ui.global_model_command)
def model_command_from_piece(piece, wrapper):
    fn = pyobj_creg.invite(piece.function)
    return ModelCommand(fn, wrapper)


def global_commands():
    d_res = data_to_res(htypes.ui.global_model_command_d())
    command_list = association_reg.get_all(d_res)
    return command_list
