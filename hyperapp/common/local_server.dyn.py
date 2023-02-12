from pathlib import Path

from .services import (
    mark,
    file_bundle,
    )


@mark.service
def local_server_ref():
    return file_bundle(Path.home() / '.local/share/hyperapp/server-ref.json')
