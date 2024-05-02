from unittest.mock import Mock

from .tested.code import client


def test_make_default_layout():
    lcs = Mock()
    layout = client.make_default_layout(lcs)
    assert layout
