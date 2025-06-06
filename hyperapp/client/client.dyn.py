import argparse
import asyncio
import logging
from pathlib import Path

from PySide6 import QtWidgets
from qasync import QEventLoop

from . import htypes
from .services import (
    hyperapp_dir,
    mosaic,
    )
from .code.mark import mark
from .code.context import Context
from .code.lcs import LCSheet
from .code.controller import Controller
from .code.reconstructors import register_reconstructors

log = logging.getLogger(__name__)


default_lcs_layers_path = hyperapp_dir / 'client/lcs-layers.yaml'
default_layout_path = Path.home() / '.local/share/hyperapp/client/layout.json'


async def make_default_piece(visualizer, ctx):
    text = "Sample text"
    text_view = await visualizer(ctx, htypes.builtin.string)
    navigator = htypes.navigator.view(
        current_view=mosaic.put(text_view),
        current_model=mosaic.put(text),
        layout_k=None,
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
                stretch=0,
                ),
            ),
        )
    tabs_piece = htypes.auto_tabs.view(
        tabs=(htypes.tabs.tab("First tab", mosaic.put(box_layout)),),
        )
    window_piece = htypes.window.view(
        menu_bar_ref=mosaic.put(htypes.menu_bar.view()),
        central_view_ref=mosaic.put(tabs_piece),
        )
    return htypes.root.view(
        window_list=(mosaic.put(window_piece),),
        )


def make_default_state():
    text_state = htypes.text.state('')
    navigator_state = text_state
    command_pane_state = htypes.command_pane.state()
    box_layout_state = htypes.box_layout.state(
        current=0,
        elements=(
            mosaic.put(navigator_state),
            mosaic.put(command_pane_state),
            ),
        )
    tabs_state = htypes.tabs.state(
        current_tab=0,
        tabs=(mosaic.put(box_layout_state),),
        )
    window_state = htypes.window.state(
        menu_bar_state=mosaic.put(htypes.menu_bar.state()),
        central_view_state=mosaic.put(tabs_state),
        size=htypes.window.size(1000, 1100),
        pos=htypes.window.pos(700, 200),
        )
    return htypes.root.state(
        window_list=(mosaic.put(window_state),),
        current=0,
        )


async def make_default_layout(visualizer, ctx):
    return htypes.root.layout(
        piece=await make_default_piece(visualizer, ctx),
        state=make_default_state(),
        )


def _parse_args(sys_argv):
    parser = argparse.ArgumentParser(description='Hyperapp client')
    parser.add_argument('--clean', '-c', action='store_true', help="Do not load stored layout state")
    parser.add_argument('--lcs-layers-path', type=Path, default=default_lcs_layers_path, help="Path to lcs layers list")
    parser.add_argument('--layout-path', type=Path, default=default_layout_path, help="Path to layout")
    parser.add_argument('--test-mode', action='store_true', help="Do not enter main loop, exit right after initing. Do not show windows. Used for testing")
    return parser.parse_args(sys_argv)


@mark.service
async def client_async_main(
        endpoint_registry,
        generate_rsa_identity,
        rpc_endpoint,
        file_bundle_factory,
        lcs_resource_storage_factory,
        visualizer,
        controller_running,
        args,
        client_project,
        app,
        stop_event,
        ):
    project_imports = {client_project}
    lcs = LCSheet.from_layer_list_path(args.lcs_layers_path, lcs_resource_storage_factory, project_imports)

    identity = generate_rsa_identity()
    endpoint_registry.register(identity, rpc_endpoint)

    ctx = Context(
        lcs=lcs,
        identity=identity,
        rpc_endpoint=rpc_endpoint,
        )
    default_layout = await make_default_layout(visualizer, ctx)
    layout_bundle = file_bundle_factory(args.layout_path)

    async with controller_running(layout_bundle, default_layout, ctx, show=not args.test_mode, load_state=not args.clean) as ctl:
        if not args.test_mode:
            await stop_event.wait()


def _on_focus_changed(focused_obj):
    if not focused_obj:
        return
    window = focused_obj.window()
    if isinstance(window, QtWidgets.QMenu):
        return
    window.focus_changed(focused_obj)


@mark.service
def client_main(client_async_main, name_to_project, sys_argv):
    args = _parse_args(sys_argv)
    client_project = name_to_project['client']

    register_reconstructors()

    app = QtWidgets.QApplication()
    event_loop = QEventLoop(app)
    asyncio.set_event_loop(event_loop)  # Should be set before any asyncio objects created.

    with event_loop:
        stop_event = asyncio.Event()
        app.aboutToQuit.connect(stop_event.set)
        app.focusObjectChanged.connect(_on_focus_changed)
        event_loop.run_until_complete(client_async_main(args, client_project, app, stop_event))
