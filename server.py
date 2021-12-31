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
    'common.resource.legacy_module',
    'common.resource.legacy_service',
    'common.resource.factory',
    'common.resource.call',
    'common.resource.rpc_command',
    'common.resource.list_service',
    'transport.rsa_identity',
    'server.tcp_server',
    'server.server_ref_list',
    'server.sample_list',
    # 'server.sample_live_list',
    # 'server.sample_tree',
    # 'server.module_list',
    # 'server.htest_module_list',
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
    services.start()
    log.info("Server is started.")
    try:
        services.stop_signal.wait()
    except KeyboardInterrupt:
        pass
    log.info("Server is stopping.")
    services.stop()


if __name__ == '__main__':
    main()
