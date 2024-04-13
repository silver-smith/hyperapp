import asyncio
from pathlib import Path

from PySide6 import QtWidgets
from qasync import QEventLoop

from . import htypes
from .services import (
    endpoint_registry,
    file_bundle,
    generate_rsa_identity,
    mosaic,
    rpc_endpoint_factory,
    visualizer,
    view_creg,
    )
from .code.context import Context
from .code.model_command import global_commands
from .code.controller import Controller


layout_path = Path.home() / '.local/share/hyperapp/client/layout.json'


def make_default_piece():
    text = "Sample text"
    text_view = visualizer(text)
    navigator = htypes.navigator.view(
        current_view=mosaic.put(text_view),
        current_model=mosaic.put(text),
        commands=tuple(mosaic.put(c) for c in global_commands()),
        prev=None,
        next=None,
        )
    command_pane = htypes.command_pane.view()
    box_layout = htypes.box_layout.view(
        direction='LeftToRight',
        elements=(
            htypes.box_layout.element(
                view=mosaic.put(navigator),
                focusable=True,
                stretch=1,
                ),
            htypes.box_layout.element(
                view=mosaic.put(command_pane),
                focusable=False,
                stretch=1,
                ),
            ),
        )
    inner_tabs_piece = htypes.auto_tabs.view(
        tabs=(
            mosaic.put(box_layout),
            ),
        )
    outer_tabs_piece = htypes.tab_groups.view(
        tabs=(
            htypes.tabs.tab("Outer", mosaic.put(inner_tabs_piece)),
            ),
        )
    window_piece = htypes.window.view(
        menu_bar_ref=mosaic.put(htypes.menu_bar.view()),
        central_view_ref=mosaic.put(outer_tabs_piece),
        )
    return htypes.root.view(
        window_list=(mosaic.put(window_piece),),
        )


def make_default_state():
    text_state = htypes.text.state()
    navigator_state = htypes.navigator.state(
        current_state=mosaic.put(text_state),
        prev=None,
        next=None,
        )
    command_pane_state = htypes.command_pane.state()
    box_layout_state = htypes.box_layout.state(
        current=0,
        elements=(
            mosaic.put(navigator_state),
            mosaic.put(command_pane_state),
            ),
        )
    inner_tabs_state = htypes.tabs.state(
        current_tab=0,
        tabs=(mosaic.put(box_layout_state),),
        )
    outer_tabs_state = htypes.tabs.state(
        current_tab=0,
        tabs=(mosaic.put(inner_tabs_state),),
        )
    window_state = htypes.window.state(
        menu_bar_state=mosaic.put(htypes.menu_bar.state()),
        central_view_state=mosaic.put(outer_tabs_state),
        size=htypes.window.size(500, 500),
        pos=htypes.window.pos(1000, 500),
        )
    return htypes.root.state(
        window_list=(mosaic.put(window_state),),
        current=0,
        )


def make_default_layout():
    return htypes.root.layout(
        piece=make_default_piece(),
        state=make_default_state(),
        )


def _main():
    app = QtWidgets.QApplication()
    event_loop = QEventLoop(app)
    asyncio.set_event_loop(event_loop)  # Should be set before any asyncio objects created.

    identity = generate_rsa_identity()
    rpc_endpoint = rpc_endpoint_factory()
    endpoint_registry.register(identity, rpc_endpoint)

    ctx = Context(
        identity=identity,
        rpc_endpoint=rpc_endpoint,
        )
    default_layout = make_default_layout()
    layout_bundle = file_bundle(layout_path)

    with Controller.running(layout_bundle, default_layout, ctx, show=True):
        return app.exec()
