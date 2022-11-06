from .services import (
    local_server_ref,
    )
from .global_command_ctr import global_command


@global_command
def open_local_server():
    return local_server_ref.load_piece()
