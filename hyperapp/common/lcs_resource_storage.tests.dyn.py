from pathlib import Path

from . import htypes
from .tested.code import lcs_resource_storage


def test_set():
    path = Path('/tmp/lcs-storage-test.yaml')
    storage = lcs_resource_storage.LcsResourceStorage('test.lcs_storage', path)
    d_1 = htypes.lcs_resource_storage_tests.sample_1_d()
    d_2 = htypes.lcs_resource_storage_tests.sample_2_d('some-path')
    piece = htypes.lcs_resource_storage_tests.sample_piece(
        direction='sample-direction',
        stretch=12345,
        )
    storage.set({d_1, d_2}, piece)
