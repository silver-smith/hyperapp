import os
from pathlib import Path

from hyperapp.resource.legacy_type import add_legacy_types_to_cache

from . import htypes
from .services import (
    builtin_types_as_dict,
    legacy_type_resource_loader,
    local_types,
    mosaic,
    pyobj_creg,
    resource_registry,
    )
from .code.mark import mark
from .tested.code import lcs_resource_storage


@mark.fixture
def path():
    pid = os.getpid()
    path = Path(f'/tmp/lcs-storage-test-{pid}.yaml')
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    return path


@mark.fixture
def key():
    d_1_t = htypes.lcs_resource_storage_tests.sample_1_d
    d_1 = pyobj_creg.actor_to_piece(d_1_t)
    d_2 = htypes.lcs_resource_storage_tests.sample_2_d('some-path')
    return {d_1, d_2}


@mark.fixture
def piece():
    inner = htypes.lcs_resource_storage_tests.inner_piece(
        value=(11, 22, 33),
        )
    return htypes.lcs_resource_storage_tests.sample_piece(
        direction='sample-direction',
        stretch=12345,
        inner=mosaic.put(inner),
        )


# Subprocess job runner does not have builtin types in resource registry cache by default.
@mark.fixture
def prereq():
    add_legacy_types_to_cache(resource_registry, legacy_type_resource_loader(builtin_types_as_dict()))


def test_persistence(lcs_resource_storage_factory, prereq, path, key, piece):
    storage_1 = lcs_resource_storage_factory('test.lcs_storage', path)
    storage_1.set(key, piece)
    assert storage_1.get(key) == piece
    storage_2 = lcs_resource_storage_factory('test.lcs_storage', path)
    assert storage_2.get(key) == piece


def test_primitive(lcs_resource_storage_factory, prereq, path, key):
    storage = lcs_resource_storage_factory('test.lcs_storage', path)
    storage.set(key, "Sample string")
    assert storage.get(key) == "Sample string"


def test_replace(lcs_resource_storage_factory, prereq, path, key, piece):
    storage = lcs_resource_storage_factory('test.lcs_storage', path)
    storage.set(key, piece)
    storage.set(key, "Sample string")
    assert storage.get(key) == "Sample string"


def test_remove(lcs_resource_storage_factory, prereq, path, key, piece):
    storage = lcs_resource_storage_factory('test.lcs_storage', path)
    storage.set(key, piece)
    storage.remove(key)
    assert storage.get(key) is None
