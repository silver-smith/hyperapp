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
    'text',
    'list_object',
    'tree_object',
    'record_object',
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
    'async.ui.commander',
    'async.ui.module',
    'client.module_command_registry',
    'async.async_web',
    'async.async_registry',
    'async.code_registry',
    'client.object_registry',
    'async.ui.qt.util',
    'async.ui.qt.qt_keys',
    'async.ui.object',
    'client.view',
    'async.ui.command',
    'client.composite',
    'client.column',
    'client.list_object',
    'client.tree_object',
    'client.simple_list_object',
    'client.command_hub',
    'client.view_registry',
    'client.object_layout_association',
    'client.items_view',
    'client.layout_handle',
    'client.layout_command',
    'client.self_command',
    'client.layout',
    'client.record_object',
    'client.chooser',
    'client.params_editor',
    'client.object_command',
    'client.params_editor_object',
    'client.view_chooser',
    'client.default_state_builder',
    'client.layout_manager',
    'client.code_command_chooser',
    'client.command_list',
    'client.layout_editor',
    'client.tab_view',
    'client.menu_bar',
    'client.command_pane',
    'client.window',
    'client.navigator.navigator',
    'client.record_view',
    'client.text_object',
    'client.data_viewer',
    'client.application_state_storage',
    'client.master_details',
    'client.line_edit',
    'client.text_view',
    'client.list_view',
    'client.list_view_sample',
    'client.tree_view',
    'client.tree_view_sample',
    'client.tree_to_list_adapter',
    'client.tree_to_list_adapter_sample',
    'client.params_editor_sample',
    'client.fs',
    'client.fs_local_service',
    'client.wiki_text_sample',
    'async.ui.qt.application',
    'async.async_main',
    'async.ui.application_state',
    ]


def main():
    init_logging('client')

    parser = argparse.ArgumentParser(description='Hyperapp client')
    args = parser.parse_args()

    services = Services()
    services.client_resources_dir = services.hyperapp_dir / 'client'
    services.init_services()
    services.init_modules(type_module_list, code_module_list)
    services.start()
    log.info("Client is started.")
    services.sync_stop_signal.wait()
    log.info("Client is stopping.")
    services.stop()


main()
