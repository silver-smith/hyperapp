import logging
from types import SimpleNamespace

import pytest

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
def module_dir_list():
    return [HYPERAPP_DIR]


@pytest.fixture
def services(module_dir_list, code_module_list, post_stop_checks):
    services = Services(module_dir_list)
    services.init_services()
    services.init_modules(code_module_list)
    yield services
    services.unregister_import_meta_hook() # Call before stopping, as stopping may raise an exception.
    log.info("Stopping services")
    services.stop()
    post_stop_checks(services)


@pytest.fixture
def htypes(services):
    return HyperTypesNamespace(services.types, services.type_module_loader.registry)


@pytest.fixture
def code(services):
    return SimpleNamespace(**{
        rec.name.split('.')[-1]: rec.python_module  # sync.rpc.rpc_endpoint -> rpc_endpoint
        for rec in services.module_registry.elements()
        })
