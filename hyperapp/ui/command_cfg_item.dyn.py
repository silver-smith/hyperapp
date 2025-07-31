from .services import pyobj_creg
from .code.mark import mark


@mark.actor.cfg_value_creg
def resolve_typed_command_cfg_value(piece, key, system, service_name):
    command_creg = system.resolve_service('command_creg')
    return command_creg.invite(piece.command)


@mark.actor.cfg_item_creg
def resolve_untyped_command_cfg_item(piece):
    return (None, piece)


@mark.actor.cfg_value_creg
def resolve_untyped_command_cfg_value(piece, key, system, service_name):
    command_creg = system.resolve_service('command_creg')
    return command_creg.animate(piece)
