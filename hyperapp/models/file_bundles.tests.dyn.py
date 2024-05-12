from . import htypes
from .tested.code import file_bundles


def test_open():
    piece = file_bundles.open_file_bundle_list()
    assert isinstance(piece, htypes.file_bundles.bundle_list)


def test_bundle_list():
    piece = htypes.file_bundles.bundle_list()
    result = file_bundles.file_bundle_list(piece)
    assert type(result) is list
    assert isinstance(result[0], htypes.file_bundles.bundle)
