from . import htypes
from .services import local_server_ref


def init_local_server_ref():
    local_server_ref.save_piece(htypes.server_global_commands.server_global_commands())
