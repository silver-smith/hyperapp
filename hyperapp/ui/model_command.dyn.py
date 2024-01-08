import logging

from . import htypes
from .services import (
    association_reg,
    data_to_res,
    pyobj_creg,
    )

log = logging.getLogger(__name__)


class ModelCommand:

    def __init__(self, fn, ctl, widget, wrapper, params=None):
        self._fn = fn
        self._ctl = ctl
        self._widget = widget
        self._wrapper = wrapper
        self._params = params or []

    @property
    def name(self):
        return self._fn.__name__

    async def run(self):
        log.info("Run: %s", self._fn)
        kw = {}
        if 'state' in self._params:
            kw['state'] = self._ctl.widget_state(self._widget)
        result = await self._fn(**kw)
        log.info("Run result: %s -> %r", self._fn, result)
        return self._wrapper(result)


@pyobj_creg.actor(htypes.ui.global_model_command)
def model_command_from_piece(piece, ctl, widget, wrapper):
    fn = pyobj_creg.invite(piece.function)
    return ModelCommand(fn, ctl, widget, wrapper)


def global_commands():
    d_res = data_to_res(htypes.ui.global_model_command_d())
    command_list = association_reg.get_all(d_res)
    return command_list
