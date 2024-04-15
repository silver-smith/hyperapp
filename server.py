#!/usr/bin/env python3

import argparse
import logging
import sys
from functools import partial

from hyperapp.common.init_logging import init_logging
from hyperapp.common import cdr_coders  # register codec
from hyperapp.common.services import HYPERAPP_DIR, Services

log = logging.getLogger(__name__)


module_dir_list = [
    HYPERAPP_DIR / 'common',
    HYPERAPP_DIR / 'resource',
    HYPERAPP_DIR / 'transport',
    HYPERAPP_DIR / 'rpc',
    HYPERAPP_DIR / 'subprocess',
    HYPERAPP_DIR / 'sample',
    HYPERAPP_DIR / 'ui',
    HYPERAPP_DIR / 'server',
    ]

BIND_ADDRESS = ('localhost', 8080)


def load_module(resource_registry, pyobj_creg, module_name):
    var_name = module_name.split('.')[-1] + '.module'
    module_res = resource_registry[module_name, var_name]
    return pyobj_creg.animate(module_res)


def main():
    init_logging('server')

    parser = argparse.ArgumentParser(description='Hyperapp server')
    args = parser.parse_args()

    services = Services(module_dir_list)
    services.init_services()
    services.load_type_modules()
    log.info("Initialized.")

    try:
        mosaic = services.mosaic
        resource_dir_list = services.resource_dir_list
        resource_registry = services.resource_registry
        resource_list_loader = services.resource_list_loader
        legacy_type_resource_loader = services.legacy_type_resource_loader
        builtin_types_as_dict = services.builtin_types_as_dict
        local_types = services.local_types
        association_reg = services.association_reg
        pyobj_creg = services.pyobj_creg

        resource_list_loader(resource_dir_list, resource_registry)
        resource_registry.update_modules(legacy_type_resource_loader({**builtin_types_as_dict(), **local_types}))

        association_reg.register_association_list(resource_registry.associations)
        server_module_res = resource_registry['server.server', 'server.module']
        server_module = pyobj_creg.animate(server_module_res)
        exit_code = server_module._main()
    finally:
        log.info("Stopping.")
        services.stop_signal.set()
        services.stop()
    if exit_code != 0:
        log.error("Application returned non-zero exit code: %d", exit_code)
        sys.exit(exit_code)


if __name__ == '__main__':
    main()
