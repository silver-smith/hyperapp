#!/usr/bin/env python3

import argparse
import logging
from pathlib import Path

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
    HYPERAPP_DIR / 'guesser',
    HYPERAPP_DIR / 'command_line',
    HYPERAPP_DIR / 'ui_types',
    ]

def main():
    init_logging('update_resources')

    parser = argparse.ArgumentParser(description='Update resources')
    parser.add_argument('--root-dir', type=Path, nargs='*', help="Additional resource root dirs")
    parser.add_argument('--module', type=str, nargs='*', help="Select (narrow) modules to update")
    parser.add_argument('--rpc-timeout', type=int, help="Timeout for RPC calls (seconds). Default is none")
    parser.add_argument('source_subdir', type=str, nargs='+', help="Subdirs with source files")
    args = parser.parse_args()

    config = {
        'command_line.update_resources': {'args': args},
    }

    services = Services(module_dir_list)
    services.init_services()
    services.load_type_modules()
    log.info("Initialized.")

    try:
        resource_dir_list = services.resource_dir_list
        resource_registry = services.resource_registry
        resource_list_loader = services.resource_list_loader
        legacy_type_resource_loader = services.legacy_type_resource_loader
        builtin_types_as_dict = services.builtin_types_as_dict
        local_types = services.local_types
        association_reg = services.association_reg
        python_object_creg = services.python_object_creg

        resource_list_loader(resource_dir_list, resource_registry)
        resource_registry.update_modules(legacy_type_resource_loader({**builtin_types_as_dict(), **local_types}))

        attribute_t = python_object_creg.animate(resource_registry['legacy_type.attribute', 'attribute'])
        attribute_module = python_object_creg.animate(resource_registry['resource.attribute', 'attribute.module'])
        python_object_creg.register_actor(attribute_t, attribute_module.python_object)

        association_reg.register_association_list(resource_registry.associations)
        fn_res = resource_registry['command_line.update_resources', 'update_resources']
        fn = python_object_creg.animate(fn_res)
        log.info("Update resources function: %r", fn)
        fn(fn_res, args.source_subdir, args.root_dir or [], args.module, args.rpc_timeout)
    finally:
        log.info("Stopping.")
        services.stop_signal.set()
        services.stop()


if __name__ == '__main__':
    main()
