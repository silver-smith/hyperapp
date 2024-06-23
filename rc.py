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
    HYPERAPP_DIR / 'rc',
    HYPERAPP_DIR / 'command_line',
    HYPERAPP_DIR / 'sample',
    HYPERAPP_DIR / 'ui',
    HYPERAPP_DIR / 'views',
    HYPERAPP_DIR / 'models',
    ]


def main():
    init_logging('rc')

    parser = argparse.ArgumentParser(description='Compile resources')
    parser.add_argument('--root-dir', type=Path, nargs='*', help="Additional resource root dirs")
    parser.add_argument('--module', type=str, nargs='*', help="Select (narrow) modules to compile")
    parser.add_argument('--workers', type=int, default=1, help="Worker process count to start and use")
    parser.add_argument('--timeout', type=int, help="Base timeout for RPC calls and everything (seconds). Default is none")
    parser.add_argument('--show-traces', action='store_true', help="Show traces for cancelled and waiting construction units")
    parser.add_argument('source_subdir', type=str, nargs='*', help="Subdirs with source files")
    args = parser.parse_args()

    config = {
        'command_line.rc': {'args': args},
    }

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
        fn_res = resource_registry['rc.rc', 'compile_resources']
        fn_ref = mosaic.put(fn_res)
        fn = pyobj_creg.animate(fn_res)
        fn(fn_ref, args.source_subdir, args.root_dir or [], args.module, args.workers, args.show_traces, args.timeout)
    finally:
        log.info("Stopping.")
        services.stop_signal.set()
        services.stop()


if __name__ == '__main__':
    main()
