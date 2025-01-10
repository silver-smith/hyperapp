#!/usr/bin/env python3

import logging
import sys

from hyperapp.boot.init_logging import init_logging
from hyperapp.boot import cdr_coders  # register codec
from hyperapp.boot.services import HYPERAPP_DIR, Services

log = logging.getLogger('rc.main')


module_dir_list = [
    HYPERAPP_DIR,
    HYPERAPP_DIR / 'common',
    HYPERAPP_DIR / 'resource',
    HYPERAPP_DIR / 'system',
    HYPERAPP_DIR / 'transport',
    HYPERAPP_DIR / 'rpc',
    HYPERAPP_DIR / 'subprocess',
    HYPERAPP_DIR / 'rc',
    HYPERAPP_DIR / 'command_line',
    HYPERAPP_DIR / 'sample',
    HYPERAPP_DIR / 'ui',
    HYPERAPP_DIR / 'views',
    HYPERAPP_DIR / 'models',
    ]


def main():
    init_logging('hyperapp')

    services = Services(module_dir_list)
    services.init_services()
    services.load_type_modules()
    log.debug("Initialized.")

    try:
        resource_dir_list = services.resource_dir_list
        resource_registry = services.resource_registry
        resource_list_loader = services.resource_list_loader
        legacy_type_resource_loader = services.legacy_type_resource_loader
        local_types = services.local_types
        pyobj_creg = services.pyobj_creg

        config_file = sys.argv[1]
        root_service = sys.argv[2]

        resource_list_loader(resource_dir_list, resource_registry)
        resource_registry.update_modules(legacy_type_resource_loader(local_types))
        config = resource_registry[config_file, 'config']
        module_res = resource_registry['system.system', 'system.module']
        module = pyobj_creg.animate(module_res)

        module.run_system(config, root_service, sys.argv[3:])

    finally:
        log.info("Stopping.")
        services.stop()


if __name__ == '__main__':
    main()
