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
        htypes.sample_list.item(1, "First"),
        htypes.sample_list.item(2, "Second"),
        htypes.sample_list.item(3, "Third"),
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
