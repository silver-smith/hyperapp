import logging
import weakref

from hyperapp.common.htypes.deduce_value_type import DeduceTypeError, deduce_value_type

from . import htypes
from .services import (
    association_reg,
    data_to_res,
    mark,
    model_command_impl_creg,
    pyobj_creg,
    )
from .code.command import FnCommandImpl

log = logging.getLogger(__name__)


class ModelCommandImpl(FnCommandImpl):
    pass


@model_command_impl_creg.actor(htypes.ui.model_command_impl)
def model_command_from_piece(piece, ctx):
    fn = pyobj_creg.invite(piece.function)
    return ModelCommandImpl(ctx, fn, piece.params)


@mark.service
def global_commands():

    def _global_commands():
        d_res = data_to_res(htypes.ui.global_model_command_d())
        command_list = association_reg.get_all(d_res)
        return command_list

    return _global_commands


@mark.service
def model_command_factory():

    def _model_commands(piece):
        try:
            t = deduce_value_type(piece)
        except DeduceTypeError:
            return []
        t_res = pyobj_creg.reverse_resolve(t)
        d_res = data_to_res(htypes.ui.model_command_d())
        command_list = association_reg.get_all((d_res, t_res))
        return command_list

    return _model_commands


@mark.service
def enum_model_commands():

    def _enum_model_commands(piece, ctx):
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
                name: getattr(ctx, name)
                for name in params
                })
            yield from fn(**kw)

    return _enum_model_commands
