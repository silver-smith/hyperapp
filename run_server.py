#!/usr/bin/env python3

import argparse
import logging
import sys

from hyperapp.common.init_logging import init_logging
from hyperapp.common import cdr_coders  # register codec
from hyperapp.common.services import Services

log = logging.getLogger(__name__)


type_module_list = [
    'rsa_identity',
    'transport',
    'tcp_transport',
    'rpc',
    'object_type',
    'string',
    'list_ot',
    'record_ot',
    'service',
    'rpc_command',
    'layout',
    'text',
    'sample_list',
    ]

code_module_list = [
    'common.dict_coders',
    'common.visitor',
    'common.ref_collector',
    'common.unbundler',
    'common.file_bundle',
    'common.local_server',
    'common.list',
    'common.record',
    'transport.identity',
    'transport.rsa_identity',
    'transport.route_table',
    'transport.tcp',
    'sync.failure',
    'sync.transport.route_table',
    'sync.transport.transport',
    'sync.transport.endpoint',
    'sync.transport.tcp',
    'sync.rpc.rpc_proxy',
    'sync.rpc.rpc_endpoint',
    'server.identity',
    'server.tcp_server',
    'server.rpc_endpoint',
    'server.server_ref_list',
    'server.sample_list',
    ]

config = {
    'server.tcp_server': {'bind_address': ('localhost', 8000)},
    }


def main():
    init_logging('server')

    parser = argparse.ArgumentParser(description='Hyperapp server')
    args = parser.parse_args()

    services = Services()
    services.init_services()
    services.init_modules(type_module_list, code_module_list, config)
    services.start()
    log.info("Server is started.")
    try:
        services.stop_signal.wait()
    except KeyboardInterrupt:
        pass
    log.info("Server is stopping.")
    services.stop()


main()
