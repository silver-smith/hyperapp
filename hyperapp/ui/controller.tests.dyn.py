from . import htypes
from .tested.code import controller


def test_layout_tree():
    piece = htypes.layout.view()
    value = controller.layout_tree(piece, None)
    assert value
    parent = htypes.layout.item("Some item")
    controller.layout_tree(piece, parent)
