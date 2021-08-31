from functools import partial

from hyperapp.common.module import Module

from . import htypes


def default_state_builder(mosaic):
    piece = "Welcome to hyperapp"
    piece_ref = mosaic.put(piece)

    navigator = htypes.navigator.navigator(piece_ref, origin_dir=[])
    navigator_ref = mosaic.put(navigator)

    tab_view = htypes.tab_view.state([navigator_ref], 0)
    tab_view_ref = mosaic.put(tab_view)

    menu_bar = htypes.menu_bar.menu_bar()
    menu_bar_ref = mosaic.put(menu_bar)

    command_pane = htypes.command_pane.command_pane()
    command_pane_ref = mosaic.put(command_pane)

    window = htypes.window.window(
        menu_bar_ref=menu_bar_ref,
        command_pane_ref=command_pane_ref,
        central_view_ref=tab_view_ref,
        size=htypes.window.size(1000, 800),
        pos=htypes.window.pos(500, 100))
    windows_state = htypes.window.state([window])

    return windows_state


class ThisModule(Module):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services, config)

        services.default_state_builder = partial(default_state_builder, services.mosaic)
