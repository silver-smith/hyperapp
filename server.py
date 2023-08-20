#!/usr/bin/env python3

import argparse
import logging
import sys
from functools import partial

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
    HYPERAPP_DIR / 'server',
    ]

code_module_list = [
    'common.dict_coders',  # Load json coders.
    'common.lcs',
    'common.lcs_service',
    'transport.rsa_identity',
    'ui.impl_registry',
    'ui.global_command_list',
    'resource.register_associations',
    # 'server.sample_list',
    # 'server.sample_live_list',
    # 'server.sample_tree',
    # 'server.module_list',
    # 'server.htest_module_list',
    # 'server.htest_list',
    ]

BIND_ADDRESS = ('localhost', 8080)


def load_module(resource_registry, python_object_creg, module_name):
    var_name = module_name.split('.')[-1] + '.module'
    module_res = resource_registry[module_name, var_name]
    return python_object_creg.animate(module_res)


def main():
    init_logging('server')

    parser = argparse.ArgumentParser(description='Hyperapp server')
    args = parser.parse_args()

    services = Services(module_dir_list)
    services.init_services()
    services.init_modules(code_module_list, config={})

    services.start_modules()

    resource_registry = services.resource_registry
    python_object_creg = services.python_object_creg
    module = partial(load_module, resource_registry, python_object_creg)

    services.register_associations(resource_registry)

    server = module('server.tcp_server').tcp_server(BIND_ADDRESS)
    module('server.rpc_endpoint').init_server_rpc_endpoint()
    module('server.announce_provider').init_server_provider_announcer()
    module('server.init_local_server_ref').init_local_server_ref()

    log.info("Server is started.")
    try:
        services.stop_signal.wait()
    except KeyboardInterrupt:
        pass
    log.info("Server is stopping.")
    services.stop()


if __name__ == '__main__':
    main()
