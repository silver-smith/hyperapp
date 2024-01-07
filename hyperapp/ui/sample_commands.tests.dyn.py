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
