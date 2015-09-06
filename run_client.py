#!/usr/bin/env python

import sys
from common.util import str2path
from common.interface import iface_registry
from client.application import Application

# self-registering ifaces:
import common.interface.server_management
import common.interface.fs
import common.interface.blog
import common.interface.article
import common.interface.code_repository
import common.interface.test_list
# self-registering views:
import client.window
import client.tab_view
import client.list_view
import client.navigator
import client.narrower
import client.text_object
import client.proxy_list_object
import client.proxy_text_object
import client.text_edit
import client.text_view
import client.object_selector
import client.ref_list
import client.form


def main():
    app = Application(sys.argv)

    if len(sys.argv) > 1:
        iface_id, path_str = sys.argv[1].split(':')
        path = str2path(path_str)
        iface = iface_registry.resolve(iface_id)
        app.execute_get_request(iface, path)

    app.exec_()


main()
