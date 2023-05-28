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
    HYPERAPP_DIR / 'client',
    ]

code_module_list = [
    'client.client_lcs_service',
    'resource.legacy_module',
    'resource.legacy_service',
    'resource.legacy_type',
    'resource.attribute',
    'resource.partial',
    'resource.python_module',
    'common.lcs',
    'ui.impl_registry',
    'ui.global_command_list',
    'ui.list_adapter',
    'ui.string_adapter',
    'ui.method_command_adapter',
    'ui.object_command_adapter',
    'ui.global_command_adapter',
    'async.ui.qt.application',
    # 'async.ui.command_list',
    'async.ui.qt.tab_view',
    'async.ui.qt.menu_bar',
    'async.ui.qt.command_pane',
    'async.ui.qt.window',
    'async.ui.navigator',
    # 'async.ui.qt.record_view',
    # 'async.ui.data_viewer',
    # 'async.ui.qt.master_details',
    # 'async.ui.none_object',
    # 'async.ui.string_object',
    # 'async.ui.ref_object',
    # 'async.ui.qt.line_edit',
    # 'async.ui.qt.text_view',
    'ui.qt.list_view',
    'ui.qt.text_view',
    # 'async.ui.qt.tree_view',
    # 'client.list_view_sample',
    # 'client.tree_view_sample',
    # 'async.ui.tree_to_list_adapter',
    # 'client.tree_to_list_adapter_sample',
    # 'async.ui.fs',
    # 'async.ui.fs_local_service',
    # 'client.wiki_text_sample',
    # 'client.local_server',
    'transport.rsa_identity',
    'transport.async_tcp_transport',
    # 'client.record_service',
    'async.ui.application_state',
    # 'async.ui.view_selector',
    # 'async.ui.record_field_list',
    # 'async.ui.column_list',
    # 'async.ui.view_config',
    # 'async.ui.object_view_config',
    # 'async.ui.record_view_config',
    # 'async.ui.dir_list',
    # 'async.ui.available_view_list',
    # 'async.ui.qt.selector_view',
    # 'async.ui.alt_command',
    # 'async.ui.lcs_list',
    # 'async.ui.raw_piece',
    # 'async.ui.local_code_module_list',
    # 'async.ui.transport_log',
    'resource.async.attribute',
    'resource.resource_module',
    'resource.register_associations',
    ]


def init_meta_registry_association(resource_registry, python_object_creg):
    resource = resource_registry['common.meta_registry_association', 'meta_registry_association.module']
    module = python_object_creg.animate(resource)
    module.init()


def main():
    init_logging('client')

    parser = argparse.ArgumentParser(description='Hyperapp client')
    args = parser.parse_args()

    services = Services(module_dir_list)
    services.init_services()
    services.init_modules(code_module_list)
    init_meta_registry_association(services.resource_registry, services.python_object_creg)
    services.register_associations(services.resource_registry)
    services.start_modules()
    services.event_loop_holder.create_task(services.open_application())
    log.info("Client is started.")
    services.stop_signal.wait()
    log.info("Client is stopping.")
    services.stop()


main()
