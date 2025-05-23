import asyncio
from pathlib import Path
from unittest.mock import AsyncMock

from PySide6 import QtWidgets

from . import htypes
from .services import (
    mosaic,
    project_factory,
    )
from .code.mark import mark
from .fixtures import visualizer_fixtures
from .tested.code import client


@mark.fixture
def adapter():
    accessor = htypes.accessor.model_accessor()
    cvt = htypes.type_convertor.noop_convertor()
    return htypes.value_adapter.value_adapter(
        accessor=mosaic.put(accessor),
        convertor=mosaic.put(cvt),
        )


@mark.fixture
def text_view(adapter):
    return htypes.text.readonly_view(
        adapter=mosaic.put(adapter),
        )


@mark.config_fixture('view_factory_reg')
def view_factory_reg_config(text_view):
    factory = AsyncMock()
    factory.call.return_value = text_view
    return {
        htypes.visualizer_fixtures.string_view_k(): factory,
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
