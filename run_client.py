#!/usr/bin/env python3

import argparse
import logging
import sys

from hyperapp.common.init_logging import init_logging
from hyperapp.common import cdr_coders  # register codec
from hyperapp.common.services import Services

log = logging.getLogger(__name__)


type_module_list = [
    'resource',
    'fs',
    'layout',
    'tab_view',
    'navigator',
    'menu_bar',
    'command_pane',
    'window',
    'root_layout',
    'application_state',
    'object_type',
    'object_layout_association',
    'none_ot',
    'string',
    'ref_ot',
    'text',
    'list_ot',
    'tree_object',
    'record_ot',
    'code_command_chooser',
    'command_list',
    'layout_editor',
    'record_view',
    'line',
    'master_details',
    'list_view',
    'tree_view',
    'tree_to_list_adapter',
    'data_viewer',
    'log_viewer',
    'params_editor',
    'list_view_sample',
    'tree_view_sample',
    'view_chooser',
    'params_editor_sample',
    'rsa_identity',
    'transport',
    'tcp_transport',
    'rpc',
    'rpc_command',
    ]

code_module_list = [
    'common.dict_coders',
    'common.visitor',
    'common.ref_collector',
    'common.unbundler',
    'common.file_bundle',
    'common.resource_registry',
    'common.resource_resolver',
    'common.resource_loader',
    'common.fs_service_impl',
    'common.weak_key_dictionary_with_callback',
    'common.file_bundle',
    'common.local_server',
    'common.list_object',
    'common.record',
    'common.resource_key',
    'transport.identity',
    'transport.rsa_identity',
    'async.ui.commander',
    'async.ui.module',
    'async.async_web',
    'async.ui.qt.application',
    'async.async_main',
    'async.ui.params_editor',
    'async.ui.object_command',
    'async.async_registry',
    'async.code_registry',
    'client.view_registry',
    'client.object_layout_association',
    'client.layout_handle',
    'async.ui.object',
    'async.ui.record_object',
    'async.ui.object_registry',
    'client.layout_command',
    'async.ui.items_view',
    'client.self_command',
    'client.layout',
    'client.command_hub',
    'async.ui.qt.util',
    'client.layout_manager',
    'client.default_state_builder',
    'client.application_state_storage',
    'async.ui.module_command_registry',
    'async.ui.qt.qt_keys',
    'client.view',
    'client.composite',
    'async.ui.column',
    'async.ui.command_registry',
    'async.ui.command',
    'async.ui.list_object',
    'async.ui.simple_list_object',
    'async.ui.list_service',
    'async.ui.record_service',
    'async.ui.chooser',
    'async.ui.params_editor_object',
    'async.ui.tree_object',
    'async.ui.view_chooser',
    'async.ui.code_command_chooser',
    'async.ui.command_list',
    'client.layout_editor',
    'client.tab_view',
    'client.menu_bar',
    'client.command_pane',
    'client.window',
    'client.navigator.navigator',
    'client.record_view',
    'async.ui.text_object',
    'async.ui.data_viewer',
    'client.master_details',
    'async.ui.none_object',
    'async.ui.string_object',
    'async.ui.ref_object',
    'client.line_edit',
    'client.text_view',
    'client.list_view',
    'client.list_view_sample',
    'client.tree_view',
    'client.tree_view_sample',
    'async.ui.tree_to_list_adapter',
    'client.tree_to_list_adapter_sample',
    'client.params_editor_sample',
    'async.ui.fs',
    'async.ui.fs_local_service',
    'client.wiki_text_sample',
    'client.local_server',
    'transport.identity',
    'transport.rsa_identity',
    'client.identity',
    'transport.route_table',
    'transport.tcp',
    'async.transport.route_table',
    'async.transport.transport',
    'async.transport.endpoint',
    'async.transport.tcp',
    'async.rpc.rpc_proxy',
    'async.rpc.rpc_endpoint',
    'client.rpc_endpoint',
    'client.list_service',
    'client.record_service',
    'async.ui.rpc_command',
    'async.ui.application_state',
    ]


def main():
    init_logging('client')

    parser = argparse.ArgumentParser(description='Hyperapp client')
    args = parser.parse_args()

    services = Services()
    services.client_resources_dir_list = [
        services.hyperapp_dir / 'async/ui',
        services.hyperapp_dir / 'async/ui/qt',
        services.hyperapp_dir / 'client',
        ]
    services.init_services()
    services.init_modules(type_module_list, code_module_list)
    services.start()
    log.info("Client is started.")
    services.stop_signal.wait()
    log.info("Client is stopping.")
    services.stop()


main()
