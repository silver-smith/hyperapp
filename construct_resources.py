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
    HYPERAPP_DIR / 'sync',
    HYPERAPP_DIR / 'async',
    HYPERAPP_DIR / 'ui',
    HYPERAPP_DIR / 'sample',
    HYPERAPP_DIR / 'guesser',
    HYPERAPP_DIR / 'command_line',
    ]

code_module_list = [
    'common.lcs',
    'common.lcs_service',
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
    'resource.value',
    'resource.piece_ref',
    'resource.typed_piece',
    'resource.selector',
    'resource.rpc_command',
    'resource.rpc_callback',
    'resource.map_service',
    'resource.python_module',
    'resource.raw',
    'ui.impl_registry',
    'ui.global_command_list',
    ]


def main():
    init_logging('server')

    parser = argparse.ArgumentParser(description='Construct resources')
    parser.add_argument('--root-dir', type=Path, help="Resource root dir")
    parser.add_argument('--resource-dir', type=Path, nargs='*', help="Additional resource dir")
    parser.add_argument('source_path', type=Path, nargs='+', help="Path to source file")
    args = parser.parse_args()

    config = {
        'command_line.construct_resources': {'args': args},
    }

    services = Services(module_dir_list)
    services.init_services()
    services.init_modules(code_module_list, config)
    services.start_modules()
    log.info("Initialized.")

    try:
        module = services.resource_module_registry['command_line.construct_resources']
        resource = module['construct_resources']
        fn = services.python_object_creg.animate(resource)
        log.info("Construct resources function: %r", fn)
        resource_dir_list = [
            dir.absolute() for dir in args.resource_dir or []
            ]
        fn(args.root_dir or services.hyperapp_dir, resource_dir_list, args.source_path)
    finally:
        log.info("Stopping.")
        services.stop()


if __name__ == '__main__':
    main()
