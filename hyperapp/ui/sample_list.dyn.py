from . import htypes


def sample_list(piece):
    return [
        htypes.sample_list.item(1, "First sample"),
        htypes.sample_list.item(2, "Second sample"),
        htypes.sample_list.item(3, "Third sample"),
        ]


async def open_sample_fn_list():
    return htypes.sample_list.sample_list()
