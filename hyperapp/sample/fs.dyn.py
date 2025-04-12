import logging
from pathlib import Path

from . import htypes
from .code.mark import mark

log = logging.getLogger(__name__)


@mark.model(key='name')
def fs_model(piece, current_path):
    fs_dir = Path('/').joinpath(*current_path)
    log.info("FS: loading dir: %s", fs_dir)
    if not fs_dir.is_dir():
        return []
    try:
        kid_list = list(fs_dir.iterdir())
    except PermissionError:
        return []
    item_list = []
    for item_path in kid_list:
        if item_path.name.startswith('.'):
            continue
        if item_path.is_file():
            size = item_path.stat().st_size
        else:
            size = None
        item = htypes.fs.item(
            name=item_path.name,
            size=size,
            )
        item_list.append(item)
    return item_list


@mark.global_command
def open_fs():
    return htypes.fs.model()


@mark.actor.formatter_creg
def format_model(piece):
    return "FS"
