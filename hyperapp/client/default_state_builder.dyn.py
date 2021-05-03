from . import htypes
from .module import ClientModule


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services)
        self._mosaic = services.mosaic
        services.default_state_builder = self._build_default_state

    def _build_default_state(self):
        piece = "Welcome to hyperapp"
        piece_ref = self._mosaic.put(piece)
        navigator = htypes.navigator.navigator(piece_ref)
        navigator_ref = self._mosaic.put(navigator)
        tab_view = htypes.tab_view.tab_view([navigator_ref], 0)
        tab_view_ref = self._mosaic.put(tab_view)
        menu_bar = htypes.menu_bar.menu_bar()
        menu_bar_ref = self._mosaic.put(menu_bar)
        command_pane = htypes.command_pane.command_pane()
        command_pane_ref = self._mosaic.put(command_pane)
        window = htypes.window.window(
            menu_bar_ref=menu_bar_ref,
            command_pane_ref=command_pane_ref,
            central_view_ref=tab_view_ref,
            size=htypes.window.size(1000, 800),
            pos=htypes.window.pos(500, 100))
        window_ref = self._mosaic.put(window)
        return htypes.root_layout.root_layout([window_ref])
