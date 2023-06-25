from .services import (
    local_server_ref,
    mark,
    )


@mark.global_command
def open_local_server():
    return local_server_ref.load_piece()
