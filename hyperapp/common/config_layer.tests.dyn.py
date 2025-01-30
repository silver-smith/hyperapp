import os
import shutil
from pathlib import Path

from . import htypes
from .services import (
    mosaic,
    project_factory,
    )
from .code.mark import mark
from .code.data_service import DataServiceConfigCtl
from .tested.code import config_layer


@mark.fixture
def project_dir():
    pid = os.getpid()
    dir = Path(f'/tmp/config-layer-test-{pid}')
    try:
        shutil.rmtree(dir)
    except FileNotFoundError:
        pass
    dir.mkdir()
    return dir


@mark.fixture
def project(project_dir):
    return project_factory(project_dir, 'layer-test')


@mark.fixture
def layer_factory(system, config_ctl, project):
    return config_layer.ProjectConfigLayer(system, config_ctl, project)


@mark.fixture.obj
def layer(layer_factory):
    return layer_factory()


@mark.fixture(ctl=DataServiceConfigCtl())
def sample_service(config):
    return config


@mark.fixture
def key():
    return htypes.config_layer_tests.sample_key(134)


@mark.fixture
def value():
    inner = htypes.config_layer_tests.inner(
        value=(11, 22, 33),
        )
    return htypes.config_layer_tests.sample_value(
        direction='sample-direction',
        stretch=12345,
        inner=mosaic.put(inner),
        )


def test_primitive(layer, key):
    layer.set('sample_service', key, "Sample string")
    assert layer.config['sample_service'][key] == "Sample string"


def test_record(layer, key, value):
    layer.set('sample_service', key, value)
    assert layer.config['sample_service'][key] == value


def test_persistence(layer_factory, key, value):
    layer_1 = layer_factory()
    layer_1.set('sample_service', key, value)
    assert layer_1.config['sample_service'][key] == value

    layer_2 = layer_factory()
    assert layer_2.config['sample_service'][key] == value


def test_invalidation(system, layer, sample_service, key, value):
    system.load_config_layer('config-layer-test', layer)
    assert sample_service.get(key) is None
    sample_service[key] = value
    assert sample_service[key] == value
