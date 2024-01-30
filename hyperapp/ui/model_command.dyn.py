import logging
import weakref

from hyperapp.common.htypes.deduce_value_type import DeduceTypeError, deduce_value_type

from . import htypes
from .services import (
    association_reg,
    data_to_res,
    model_command_creg,
    pyobj_creg,
    )

log = logging.getLogger(__name__)


class ModelCommand:

    def __init__(self, fn, params, view, model_piece, widget, wrappers):
        self._fn = fn
        self._params = params
        self._view = view
        self._model_piece = model_piece
        self._widget = weakref.ref(widget)
        self._wrappers = wrappers

    @property
    def name(self):
        return self._fn.__name__

    async def run(self):
        widget = self._widget()
        if widget is None:
            log.warning("Widget for command %s is gone; won't run", self._fn)
            return
        kw = {}
        params = [*self._params]
        if params[:1] == ['piece']:
            kw['piece'] = self._model_piece
            params.pop(0)
        state = self._view.model_state(widget)
        if params[:1] == ['state']:
            kw['state'] = state
            params.pop(0)
        for name in params:
            kw[name] = getattr(state, name)
        log.info("Run model command: %r (%s)", self.name, kw)
        result = await self._fn(**kw)
        log.info("Run model command %r result: [%s] %r", self.name, type(result), result)
        for wrapper in reversed(self._wrappers):
            result = wrapper(result)
        log.info("Run model command %r wrapped result: [%s] %r", self.name, type(result), result)
        return result


@model_command_creg.actor(htypes.ui.model_command)
def model_command_from_piece(piece, view, model_piece, widget, wrappers):
    fn = pyobj_creg.invite(piece.function)
    return ModelCommand(fn, piece.params, view, model_piece, widget, wrappers)


def global_commands():
    d_res = data_to_res(htypes.ui.global_model_command_d())
    command_list = association_reg.get_all(d_res)
    return command_list


def model_commands(piece):
    try:
        t = deduce_value_type(piece)
    except DeduceTypeError:
        return []
    t_res = pyobj_creg.reverse_resolve(t)
    d_res = data_to_res(htypes.ui.model_command_d())
    command_list = association_reg.get_all((d_res, t_res))
    return command_list
