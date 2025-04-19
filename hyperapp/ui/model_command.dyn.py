import inspect
import logging
from functools import partial

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.system_fn import ContextFn
from .code.command import UnboundCommand, BoundCommand
from .code.command_enumerator import UnboundCommandEnumerator
from .code.list_config_ctl import DictListConfigCtl, FlatListConfigCtl

log = logging.getLogger(__name__)


def model_command_ctx(ctx, model, model_state):
    return ctx.push(
        model=model,
        piece=model,
        model_state=model_state,
        **ctx.attributes(model_state),
        )


class ModelCommandFnBase(ContextFn):

    @classmethod
    @mark.actor.system_fn_creg
    def from_piece(cls, piece, system, rpc_system_call_factory):
        return super().from_piece(piece, system, rpc_system_call_factory)

    @property
    def piece(self):
        return self._fn_t(
            function=pyobj_creg.actor_to_ref(self._raw_fn),
            ctx_params=tuple(self._ctx_params),
            service_params=tuple(self._service_params),
            )


class ModelCommandFn(ModelCommandFnBase):

    _fn_t = htypes.command.model_command_fn

    async def call(self, ctx, remote_peer=None, **kw):
        if remote_peer:
            rpc_call = self._rpc_system_call_factory(
                receiver_peer=remote_peer,
                sender_identity=ctx.identity,
                fn=self,
                )
            kw = self.call_kw(ctx)
            return rpc_call(**kw)
        result = super().call(ctx, **kw)
        if inspect.iscoroutine(result):
            result = await result
        return self._prepare_result(ctx, result)

    @staticmethod
    def _prepare_result(ctx, result):
        if isinstance(result, htypes.command.command_result):
            return result
        if result is None:
            return result
        if type(result) is tuple and len(result) == 2:
            model, key = result
        else:
            model = result
            key = None
        if type(model) is list:
            model = tuple(model)
        return htypes.command.command_result(
            model=mosaic.put_opt(model),
            key=mosaic.put_opt(key),
            diff=None,
            )


class ModelCommandAddFn(ModelCommandFn):

    _fn_t = htypes.command.model_command_add_fn

    @classmethod
    @mark.actor.system_fn_creg
    def from_piece(cls, piece, system, rpc_system_call_factory, model_servant):
        fn = pyobj_creg.invite(piece.function)
        bound_fn = system.bind_services(fn, piece.service_params)
        return cls(rpc_system_call_factory, piece.ctx_params, piece.service_params, fn, bound_fn, model_servant)

    def __init__(self, rpc_system_call_factory, ctx_params, service_params, raw_fn, bound_fn, model_servant):
        super().__init__(rpc_system_call_factory, ctx_params, service_params, raw_fn, bound_fn)
        self._model_servant = model_servant

    def _prepare_result(self, ctx, result):
        assert not isinstance(result, htypes.command.command_result)
        if result is None:
            return result
        servant = self._model_servant(ctx.piece)
        if servant.key_field_t is None:
            if type(result) is not int:
                raise RuntimeError(f"Result from add command for {ctx.piece} is expected to be an int: {result!r}")
        else:
            if not isinstance(result, servant.key_field_t):
                raise RuntimeError(f"Result from add command for {ctx.piece} is expected to be a {servant.key_field_t}: {result!r}")
        key_field = servant.key_field
        item_list = servant.fn.call(ctx)
        for idx, item in enumerate(item_list):
            if key_field:
                key = getattr(item, key_field)
            else:
                key = idx
            if key == result:
                break
        else:
            log.warning("No new items with key %r exists for add command %s", result, self)
            return
        assert 0, f'todo: {ctx.piece}/{result!r}/{item!r}'
        return htypes.command.command_result(
            model=mosaic.put_opt(model),
            key=mosaic.put_opt(key),
            diff=None,
            )


class ModelCommandEnumFn(ModelCommandFnBase):

    _fn_t = htypes.command.model_command_enum_fn

    def call(self, ctx, **kw):
        result = super().call(ctx, **kw)
        return self._prepare_result(result)

    @staticmethod
    def _prepare_result(result):
        if result is None:
            return result
        if type(result) is list:
            result = tuple(result)
        return result



class UnboundModelCommand(UnboundCommand):

    def __init__(self, d, ctx_fn, properties):
        super().__init__(d, ctx_fn)
        self._properties = properties

    @property
    def piece(self):
        return htypes.command.model_command(
            d=mosaic.put(self._d),
            properties=self._properties,
            system_fn=mosaic.put(self._ctx_fn.piece),
            )

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
        d=web.summon(piece.d),
        ctx_fn=ctx_fn,
        properties=piece.properties,
        )


@mark.actor.command_creg
def model_command_enumerator_from_piece(piece, system_fn_creg):
    ctx_fn = system_fn_creg.invite(piece.system_fn)
    return UnboundCommandEnumerator(
        ctx_fn=ctx_fn,
        )


class CommandDict:

    def __init__(self, command_list):
        self._command_list = command_list

    def __getitem__(self, d):
        return self._command_dict[d]

    def values(self):
        return self._command_list

    @property
    def _command_dict(self):
        d_to_command = {}
        for command in self._command_list:
            d_to_command[command.d] = command
        return d_to_command


@mark.service(ctl=FlatListConfigCtl())
def global_model_command_reg(config):
    return CommandDict(config)


@mark.service(ctl=DictListConfigCtl())
def model_command_reg(config, model_t):
    return config.get(model_t, [])


@mark.service(ctl=DictListConfigCtl())
def model_command_enumerator_reg(config, model_t):
    return config.get(model_t, [])


# @mark.service(ctl=FlatListConfigCtl())
# def global_model_command_enumerator_reg(config):
#     return CommandDict(config)


@mark.service
def get_model_commands(model_command_reg, model_command_enumerator_reg, model_t, ctx):
    command_list = [*model_command_reg(model_t)]
    for enumerator in model_command_enumerator_reg(model_t):
        command_list += enumerator.enum_commands(ctx)
    return command_list
