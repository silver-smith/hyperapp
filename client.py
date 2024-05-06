#!/usr/bin/env python3

import argparse
import logging
import sys

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
    HYPERAPP_DIR / 'models',
    HYPERAPP_DIR / 'sample',
    HYPERAPP_DIR / 'ui',
    HYPERAPP_DIR / 'client',
    ]


def main():
    init_logging('client')

    parser = argparse.ArgumentParser(description='Hyperapp client')
    parser.add_argument('--clean', '-c', action='store_true', help="Do not load stored layout state")
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
        client_module_res = resource_registry['client.client', 'client.module']
        client_module = pyobj_creg.animate(client_module_res)
        exit_code = client_module._main(load_state=not args.clean)
    finally:
        log.info("Stopping.")
        services.stop_signal.set()
        services.stop()
    if exit_code != 0:
        log.error("Application returned non-zero exit code: %d", exit_code)
        sys.exit(exit_code)


main()
