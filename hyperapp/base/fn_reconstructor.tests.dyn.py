from . import htypes
from .tested.code.fn_reconstructor import fn_to_piece



def _test_fn():
    pass


def test_fn_to_ref():
    piece = fn_to_piece(_test_fn)
    assert isinstance(piece, htypes.builtin.attribute)
