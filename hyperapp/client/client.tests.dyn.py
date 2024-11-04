import asyncio

from PySide6 import QtWidgets

from .tested.code import client


def test_client(client_main):
    sys_argv = [
        '--clean',
        '--lcs-storage-path=/tmp/client-test-lcs-storage-path.yaml',
        '--layout-path=/tmp/client-test-layout-path.jaon',
        '--test-mode',
        ]
    try:
        client_main(sys_argv)
    finally:
        app = QtWidgets.QApplication.instance()
        if app:
            loop = asyncio.get_event_loop()
            loop.close()
            app.shutdown()
