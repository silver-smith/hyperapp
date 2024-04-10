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
from .code.ui_command import CommandBase
log = logging.getLogger(__name__)


class ModelCommand(CommandBase):

    def __init__(self, name, d, fn, params, view, model_piece, widget, wrappers):
        super().__init__(name, d, fn, view, widget, wrappers)
        self._params = params
        self._model_piece = model_piece

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
    command_d = pyobj_creg.invite(piece.d)
    fn = pyobj_creg.invite(piece.function)
    return ModelCommand(piece.name, command_d, fn, piece.params, view, model_piece, widget, wrappers)


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


def enum_model_commands(piece, model_state):
    try:
        t = deduce_value_type(piece)
    except DeduceTypeError:
        return []
    t_res = pyobj_creg.reverse_resolve(t)
    d_res = data_to_res(htypes.ui.model_command_enumerator_d())
    enumerator_list = association_reg.get_all((d_res, t_res))
    for enumerator in enumerator_list:
        fn = pyobj_creg.invite(enumerator.function)
        params = set(enumerator.params)
        kw = {}
        if 'piece' in params:
            kw['piece'] = piece
            params.remove('piece')
        kw.update({
            name: getattr(model_state, name)
            for name in params
            })
        yield from fn(**kw)
