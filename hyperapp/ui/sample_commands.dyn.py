from . import htypes


async def open_sample_static_text_1():
    return "Sample text 1"


async def open_sample_static_text_2():
    return "Sample text 2"


async def open_sample_static_list():
    items = [
        htypes.sample_list.item(1, "First"),
        htypes.sample_list.item(2, "Second"),
        htypes.sample_list.item(3, "Third"),
        ]
    return items


async def show_state(state):
    return str(state)


async def sample_list_state(piece, current_idx):
    return f"{piece} current idx: {current_idx}"


async def sample_tree_info(piece):
    return f"Sample tree piece: {piece}"
