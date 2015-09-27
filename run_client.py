#!/usr/bin/env python

import sys
from hyperapp.common.util import str2path
from hyperapp.common.interface import iface_registry
from hyperapp.client.application import Application

# self-registering ifaces:
import hyperapp.common.interface.server_management
import hyperapp.common.interface.fs
import hyperapp.common.interface.blog
import hyperapp.common.interface.article
import hyperapp.common.interface.code_repository
import hyperapp.common.interface.test_list
# self-registering views:
import hyperapp.client.window
import hyperapp.client.tab_view
import hyperapp.client.list_view
import hyperapp.client.navigator
import hyperapp.client.narrower
import hyperapp.client.text_object
import hyperapp.client.proxy_list_object
import hyperapp.client.proxy_text_object
import hyperapp.client.text_edit
import hyperapp.client.text_view
import hyperapp.client.object_selector
import hyperapp.client.ref_list


def main():
    app = Application(sys.argv)

    if len(sys.argv) > 1:
        iface_id, path_str = sys.argv[1].split(':')
        path = str2path(path_str)
        iface = iface_registry.resolve(iface_id)
        app.execute_get_request(iface, path)

    app.exec_()


main()
