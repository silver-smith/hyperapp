from .import htypes
from .services import sample_global_command_command
from .view_command import ViewCommand


def global_command_list_piece():
    return htypes.command_list.global_command_list()


def view_command_list_piece():
    return htypes.command_list.view_command_list()


def global_command_list_global_command_list():
    return [sample_global_command_command]


class _PhonyRootView:

    def iter_view_commands(self):
        command = ViewCommand(
            module_name='command_list.fixture',
            qual_name='phony.view.command',
            name='phony',
            method=None,
            )
        return [([], command)]


def view_command_list_root_view():
    return _PhonyRootView()
