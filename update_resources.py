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

    parser = argparse.ArgumentParser(description='Update resources')
    parser.add_argument('--root-dir', type=Path, help="Resource root dir")
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
        resource = services.resource_registry['command_line.update_resources', 'update_resources']
        fn = services.python_object_creg.animate(resource)
        log.info("Update resources function: %r", fn)
        fn(args.root_dir or services.hyperapp_dir, args.source_subdir)
    finally:
        log.info("Stopping.")
        services.stop()


if __name__ == '__main__':
    main()
