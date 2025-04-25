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
from .code.list_diff import IndexListDiff, KeyListDiff
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
            return await self._remote_call(ctx, remote_peer, **kw)
        else:
            return await self._local_call(ctx, **kw)

    async def _remote_call(self, ctx, remote_peer, **kw):
        rpc_call = self._rpc_system_call_factory(
            receiver_peer=remote_peer,
            sender_identity=ctx.identity,
            fn=self,
            )
        call_kw = self.call_kw(ctx, **kw)
        result = rpc_call(**call_kw)
        if inspect.iscoroutine(result):
            # Special case for test fixtures.
            result = await result
        return result

    async def _local_call(self, ctx, **kw):
        result = super().call(ctx, **kw)
        if inspect.iscoroutine(result):
            result = await result
        if kw:
            kw_ctx = ctx.clone_with(**kw)
        else:
            kw_ctx = ctx
        return self._prepare_result(kw_ctx, result)

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


class ModelCommandOpFn(ModelCommandFn):

    @classmethod
    @mark.actor.system_fn_creg
    def from_piece(cls, piece, system, rpc_system_call_factory, model_servant):
        fn = pyobj_creg.invite(piece.function)
        bound_fn = system.bind_services(fn, piece.service_params)
        return cls(rpc_system_call_factory, model_servant, piece.ctx_params, piece.service_params, fn, bound_fn)

    def __init__(self, rpc_system_call_factory, model_servant, ctx_params, service_params, raw_fn, bound_fn):
        super().__init__(rpc_system_call_factory, ctx_params, service_params, raw_fn, bound_fn)
        self._model_servant = model_servant

    @staticmethod
    def _ctx_model(ctx):
        try:
            return ctx.model
        except KeyError:
            return ctx.piece

    @staticmethod
    def _diff_model(ctx, model):
        if not ctx.get('request'):
            return model
        peer = ctx.request.receiver_identity.peer
        return htypes.model.remote_model(
            model=mosaic.put(model),
            remote_peer=mosaic.put(peer.piece),
            )


class ModelCommandAddFn(ModelCommandOpFn):

    _fn_t = htypes.command.model_command_add_fn

    def _prepare_result(self, ctx, result):
        assert not isinstance(result, htypes.command.command_result)
        if result is None:
            return result
        model = self._ctx_model(ctx)
        servant = self._model_servant(model)
        if servant.key_field_t is None:
            if type(result) is not int:
                raise RuntimeError(f"Result from 'add' command for {model} is expected to be an int: {result!r}")
            Diff = IndexListDiff.Append
        else:
            if not isinstance(result, servant.key_field_t):
                raise RuntimeError(f"Result from 'add' command for {model} is expected to be a {servant.key_field_t}: {result!r}")
            Diff = KeyListDiff.Append
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
            log.warning("No new items with key %r exists for 'Add' command %s", result, self)
            return
        diff = Diff(item)
        model_diff = htypes.diff.model_diff(
            model=mosaic.put(self._diff_model(ctx, model)),
            diff=mosaic.put(diff.piece),
            )
        return htypes.command.command_result(
            model=None,
            key=mosaic.put(key),
            diff=mosaic.put(model_diff),
            )


class ModelCommandRemoveFn(ModelCommandOpFn):

    _fn_t = htypes.command.model_command_remove_fn

    def _prepare_result(self, ctx, result):
        assert not isinstance(result, htypes.command.command_result)
        if result is None:
            return result
        if type(result) is not bool:
            raise RuntimeError(f"Result from 'remove' command for {model} should be None or bool: {result!r}")
        if not result:
            return
        model = self._ctx_model(ctx)
        servant = self._model_servant(model)
        if servant.key_field_t is None:
            idx = self._ctx_idx(ctx, model)
            diff = IndexListDiff.Remove(idx=idx)
        else:
            param_name, key = self._ctx_key(ctx, servant.key_field)
            if not isinstance(key, servant.key_field_t):
                raise RuntimeError(f"'Remove' command parameter {param_name!r} for {model} is expected to be a {servant.key_field_t}: {key!r}")
            diff = KeyListDiff.Remove(key=key)
        model_diff = htypes.diff.model_diff(
            model=mosaic.put(self._diff_model(ctx, model)),
            diff=mosaic.put(diff.piece),
            )
        return htypes.command.command_result(
            model=None,
            key=None,
            diff=mosaic.put(model_diff),
            )

    @staticmethod
    def _ctx_idx(ctx, model):
        try:
            idx = ctx.current_idx
            if type(idx) is not int:
                raise RuntimeError(f"'Remove' command parameter {param_name!r} for {model} is expected to be an int: {idx!r}")
            return idx
        except KeyError:
            pass
        if 'current_item' in ctx:
            raise RuntimeError(f"TODO: Remove command: Produce 'current_idx' for {model} from 'current_item' parameter")
        raise RuntimeError(
            f"'Remove' command from indexed model {model} should have at least one of parameters: 'current_idx', 'current_item'")

    @staticmethod
    def _ctx_key(ctx, key_field):
        key_param = f'current_{key_field}'
        for name in ['current_key', key_param]:
            try:
                return (name, ctx[name])
            except KeyError:
                pass
        try:
            current_item = ctx.current_item
        except KeyError:
            raise RuntimeError(
                f"'Remove' command from keyed model should have at least one of parameters:"
                f" 'current_key', {key_param!r}, 'current_item'"
                )
        key = getattr(current_item, key_field)
        return (f'current_item.{key_field}', key)


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
