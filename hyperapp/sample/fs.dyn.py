import os
import os.path

from . import htypes
from .code.mark import mark


@mark.model(key='name')
def fs_model(piece, current_path):
    fs_path = '/' + '/'.join(current_path)
    if not os.path.isdir(fs_path):
        return []
    try:
        name_list = os.listdir(fs_path)
    except PermissionError:
        return []
    return [
        htypes.fs.item(
            name=name,
            size=None,
            )
        for name in name_list
        if not name.startswith('.')
        ]


@mark.global_command
def open_fs():
    return htypes.fs.model()
