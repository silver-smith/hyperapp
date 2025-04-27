import logging
import magic
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


@mark.command
def open(piece, current_path):
    file_path = Path('/').joinpath(*current_path)
    if not file_path.is_file():
        return
    file_type = magic.from_file(file_path)
    log.info("FS: opening file typed %r: %s", file_type, file_path)
    if 'text' not in file_type:
        return
    return file_path.read_text()


@mark.global_command
def open_fs():
    return htypes.fs.model()


@mark.actor.formatter_creg
def format_model(piece):
    return "FS"
