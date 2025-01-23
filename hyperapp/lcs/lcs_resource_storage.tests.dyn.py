import os
from pathlib import Path

from hyperapp.boot.resource.legacy_type import add_legacy_types_to_cache

from . import htypes
from .services import (
    legacy_type_resource_loader,
    local_types,
    mosaic,
    pyobj_creg,
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


@mark.fixture.obj
def storage_factory(lcs_resource_storage_factory, path):
    def factory():
        return lcs_resource_storage_factory('test.lcs_storage', path, project_imports={})
    return factory


@mark.fixture
def storage(storage_factory):
    return storage_factory()


def test_persistence(storage_factory, path, key, piece):
    storage_1 = storage_factory()
    storage_1.set(key, piece)
    assert storage_1.get(key) == piece
    storage_2 = storage_factory()
    assert storage_2.get(key) == piece


def test_primitive(storage, path, key):
    storage.set(key, "Sample string")
    assert storage.get(key) == "Sample string"


def test_replace(storage, path, key, piece):
    storage.set(key, piece)
    storage.set(key, "Sample string")
    assert storage.get(key) == "Sample string"


def test_remove(storage, path, key, piece):
    storage.set(key, piece)
    storage.remove(key)
    assert storage.get(key) is None
