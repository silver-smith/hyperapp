import logging
from pathlib import Path

from . import htypes
from .code.mark import mark

log = logging.getLogger(__name__)


def _enum_dir(fs_dir):
    if not fs_dir.is_dir():
        return
    for item_path in fs_dir.iterdir():
        if item_path.name.startswith('.'):
            continue
        if item_path.is_file():
            size = item_path.stat().st_size
        else:
            size = None
        yield htypes.fs.item(
            name=item_path.name,
            size=size,
            )


@mark.model(key='name')
def fs_model(piece, current_path):
    fs_dir = Path('/').joinpath(*current_path)
    log.info("FS: loading dir: %s", fs_dir)
    try:
        return list(_enum_dir(fs_dir))
    except PermissionError:
        return []


@mark.global_command
def open_fs():
    return htypes.fs.model()
