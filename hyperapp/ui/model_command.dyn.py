import logging
import weakref

from . import htypes
from .services import (
    association_reg,
    data_to_res,
    model_command_creg,
    pyobj_creg,
    )

log = logging.getLogger(__name__)


class ModelCommand:

    def __init__(self, fn, params, ctl, widget, wrapper):
        self._fn = fn
        self._params = params
        self._ctl = ctl
        self._widget = weakref.ref(widget)
        self._wrapper = wrapper

    @property
    def name(self):
        return self._fn.__name__

    async def run(self):
        widget = self._widget()
        if widget is None:
            log.warning("Widget for command %s is gone; won't run", self._fn)
            return
        kw = {}
        if 'state' in self._params:
            kw['state'] = self._ctl.widget_state(widget)
        log.info("Run: %s (%s)", self._fn, kw)
        result = await self._fn(**kw)
        log.info("Run result: %s -> %r", self._fn, result)
        return self._wrapper(result)


@model_command_creg.actor(htypes.ui.model_command)
def model_command_from_piece(piece, ctl, widget, wrapper):
    fn = pyobj_creg.invite(piece.function)
    return ModelCommand(fn, piece.params, ctl, widget, wrapper)


def global_commands():
    d_res = data_to_res(htypes.ui.global_model_command_d())
    command_list = association_reg.get_all(d_res)
    return command_list
