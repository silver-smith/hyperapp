#!/usr/bin/env python3

import argparse
import logging
import sys

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
    'resource.legacy_module',
    'resource.legacy_service',
    'resource.legacy_type',
    'resource.attribute',
    'resource.partial',
    'resource.call',
    'resource.value',
    'resource.python_module',
    'resource.piece_ref',
    'resource.rpc_command',
    'resource.rpc_callback',
    'resource.list_service',
    'resource.live_list_service',
    'resource.tree_service',
    'resource.selector',
    'transport.rsa_identity',
    'ui.impl_registry',
    'ui.global_command_list',
    'server.tcp_server',
    'server.rpc_endpoint',
    'resource.register_associations',
    'server.announce_provider',
    # 'server.server_ref_list',
    # 'server.sample_list',
    # 'server.sample_live_list',
    # 'server.sample_tree',
    # 'server.module_list',
    # 'server.htest_module_list',
    # 'server.htest_list',
    ]

config = {
    'server.tcp_server': {'bind_address': ('localhost', 8080)},
    }


def init_meta_registry_association(resource_module_registry, python_object_creg):
    module_res = resource_module_registry['common.meta_registry_association']
    resource = module_res['meta_registry_association.module']
    module = python_object_creg.animate(resource)
    module.init()


def init_sample_list(resource_module_registry, python_object_creg):
    call_resource = resource_module_registry['server.sample_list_ref']['save_sample_list_ref_call']
    python_object_creg.animate(call_resource)


def main():
    init_logging('server')

    parser = argparse.ArgumentParser(description='Hyperapp server')
    args = parser.parse_args()

    services = Services(module_dir_list)
    services.init_services()
    services.init_modules(code_module_list, config)

    init_meta_registry_association(services.resource_module_registry, services.python_object_creg)
    services.register_associations(services.resource_module_registry)
    init_sample_list(services.resource_module_registry, services.python_object_creg)

    services.start_modules()

    log.info("Server is started.")
    try:
        services.stop_signal.wait()
    except KeyboardInterrupt:
        pass
    log.info("Server is stopping.")
    services.stop()


if __name__ == '__main__':
    main()
