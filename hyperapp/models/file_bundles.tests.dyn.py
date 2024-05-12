from pathlib import Path

from . import htypes
from .services import (
    file_bundle,
    )
from .tested.code import file_bundles


def test_open_list():
    piece = file_bundles.open_file_bundle_list()
    assert isinstance(piece, htypes.file_bundles.bundle_list)


def test_bundle_list():
    piece = htypes.file_bundles.bundle_list()
    result = file_bundles.file_bundle_list(piece)
    assert type(result) is list
    assert isinstance(result[0], htypes.file_bundles.bundle_item)


def test_open_bundle():
    path = "~/.cache/hyperapp/test/file_bundles.cdr"
    root = htypes.file_bundles_tests.sample_root()
    bundle = file_bundle(Path(path).expanduser(), 'cdr')
    bundle.save_piece(root)

    piece = htypes.file_bundles.bundle_list()
    current_item = htypes.file_bundles.bundle_item(
        name="sample test bundle",
        path=path,
        )
    result = file_bundles.open(piece, current_item)
    assert result
