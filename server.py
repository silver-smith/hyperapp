#!/usr/bin/env python3

import argparse
import logging
import sys

from hyperapp.common.init_logging import init_logging
from hyperapp.common import cdr_coders  # register codec
from hyperapp.common.services import Services

log = logging.getLogger(__name__)


code_module_list = [
    'common.dict_coders',  # Load json coders.
    'resource.legacy_module',
    'resource.legacy_service',
    'resource.legacy_type',
    'resource.attribute',
    'resource.partial',
    'resource.call',
    'resource.value',
    'resource.piece_ref',
    'resource.rpc_command',
    'resource.rpc_callback',
    'resource.list_service',
    'resource.live_list_service',
    'resource.tree_service',
    'resource.selector',
    'transport.rsa_identity',
    'async.ui.rpc_callback',
    'server.tcp_server',
    'server.server_ref_list',
    'server.sample_list',
    'server.sample_live_list',
    'server.sample_tree',
    'server.module_list',
    'server.htest_module_list',
    # 'server.htest_list',
    ]

config = {
    'server.tcp_server': {'bind_address': ('localhost', 8080)},
    }


def main():
    init_logging('server')

    parser = argparse.ArgumentParser(description='Hyperapp server')
    args = parser.parse_args()

    services = Services()
    services.init_services()
    services.init_modules(code_module_list, config)
    log.info("Server is started.")
    try:
        services.stop_signal.wait()
    except KeyboardInterrupt:
        pass
    log.info("Server is stopping.")
    services.stop()


if __name__ == '__main__':
    main()
