from functools import partial

import pytest

from hyperapp.boot.resource.resource_registry import ResourceRegistry
from hyperapp.boot.resource.builtin_service import make_builtin_service_resource_module
from hyperapp.boot.resource.legacy_type import add_legacy_types_to_cache, load_legacy_type_resources


@pytest.fixture
def builtin_services(
        mosaic,
        web,
        ):
    return {
        'mosaic': mosaic,
        'web': web,
    }


@pytest.fixture
def builtin_service_resource_loader(mosaic, builtin_services):
    return partial(make_builtin_service_resource_module, mosaic, builtin_services.keys())


@pytest.fixture
def resource_registry(
        resource_list_loader,
        builtin_types_as_dict,
        local_types,
        builtin_service_resource_loader,
        resource_dir_list,
        ):
    registry = ResourceRegistry()
    resource_list_loader(resource_dir_list, registry)
    legacy_type_modules = load_legacy_type_resources({**builtin_types_as_dict(), **local_types})
    registry.update_modules(legacy_type_modules)
    add_legacy_types_to_cache(registry, legacy_type_modules)  # Also adds builtin types, again.
    registry.set_module('builtins', builtin_service_resource_loader(registry))
    return registry
