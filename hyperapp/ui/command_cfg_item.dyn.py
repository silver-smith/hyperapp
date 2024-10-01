from . import htypes
from .services import pyobj_creg
from .code.mark import mark


class TypedCommandCfgItem:

    @classmethod
    @mark.actor.cfg_item_creg
    def from_piece(cls, piece):
        return cls(
            t=pyobj_creg.invite(piece.t),
            command_ref=piece.command,
            )

    def __init__(self, t, command_ref):
        self._t = t
        self._command_ref = command_ref

    @property
    def piece(self):
        return htypes.command.cfg_item(
            t=pyobj_creg.actor_to_ref(self._t),
            command=self._command_ref,
            )

    @property
    def key(self):
        return self._t

    def resolve(self, system, service_name):
        command_creg = system.resolve_service('command_creg')
        return command_creg.invite(self._command_ref)


class UntypedCommandCfgItem:

    @classmethod
    @mark.actor.cfg_item_creg
    def from_piece(cls, piece):
        return cls(
            command=piece,
            )

    def __init__(self, command):
        self._command = command

    @property
    def piece(self):
        return self._command

    def resolve(self, system, service_name):
        command_creg = system.resolve_service('command_creg')
        return command_creg.animate(self._command)
