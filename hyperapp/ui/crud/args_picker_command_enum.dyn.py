import inspect
import logging

from . import htypes
from .services import (
    web,
    )
from .code.mark import mark
from .code.command import CommandKind
from .code.command_groups import default_command_groups
from .code.ui_command import UnboundUiCommand
from .code.args_picker_fn import ArgsPickerFn, args_dict_to_tuple, args_tuple_to_dict

log = logging.getLogger(__name__)


class UnboundArgsPickerCommandEnumerator:

    @classmethod
    @mark.actor.command_creg
    def from_piece(cls, piece, crud, system_fn_creg, editor_default_reg):
        args = args_tuple_to_dict(piece.args)
        args_picker_command_d = web.summon(piece.args_picker_command_d)
        commit_command_d = web.summon(piece.commit_command_d)
        commit_fn = system_fn_creg.invite(piece.commit_fn)
        return cls(
            crud=crud,
            system_fn_creg=system_fn_creg,
            editor_default_reg=editor_default_reg,
            name=piece.name,
            is_global=piece.is_global,
            args=args,
            args_picker_command_d=args_picker_command_d,
            commit_command_d=commit_command_d,
            commit_fn=commit_fn,
            )

    def __init__(self, crud, system_fn_creg, editor_default_reg, name, is_global, args, args_picker_command_d, commit_command_d, commit_fn):
        self._crud = crud
        self._system_fn_creg = system_fn_creg
        self._editor_default_reg = editor_default_reg
        self._name = name
        self._is_global = is_global
        self._args = args
        self._args_picker_command_d = args_picker_command_d
        self._commit_command_d = commit_command_d
        self._commit_fn = commit_fn

    def __repr__(self):
        return f"<ArgsPickerCommandEnum: {self._commit_fn}>"

    def enum_commands(self, ctx):
        log.info("Run args picker command enumerator: %r (%s)", self, self._args)
        fn = ArgsPickerFn(
            system_fn_creg=self._system_fn_creg,
            crud=self._crud,
            editor_default_reg=self._editor_default_reg,
            name=self._name,
            args=self._args,
            commit_command_d=self._commit_command_d,
            commit_fn=self._commit_fn,
            )
        properties = htypes.command.properties(
            is_global=self._is_global,
            uses_state=False,
            remotable=False,
            )
        command = UnboundUiCommand(
            d=self._args_picker_command_d,
            ctx_fn=fn,
            properties=properties,
            groups=default_command_groups(properties, CommandKind.VIEW),
            )
        result = [command]
        log.info("Run args picker command enumerator %r result: %r", self, result)
        return result
