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
def additional_code_module_dirs():
    return []


@pytest.fixture
def services(additional_code_module_dirs, code_module_list, post_stop_checks):
    services = Services()
    services.init_services()
    services.code_module_dir_list += additional_code_module_dirs
    services.init_modules(code_module_list)
    services.start()
    yield services
    log.info("Stopping services")
    services.stop()
    post_stop_checks(services)


@pytest.fixture
def htypes(services):
    return HyperTypesNamespace(services.types, services.type_module_loader.registry)


@pytest.fixture
def code(services):
    return SimpleNamespace(**{
        name.split('.')[-1]: rec.module  # sync.rpc.rpc_endpoint -> rpc_endpoint
        for name, rec in services.imported_code_modules.items()
        })
