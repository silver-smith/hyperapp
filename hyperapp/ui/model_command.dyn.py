import inspect
import logging
from functools import partial

from .services import (
    deduce_t,
    pyobj_creg,
    )
from .code.mark import mark
from .code.command import UnboundCommand, BoundCommand
from .code.command_config_ctl import TypedCommandConfigCtl, UntypedCommandConfigCtl

log = logging.getLogger(__name__)


def model_command_ctx(ctx, model, model_state):
    return ctx.push(
        model=model,
        piece=model,
        model_state=model_state,
        **ctx.attributes(model_state),
        )


class UnboundModelCommand(UnboundCommand):

    def __init__(self, d, ctx_fn, properties):
        super().__init__(d, ctx_fn)
        self._properties = properties

    @property
    def properties(self):
        return self._properties

    def bind(self, ctx):
        return BoundModelCommand(self._d, self._ctx_fn, ctx, self._properties)


class BoundModelCommand(BoundCommand):

    def __init__(self, d, ctx_fn, ctx, properties):
        super().__init__(d, ctx_fn, ctx)
        self._properties = properties

    @property
    def properties(self):
        return self._properties


@mark.actor.command_creg
def model_command_from_piece(piece, system_fn_creg):
    ctx_fn = system_fn_creg.invite(piece.system_fn)
    return UnboundModelCommand(
        d=pyobj_creg.invite(piece.d),
        ctx_fn=ctx_fn,
        properties=piece.properties,
        )


class UnboundModelCommandEnumerator:

    def __init__(self, ctx_fn):
        self._ctx_fn = ctx_fn

    def __repr__(self):
        return f"<CommandEnum: {self._ctx_fn}>"

    def enum_commands(self, ctx):
        # log.info("Run command enumerator: %r (%s)", self, kw)
        result = self._ctx_fn.call(ctx)
        assert not inspect.iscoroutine(result), f"Async command enumerators are not supported: {self._ctx_fn}"
        log.info("Run command enumerator %r result: [%s] %r", self, type(result), result)
        return result


@mark.actor.command_creg
def model_command_enumerator_from_piece(piece, system_fn_creg):
    ctx_fn = system_fn_creg.invite(piece.system_fn)
    return UnboundModelCommandEnumerator(
        ctx_fn=ctx_fn,
        )


@mark.service2(ctl=UntypedCommandConfigCtl())
def global_model_command_reg(config):
    return config


@mark.service2(ctl=TypedCommandConfigCtl())
def model_command_reg(config, model_t):
    return config.get(model_t, [])


@mark.service2(ctl=TypedCommandConfigCtl())
def model_command_enumerator_reg(config, model_t):
    return config.get(model_t, [])


@mark.service2
def get_model_commands(model_command_reg, model_command_enumerator_reg, model, ctx):
    model_t = deduce_t(model)
    command_list = [*model_command_reg(model_t)]
    for enumerator in model_command_enumerator_reg(model_t):
        command_list += enumerator.enum_commands(ctx)
    return command_list


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
