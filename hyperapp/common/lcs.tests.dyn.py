from unittest.mock import Mock

from . import htypes
from .services import (
    mosaic,
    )
from .tested.code import lcs


def _test_load_add_iter_save():
    association = htypes.lcs.lcs_set_association(
        dir=(mosaic.put(htypes.lcs_tests.sample_d()),),
        value=mosaic.put("Sample value"),
        )
    storage = Mock()
    storage.association_list = [mosaic.put(association)]
    bundle = Mock()
    bundle.load_piece.return_value = storage

    sheet = lcs.LCSheet(bundle)
    d = {htypes.lcs_tests.sample_d()}
    sheet.add(d, "Another value", persist=True)
    assert set(sheet.iter_dir_list_values([d])) == {"Sample value", "Another value"}

    bundle.save_piece.assert_called()
