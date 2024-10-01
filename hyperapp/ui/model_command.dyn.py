import logging
from functools import partial

from .services import (
    pyobj_creg,
    )
from .code.mark import mark
from .code.command import UnboundCommand, BoundCommand

log = logging.getLogger(__name__)



class UnboundModelCommand(UnboundCommand):

    def __init__(self, d, fn, ctx_params, properties):
        super().__init__(d, fn, ctx_params)
        self._properties = properties

    def bind(self, ctx):
        return BoundModelCommand(self._d, self._fn, self._ctx_params, ctx, self._properties)


class BoundModelCommand(BoundCommand):

    def __init__(self, d, fn, ctx_params, ctx, properties):
        super().__init__(d, fn, ctx_params, ctx)
        self._properties = properties

    @property
    def properties(self):
        return self._properties


@mark.actor.command_creg
def model_command_from_piece(piece, system):
    kw = {
        name: system.resolve_service(name)
        for name in piece.service_params
        }
    fn = pyobj_creg.invite(piece.function)
    return UnboundModelCommand(
        d=pyobj_creg.invite(piece.d),
        fn=partial(fn, **kw),
        ctx_params=piece.ctx_params,
        properties=piece.properties,
        )


@mark.service2
def global_model_command_reg(config):
    return config


# @mark.service
# def model_commands():

#     def _model_commands(piece):
#         try:
#             t = deduce_value_type(piece)
#         except DeduceTypeError:
#             return []
#         t_res = pyobj_creg.actor_to_piece(t)
#         d_res = data_to_res(htypes.ui.model_command_d())
#         command_list = association_reg.get_all((d_res, t_res))
#         return command_list

#     return _model_commands


# @mark.service
# def enum_model_commands():

#     def _enum_model_commands(piece, ctx):
#         try:
#             t = deduce_value_type(piece)
#         except DeduceTypeError:
#             return []
#         t_res = pyobj_creg.actor_to_piece(t)
#         d_res = data_to_res(htypes.ui.model_command_enumerator_d())
#         enumerator_list = association_reg.get_all((d_res, t_res))
#         for enumerator in enumerator_list:
#             fn = pyobj_creg.invite(enumerator.function)
#             params = set(enumerator.params)
#             kw = {}
#             if 'piece' in params:
#                 kw['piece'] = piece
#                 params.remove('piece')
#             kw.update({
#                 name: getattr(ctx, name)
#                 for name in params
#                 })
#             yield from fn(**kw)

#     return _enum_model_commands


# @mark.service
# def model_command_factory():
#     def _model_command_factory(piece, ctx):
#         command_d = pyobj_creg.invite(piece.d)
#         impl = model_command_impl_creg.invite(piece.impl, ctx)
#         return ModelCommand(command_d, impl)
#     return _model_command_factory
