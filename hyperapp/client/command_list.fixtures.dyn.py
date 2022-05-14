from .htypes import command_list
from .services import sample_global_command_command


def global_command_list_piece():
    return command_list.global_command_list()


def global_command_list_global_command_list():
    return [sample_global_command_command]
