import logging
from types import SimpleNamespace

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


class HyperTypesNamespace:

    def __init__(self, types, local_type_module_registry):
        self._types = types
        self._local_type_module_registry = local_type_module_registry

    def __getattr__(self, name):
        if not name.startswith('_'):
            try:
                type_module = self._local_type_module_registry[name]
            except KeyError:
                pass
            else:
                return self._type_module_namespace(type_module)
        raise AttributeError(name)

    def _type_module_namespace(self, type_module):
        name_to_type = {}
        for name, type_ref in type_module.items():
            name_to_type[name] = self._types.resolve(type_ref)
        return SimpleNamespace(**name_to_type)


@pytest.fixture
def htypes(services):
    return HyperTypesNamespace(services.types, services.local_type_module_registry)
