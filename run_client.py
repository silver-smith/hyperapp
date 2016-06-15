#!/usr/bin/env python3

# self-registering ifaces:
import hyperapp.common.interface.server_management
import hyperapp.common.interface.admin
import hyperapp.common.interface.fs
import hyperapp.common.interface.blog
import hyperapp.common.interface.article
import hyperapp.common.interface.module_list
# self-registering views:
import hyperapp.client.window
import hyperapp.client.tab_view
import hyperapp.client.list_view
import hyperapp.client.navigator
import hyperapp.client.narrower
import hyperapp.client.text_object
import hyperapp.client.proxy_list_object
import hyperapp.client.text_edit
import hyperapp.client.text_view
import hyperapp.client.form_view
import hyperapp.client.identity
import hyperapp.client.code_repository
import hyperapp.client.bookmarks
import hyperapp.client.url_clipboard

from hyperapp.client import tcp_transport
from hyperapp.client import encrypted_transport

import sys
import logging
import argparse
from hyperapp.common.htypes import tServerPacket, iface_registry
from hyperapp.client.application import Application
from hyperapp.client.transport import transport_registry
from hyperapp.client.objimpl_registry import objimpl_registry
from hyperapp.client.view_registry import view_registry


def main():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)-15s  %(message)s')

    parser = argparse.ArgumentParser(description='Hyperapp client')
    args = parser.parse_args()

    app = Application(sys.argv)

    tcp_transport.register_transports(transport_registry, app._module_mgr, app._code_repository,
                                      iface_registry, objimpl_registry, view_registry)

    app.exec_()


main()
