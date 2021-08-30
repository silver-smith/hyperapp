#!/usr/bin/env python3

import argparse
import logging
import sys

from hyperapp.common.init_logging import init_logging
from hyperapp.common import cdr_coders  # register codec
from hyperapp.common.services import Services

log = logging.getLogger(__name__)


code_module_list = [
    'async.ui.qt.application',
    'async.ui.command_list',
    'client.layout_editor',
    'client.tab_view',
    'client.menu_bar',
    'client.command_pane',
    'client.window',
    'async.ui.navigator',
    'async.ui.qt.record_view',
    'async.ui.data_viewer',
    'async.ui.qt.master_details',
    'async.ui.none_object',
    'async.ui.string_object',
    'async.ui.ref_object',
    'async.ui.qt.line_edit',
    'async.ui.qt.text_view',
    'async.ui.qt.list_view',
    'async.ui.qt.tree_view',
    'client.list_view_sample',
    'client.tree_view_sample',
    'async.ui.tree_to_list_adapter',
    'client.tree_to_list_adapter_sample',
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
    'async.ui.view_selector',
    'async.ui.record_field_list',
    'async.ui.view_config',
    'async.ui.object_view_config',
    'async.ui.record_view_config',
    'async.ui.dir_list',
    'async.ui.available_view_list',
    'async.ui.selector',
    'async.ui.qt.selector_view',
    'async.ui.alt_command',
    ]


def main():
    init_logging('client')

    parser = argparse.ArgumentParser(description='Hyperapp client')
    args = parser.parse_args()

    services = Services()
    services.init_services()
    services.init_modules(code_module_list)
    services.start()
    log.info("Client is started.")
    services.stop_signal.wait()
    log.info("Client is stopping.")
    services.stop()


main()
