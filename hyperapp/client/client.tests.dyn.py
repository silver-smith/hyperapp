import asyncio
from pathlib import Path

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    project_factory,
    )
from .code.mark import mark
from .tested.code import client


@mark.config_fixture('model_layout_reg')
def model_layout_reg_config():
    return {
        htypes.builtin.string: htypes.text.edit_view(
            adapter=mosaic.put(htypes.str_adapter.static_str_adapter()),
            ),
        }


def test_client(client_main):
    client_project = project_factory(Path('/tmp/client-test'), 'mock-client')
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
