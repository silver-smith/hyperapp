import asyncio

from PySide6 import QtWidgets

from .services import (
    project_factory,
    )
from .tested.code import client


def test_client(client_main):
    client_project = project_factory('mock-client')
    name_to_project = {
        'client': client_project,
        }
    sys_argv = [
        '--clean',
        '--lcs-layers-path=/tmp/client-test-lcs-layers.yaml',
        '--layout-path=/tmp/client-test-layout.jaon',
        '--test-mode',
        ]
    try:
        client_main(name_to_project, sys_argv)
    finally:
        app = QtWidgets.QApplication.instance()
        if app:
            loop = asyncio.get_event_loop()
            loop.close()
            app.shutdown()
