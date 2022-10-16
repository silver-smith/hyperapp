import logging
from types import SimpleNamespace

import pytest

from hyperapp.common.resource_dir import ResourceDir
from hyperapp.common.services import HYPERAPP_DIR, Services
from hyperapp.common.test.hyper_types_namespace import HyperTypesNamespace

log = logging.getLogger(__name__)


@pytest.fixture
def code_module_list():
    return []


@pytest.fixture
def post_stop_checks():
    def do_nothing(services):
        pass
    return do_nothing


@pytest.fixture
def hyperapp_dir():
    return HYPERAPP_DIR


@pytest.fixture
def default_module_dir_list(hyperapp_dir):
    return [
        hyperapp_dir / 'common',
        hyperapp_dir / 'resource',
        hyperapp_dir / 'transport',
        hyperapp_dir / 'sync',
        hyperapp_dir / 'async',
        hyperapp_dir / 'ui',
        hyperapp_dir / 'sample',
        ]


@pytest.fixture
def additional_root_dirs():
    return []


@pytest.fixture
def module_dir_list(default_module_dir_list):
    return default_module_dir_list


@pytest.fixture
def services(additional_root_dirs, module_dir_list, code_module_list, post_stop_checks):
    additional_resource_dirs = [
        ResourceDir(d) for d in additional_root_dirs
        ]
    services = Services(module_dir_list, additional_resource_dirs)
    services.init_services()
    services.init_modules(code_module_list)
    services.start_modules()
    yield services
    services.unregister_import_meta_hook() # Call before stopping, as stopping may raise an exception.
    log.info("Stopping services")
    services.stop()
    post_stop_checks(services)


@pytest.fixture
def htypes(services):
    return HyperTypesNamespace(services.types, services.local_types)


@pytest.fixture
def code(services):
    return SimpleNamespace(**{
        rec.name.split('.')[-1]: rec.python_module  # sync.rpc.rpc_endpoint -> rpc_endpoint
        for rec in services.module_registry.elements()
        })
