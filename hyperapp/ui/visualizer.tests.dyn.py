from .tested.code import visualizer
from .tested.services import visualizer


def test_visualizer():
    layout = visualizer("Sample text")
    assert layout
