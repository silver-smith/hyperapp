from . import htypes
from .tested.code import sample_commands


async def test_open_sample_static_text_1():
    text = await sample_commands.open_sample_static_text_1()
    assert text


async def test_open_sample_static_text_2():
    text = await sample_commands.open_sample_static_text_2()
    assert text


async def test_open_sample_static_list():
    list = await sample_commands.open_sample_static_list()
    assert list


async def test_show_state():
    value = await sample_commands.show_state(state="sample state")
    assert value


async def test_sample_list_state():
    value = await sample_commands.sample_list_state(
        htypes.sample_list.sample_list(), current_idx=11)


async def test_sample_tree_info():
    value = await sample_commands.sample_tree_info(
        htypes.sample_tree.sample_tree())
