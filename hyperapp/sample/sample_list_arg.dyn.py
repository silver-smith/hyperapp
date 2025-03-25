from . import htypes
from .code.mark import mark


@mark.editor.default
def sample_list_default():
    return htypes.sample_list_selector.item(id=0)


# TODO: If we need global commands with args, add global command enumerator
# and refactor so that all model commands with enums can be picked with single service.
# @mark.global_command(args=['item'])
# def show_sample_list_item(item):
#     assert isinstance(item, htypes.sample_list_selector.item)
#     return f"Selected sample list item: {item}"
