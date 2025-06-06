import inspect
import logging

from hyperapp.boot.htypes.deduce_value_type import DeduceTypeError

from . import htypes
from .services import (
    deduce_t,
    mosaic,
    web,
    )
from .code.mark import mark
from .code.command import CommandKind
from .code.command_groups import default_command_groups
from .code.model_command import UnboundModelCommand
from .code.ui_command import UnboundUiCommand
from .code.arg_mark import model_mark_prefix, value_mark_name
from .code.canned_args_command_fn import CannedArgsCommandFn
from .code.command_args import args_dict_to_tuple, args_t_tuple_to_dict
from .code.args_picker_fn import ArgsPickerFn

log = logging.getLogger(__name__)


class UnboundArgsPickerCommandEnumerator:

    @classmethod
    @mark.actor.command_creg
    def from_piece(cls, piece, crud, editor_default_reg, rpc_system_call_factory, system_fn_creg):
        required_args = args_t_tuple_to_dict(piece.required_args)
        args_picker_command_d = web.summon(piece.args_picker_command_d)
        commit_command_d = web.summon(piece.commit_command_d)
        commit_fn = system_fn_creg.invite(piece.commit_fn)
        return cls(
            system_fn_creg=system_fn_creg,
            rpc_system_call_factory=rpc_system_call_factory,
            crud=crud,
            editor_default_reg=editor_default_reg,
            name=piece.name,
            is_global=piece.is_global,
            required_args=required_args,
            args_picker_command_d=args_picker_command_d,
            commit_command_d=commit_command_d,
            commit_fn=commit_fn,
            )

    def __init__(self, system_fn_creg, rpc_system_call_factory, crud, editor_default_reg, name, is_global, required_args,
                 args_picker_command_d, commit_command_d, commit_fn):
        self._system_fn_creg = system_fn_creg
        self._rpc_system_call_factory = rpc_system_call_factory
        self._crud = crud
        self._editor_default_reg = editor_default_reg
        self._name = name
        self._is_global = is_global
        self._required_args = required_args
        self._args_picker_command_d = args_picker_command_d
        self._commit_command_d = commit_command_d
        self._commit_fn = commit_fn

    def __repr__(self):
        return f"<ArgsPickerCommandEnum: {self._commit_fn}>"

    def enum_commands(self, ctx):
        log.debug("Run args picker command enumerator: %r (%s)", self, self._required_args)
        args, required_args = self._pick_args_from_context(ctx)
        if htypes.builtin.ref in required_args.values():
            log.warning("Args picker for references is not yet implemented")
            result = []
        else:
            if required_args:
                command = self._args_picker_command(args, required_args)
            else:
                command = self._canned_args_command(args)
            result = [command]
        log.debug("Run args picker command enumerator %r result: %r", self, result)
        return result

    def _args_picker_command(self, args, required_args):
        fn = ArgsPickerFn(
            system_fn_creg=self._system_fn_creg,
            crud=self._crud,
            editor_default_reg=self._editor_default_reg,
            name=self._name,
            args=args,
            required_args=required_args,
            commit_command_d=self._commit_command_d,
            commit_fn=self._commit_fn,
            )
        properties = htypes.command.properties(
            is_global=self._is_global,
            uses_state=False,
            remotable=False,
            )
        return self._make_command(self._args_picker_command_d, properties, fn)

    def _pick_args_from_context(self, ctx):
        args = {}
        required_args = {}
        for name, t in self._required_args.items():
            if t is htypes.builtin.ref:
                value = self._pick_ref_arg(ctx)
            else:
                value = self._pick_arg(ctx, name, t)
            if value is None:
                required_args[name] = t
            else:
                args[name] = value
        return (args, required_args)

    def _pick_arg(self, ctx, name, required_t):
        ctx_name = value_mark_name(required_t)
        try:
            value = ctx[ctx_name]
        except KeyError:
            return None
        try:
            value_t = deduce_t(value)
        except DeduceTypeError:
            return None
        if required_t is value_t:
            return value
        return None

    def _pick_ref_arg(self, ctx):
        for name, value in reversed(ctx.items()):
            if name.startswith(model_mark_prefix):
                return mosaic.put(value)
        return None

    def _canned_args_command(self, args):
        fn = CannedArgsCommandFn(self._rpc_system_call_factory, args, self._commit_fn)
        properties = htypes.command.properties(
            is_global=self._is_global,
            uses_state=False,
            remotable=False,
            )
        command_d = htypes.command.canned_arg_command_d(
            commit_command_d=mosaic.put(self._commit_command_d),
            args=args_dict_to_tuple(args),
            )
        return self._make_command(command_d, properties, fn)


class UnboundArgsPickerModelCommandEnumerator(UnboundArgsPickerCommandEnumerator):

    def _make_command(self, d, properties, fn):
        return UnboundModelCommand(d, fn, properties)


class UnboundArgsPickerUiCommandEnumerator(UnboundArgsPickerCommandEnumerator):

    def _make_command(self, d, properties, fn):
        groups = default_command_groups(properties, CommandKind.VIEW)
        return UnboundUiCommand(d, fn, properties, groups)


@mark.actor.formatter_creg
def format_open_args_picker_command_d(piece, format):
    commit_command_d = web.summon(piece.commit_command_d)
    commit_command_text = format(commit_command_d)
    return f"{commit_command_text}..."
