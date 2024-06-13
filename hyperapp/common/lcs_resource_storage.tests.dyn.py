from pathlib import Path

from . import htypes
from .services import (
    legacy_type_resource_loader,
    local_types,
    resource_registry,
    )
from .tested.code import lcs_resource_storage


def test_set():
    # Subprocess does not add local types to resource registry.
    resource_registry.update_modules(legacy_type_resource_loader(local_types))

    path = Path('/tmp/lcs-storage-test.yaml')
    try:
        path.unlink()
    except FileNotFoundError:
        pass

    d_1 = htypes.lcs_resource_storage_tests.sample_1_d()
    d_2 = htypes.lcs_resource_storage_tests.sample_2_d('some-path')
    piece = htypes.lcs_resource_storage_tests.sample_piece(
        direction='sample-direction',
        stretch=12345,
        )

    storage_1 = lcs_resource_storage.LcsResourceStorage('test.lcs_storage', path)
    storage_1.set({d_1, d_2}, piece)

    storage_2 = lcs_resource_storage.LcsResourceStorage('test.lcs_storage', path)
    assert storage_2.get({d_1, d_2}) == piece
