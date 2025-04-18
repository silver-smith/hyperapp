from .services import (
    mosaic,
    )
from .tested.code import ref_formatter


def test_format():
    piece = "Sample piece"
    ref = mosaic.put(piece)
    title = ref_formatter.format_ref(ref)
    assert type(title) is str
