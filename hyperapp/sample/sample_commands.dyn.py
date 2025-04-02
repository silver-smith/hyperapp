import os

from . import htypes
from .code.mark import mark


@mark.global_command
async def open_sample_static_text_1():
    return "Sample text 1"


@mark.global_command
async def open_sample_static_text_2():
    return "Sample text 2"


@mark.global_command
async def open_sample_static_list():
    items = [
        htypes.sample_list.item(1, "First", "First item"),
        htypes.sample_list.item(2, "Second", "Second item"),
        htypes.sample_list.item(3, "Third", "Third item"),
        ]
    return items


@mark.global_command
async def show_state(model_state):
    return str(model_state)


@mark.command
async def details(piece, current_idx):
    return f"{piece} current idx: {current_idx}"


@mark.command
async def sample_tree_info(piece):
    return f"Sample tree piece: {piece}"


@mark.global_command
def system_info():
    uname = os.uname()
    info = {
        'user': os.getlogin(),
        'nodename': uname.nodename,
        'version': uname.version,
        'cpu_count': str(os.cpu_count()),
        }
    return [
        htypes.sample_commands.system_info_item(idx, key, value)
        for idx, (key, value) in enumerate(info.items())
        ]
