#!/usr/bin/env python

import sys
from hyperapp.common.util import decode_url
from hyperapp.common.interface import iface_registry
from hyperapp.client.application import Application

# self-registering ifaces:
import hyperapp.common.interface.server_management
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


def main():
    app = Application(sys.argv)

    if len(sys.argv) > 1:
        url = decode_url(sys.argv[1])
        app.execute_get_request(url)

    app.exec_()


main()
