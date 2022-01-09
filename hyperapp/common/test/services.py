import logging
from types import SimpleNamespace

import pytest

from hyperapp.common.services import Services
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
def additional_module_dirs():
    return []


@pytest.fixture
def services(additional_module_dirs, code_module_list, post_stop_checks):
    services = Services()
    services.init_services()
    services.module_dir_list += additional_module_dirs
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
