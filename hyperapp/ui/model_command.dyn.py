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

    @property
    def params(self):
        params = {
            'view': self._view.piece,
            }
        widget = self._widget()
        if widget is not None:
            state = self._view.model_state(widget)
            params['state'] = state
            for name in dir(state):
                if not name.startswith('_'):
                    params[name] = getattr(state, name)
        if self._model is not None:
            params['piece'] = self._model
        return params


@model_command_creg.actor(htypes.ui.model_command)
def model_command_from_piece(piece, view, model_piece, widget, wrappers):
    command_d = {pyobj_creg.invite(d) for d in piece.d}
    fn = pyobj_creg.invite(piece.function)
    return ModelCommand(piece.name, command_d, fn, piece.params, model_piece, view, widget, wrappers)


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
