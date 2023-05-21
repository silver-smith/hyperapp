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

code_module_list = [
    'resource.resource_type',
    'resource.registry',
    'resource.resource_module',
    'resource.legacy_module',
    'resource.legacy_service',
    'resource.legacy_type',
    'resource.attribute',
    'resource.partial',
    'resource.call',
    'resource.list_service',
    'resource.live_list_service',
    'resource.tree_service',
    'resource.piece_ref',
    'resource.typed_piece',
    'resource.selector',
    'resource.rpc_command',
    'resource.rpc_callback',
    'resource.map_service',
    'resource.python_module',
    'resource.raw',
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
    services.init_modules(code_module_list, config)
    services.start_modules()
    log.info("Initialized.")

    try:
        fn_res = services.resource_registry['command_line.update_resources', 'update_resources']
        fn = services.python_object_creg.animate(fn_res)
        log.info("Update resources function: %r", fn)
        fn(fn_res, args.source_subdir, args.root_dir or [], args.module, args.rpc_timeout)
    finally:
        log.info("Stopping.")
        services.stop_signal.set()
        services.stop()


if __name__ == '__main__':
    main()
