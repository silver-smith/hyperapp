import logging

import pytest

from hyperapp.common.services import Services

log = logging.getLogger(__name__)


@pytest.fixture
def type_module_list():
    return []


@pytest.fixture
def code_module_list():
    return []


@pytest.fixture
def services(type_module_list, code_module_list):
    services = Services()
    services.init_services()
    services.init_modules(type_module_list, code_module_list)
    services.start()
    yield services
    services.stop()
    for reason in services.get_failure_reason_list():
        log.error("Services failure reason: %s", reason)
    assert not services.is_failed()
