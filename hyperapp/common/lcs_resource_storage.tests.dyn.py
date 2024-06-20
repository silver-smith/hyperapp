from pathlib import Path

from . import htypes
from .services import (
    builtin_types_as_dict,
    legacy_type_resource_loader,
    local_types,
    mosaic,
    pyobj_creg,
    resource_registry,
    )
from .tested.code import lcs_resource_storage


def test_set():
    # Subprocess does not add local types to resource registry.
    resource_registry.update_modules(legacy_type_resource_loader({
        **builtin_types_as_dict(), **local_types}))
    # Test driver does not load types from resources.
    # Manually add used type to cache.
    _ = resource_registry['legacy_type.lcs_resource_storage_tests', 'sample_1_d']

    path = Path('/tmp/lcs-storage-test.yaml')
    try:
        path.unlink()
    except FileNotFoundError:
        pass

    d_1_t = htypes.lcs_resource_storage_tests.sample_1_d
    d_1 = pyobj_creg.actor_to_piece(d_1_t)
    d_2 = htypes.lcs_resource_storage_tests.sample_2_d('some-path')
    inner = htypes.lcs_resource_storage_tests.inner_piece(
        value=(11, 22, 33),
        )
    piece = htypes.lcs_resource_storage_tests.sample_piece(
        direction='sample-direction',
        stretch=12345,
        inner=mosaic.put(inner),
        )

    storage_1 = lcs_resource_storage.LcsResourceStorage('test.lcs_storage', path)
    storage_1.set({d_1, d_2}, piece)

    storage_2 = lcs_resource_storage.LcsResourceStorage('test.lcs_storage', path)
    assert storage_2.get({d_1, d_2}) == piece
