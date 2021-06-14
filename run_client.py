#!/usr/bin/env python3

import argparse
import logging
import sys

from hyperapp.common.init_logging import init_logging
from hyperapp.common import cdr_coders  # register codec
from hyperapp.common.services import Services

log = logging.getLogger(__name__)


code_module_list = [
    'common.resource_loader',
    'async.ui.qt.application',
    'async.ui.code_command_chooser',
    'async.ui.command_list',
    'client.layout_editor',
    'client.tab_view',
    'client.menu_bar',
    'client.command_pane',
    'client.window',
    'client.navigator.navigator',
    'client.record_view',
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
    'async.transport.tcp',
    'client.list_service',
    'client.tree_service',
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
    services.init_modules(code_module_list)
    services.start()
    log.info("Client is started.")
    services.stop_signal.wait()
    log.info("Client is stopping.")
    services.stop()


main()
